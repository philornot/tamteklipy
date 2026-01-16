"""
API endpoint performance tests.

Tests response times and throughput for main API endpoints.
Related to: TK-629 (SQL optimization), TK-633 (pagination)
"""
import time
import pytest
from fastapi.testclient import TestClient


class TestClipsEndpointPerformance:
    """Performance tests for /api/files/clips endpoint."""

    def test_clips_list_response_time(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips,
            perf_metrics
    ):
        """
        Test /api/files/clips response time.

        Target: < 200ms for 50 clips (TK-629)
        Baseline: Measure current performance
        """
        start = time.time()
        response = client.get("/api/files/clips", headers=auth_headers)
        duration = time.time() - start

        assert response.status_code == 200
        perf_metrics.add_response_time(duration)

        print(f"\n/clips response time: {duration * 1000:.2f}ms")
        print(f"Clips returned: {len(response.json()['clips'])}")

        # Baseline measurement - should improve after TK-629
        assert duration < 1.0, "Response should be under 1 second (pre-optimization)"

    def test_clips_pagination_performance(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips,
            perf_metrics
    ):
        """
        Test pagination performance across multiple pages.

        Related to: TK-633 (pagination optimization)
        """
        page_times = []

        for page in range(1, 4):
            start = time.time()
            response = client.get(
                f"/api/files/clips?page={page}&limit=20",
                headers=auth_headers
            )
            duration = time.time() - start

            assert response.status_code == 200
            page_times.append(duration)
            perf_metrics.add_response_time(duration)

        avg_time = sum(page_times) / len(page_times)
        print(f"\nAverage pagination time: {avg_time * 1000:.2f}ms")
        print(f"Page times: {[f'{t * 1000:.2f}ms' for t in page_times]}")

        # All pages should have similar performance
        assert max(page_times) < min(page_times) * 2, \
            "Page performance should be consistent"

    def test_clips_with_filters_performance(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test performance with various filters.

        Related to: TK-629 (need indexes for filtered queries)
        """
        filters = [
            "?clip_type=video",
            "?clip_type=screenshot",
            "?uploader_id=1",
            "?sort_by=created_at&sort_order=desc",
            "?sort_by=file_size&sort_order=asc"
        ]

        times = {}
        for filter_str in filters:
            start = time.time()
            response = client.get(
                f"/api/files/clips{filter_str}",
                headers=auth_headers
            )
            duration = time.time() - start

            assert response.status_code == 200
            times[filter_str] = duration

        print("\nFilter performance:")
        for filter_str, duration in times.items():
            print(f"  {filter_str}: {duration * 1000:.2f}ms")

        # After TK-629, all should be fast
        for duration in times.values():
            assert duration < 0.5, "Filtered queries should be fast"

    def test_clips_random_performance(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test /api/files/clips/random performance.

        Related to: TK-633 (random query optimization)
        """
        times = []

        for _ in range(5):
            start = time.time()
            response = client.get(
                "/api/files/clips/random?limit=10",
                headers=auth_headers
            )
            duration = time.time() - start

            assert response.status_code == 200
            times.append(duration)

        avg_time = sum(times) / len(times)
        print(f"\nRandom clips average time: {avg_time * 1000:.2f}ms")

        assert avg_time < 0.3, "Random query should be fast"


class TestClipDetailPerformance:
    """Performance tests for single clip endpoints."""

    def test_clip_detail_response_time(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """Test single clip detail response time."""
        clip = sample_clips[0]

        start = time.time()
        response = client.get(
            f"/api/files/clips/{clip.id}",
            headers=auth_headers
        )
        duration = time.time() - start

        assert response.status_code == 200
        print(f"\nClip detail response time: {duration * 1000:.2f}ms")

        assert duration < 0.1, "Single clip should be very fast"


class TestAwardsEndpointPerformance:
    """Performance tests for awards endpoints."""

    def test_clip_awards_list_performance(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips,
            sample_awards
    ):
        """
        Test awards list for clip.

        Related to: TK-629 (joinedload optimization)
        """
        clip = sample_clips[0]

        start = time.time()
        response = client.get(
            f"/api/awards/clips/{clip.id}",
            headers=auth_headers
        )
        duration = time.time() - start

        assert response.status_code == 200
        print(f"\nClip awards response time: {duration * 1000:.2f}ms")

        assert duration < 0.15, "Awards list should be fast"

    def test_my_awards_performance(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_award_types
    ):
        """Test /api/awards/my-awards performance."""
        start = time.time()
        response = client.get(
            "/api/awards/my-awards",
            headers=auth_headers
        )
        duration = time.time() - start

        assert response.status_code == 200
        print(f"\nMy awards response time: {duration * 1000:.2f}ms")

        # Should be cacheable (TK-634)
        assert duration < 0.1, "My awards should be fast (future: cacheable)"

    def test_award_stats_performance(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips,
            sample_awards
    ):
        """
        Test /api/awards/stats performance.

        Related to: TK-629 (complex aggregations need optimization)
        """
        start = time.time()
        response = client.get(
            "/api/awards/stats",
            headers=auth_headers
        )
        duration = time.time() - start

        assert response.status_code == 200
        print(f"\nAward stats response time: {duration * 1000:.2f}ms")
        print(f"Stats computed: {len(response.json())}")

        # Complex aggregation - baseline for optimization
        assert duration < 1.0, "Stats should complete in reasonable time"


class TestAdminEndpointPerformance:
    """Performance tests for admin endpoints."""

    def test_admin_users_list_performance(
            self,
            client: TestClient,
            admin_headers: dict,
            db_session
    ):
        """Test /api/admin/users performance."""
        # Create more users
        from app.models.user import User
        from app.core.security import hash_password

        for i in range(20):
            user = User(
                username=f"user{i}",
                email=f"user{i}@test.com",
                hashed_password=hash_password("pass"),
                is_active=True,
                is_admin=False
            )
            db_session.add(user)
        db_session.commit()

        start = time.time()
        response = client.get(
            "/api/admin/users",
            headers=admin_headers
        )
        duration = time.time() - start

        assert response.status_code == 200
        print(f"\nAdmin users list: {duration * 1000:.2f}ms")

        assert duration < 0.2, "Users list should be fast"

    def test_admin_awards_list_performance(
            self,
            client: TestClient,
            admin_headers: dict,
            sample_awards
    ):
        """
        Test /api/admin/awards with pagination.

        Related to: TK-633 (pagination optimization)
        """
        start = time.time()
        response = client.get(
            "/api/admin/awards?page=1&limit=20",
            headers=admin_headers
        )
        duration = time.time() - start

        assert response.status_code == 200
        print(f"\nAdmin awards list: {duration * 1000:.2f}ms")
        print(f"Awards returned: {len(response.json()['awards'])}")

        assert duration < 0.3, "Admin awards should be reasonably fast"


class TestConcurrentRequests:
    """Test performance under concurrent load."""

    def test_concurrent_clips_requests(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Simulate concurrent requests to clips endpoint.

        Related to: TK-630 (connection pooling), TK-640 (workers)
        """
        import concurrent.futures

        def make_request():
            start = time.time()
            response = client.get("/api/files/clips", headers=auth_headers)
            duration = time.time() - start
            return duration, response.status_code

        # Simulate 10 concurrent users
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        durations = [r[0] for r in results]
        status_codes = [r[1] for r in results]

        print(f"\nConcurrent requests results:")
        print(f"  Average: {sum(durations) / len(durations) * 1000:.2f}ms")
        print(f"  Max: {max(durations) * 1000:.2f}ms")
        print(f"  Min: {min(durations) * 1000:.2f}ms")
        print(f"  All successful: {all(s == 200 for s in status_codes)}")

        assert all(s == 200 for s in status_codes), "All requests should succeed"
        # Performance should degrade gracefully under load
        assert max(durations) < min(durations) * 5, \
            "Max time shouldn't be 5x slower than min (after TK-630 should be better)"


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests using pytest-benchmark."""

    def test_benchmark_clips_list(
            self,
            benchmark,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """Benchmark clips list endpoint."""

        def clips_list():
            return client.get("/api/files/clips", headers=auth_headers)

        result = benchmark(clips_list)
        assert result.status_code == 200

    def test_benchmark_single_clip(
            self,
            benchmark,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """Benchmark single clip endpoint."""
        clip = sample_clips[0]

        def get_clip():
            return client.get(f"/api/files/clips/{clip.id}", headers=auth_headers)

        result = benchmark(get_clip)
        assert result.status_code == 200

    def test_benchmark_awards_list(
            self,
            benchmark,
            client: TestClient,
            auth_headers: dict,
            sample_clips,
            sample_awards
    ):
        """Benchmark awards list endpoint."""
        clip = sample_clips[0]

        def get_awards():
            return client.get(f"/api/awards/clips/{clip.id}", headers=auth_headers)

        result = benchmark(get_awards)
        assert result.status_code == 200
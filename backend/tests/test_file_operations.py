"""
File operations performance tests.

Tests file upload, thumbnail generation, and streaming performance.
Related to: TK-631 (thumbnail optimization), TK-635 (file serving)
"""
import io
import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient


class TestFileUploadPerformance:
    """Test file upload performance."""

    def test_small_video_upload_time(
            self,
            client: TestClient,
            auth_headers: dict,
            tmp_path
    ):
        """
        Test upload time for small video (1MB).

        Related to: TK-631 (upload shouldn't block)
        Target: Upload response < 500ms (processing in background)
        """
        # Create fake video file (1MB)
        video_data = b'0' * (1024 * 1024)

        files = {
            'file': ('test_small.mp4', io.BytesIO(video_data), 'video/mp4')
        }

        start = time.time()
        response = client.post(
            "/api/files/upload",
            files=files,
            headers=auth_headers
        )
        duration = time.time() - start

        print(f"\nSmall video upload time: {duration * 1000:.2f}ms")

        assert response.status_code == 200, f"Upload failed: {response.json()}"

        # Upload should return quickly (thumbnail in background)
        assert duration < 1.0, "Upload should be fast (TK-631: < 500ms after optimization)"

    def test_large_video_upload_time(
            self,
            client: TestClient,
            auth_headers: dict
    ):
        """
        Test upload time for larger video (10MB).

        Related to: TK-637 (memory optimization)
        """
        # Create fake video file (10MB)
        video_data = b'0' * (10 * 1024 * 1024)

        files = {
            'file': ('test_large.mp4', io.BytesIO(video_data), 'video/mp4')
        }

        start = time.time()
        response = client.post(
            "/api/files/upload",
            files=files,
            headers=auth_headers
        )
        duration = time.time() - start

        print(f"\nLarge video upload time: {duration * 1000:.2f}ms")
        print(f"Upload rate: {10 / duration:.2f} MB/s")

        assert response.status_code == 200

        # Larger files take longer but should still be reasonable
        assert duration < 5.0, "Large upload should complete in reasonable time"

    def test_screenshot_upload_time(
            self,
            client: TestClient,
            auth_headers: dict
    ):
        """Test screenshot upload performance."""
        # Create fake PNG (500KB)
        png_data = b'\x89PNG\r\n\x1a\n' + b'0' * (500 * 1024)

        files = {
            'file': ('test_screenshot.png', io.BytesIO(png_data), 'image/png')
        }

        start = time.time()
        response = client.post(
            "/api/files/upload",
            files=files,
            headers=auth_headers
        )
        duration = time.time() - start

        print(f"\nScreenshot upload time: {duration * 1000:.2f}ms")

        assert response.status_code == 200
        assert duration < 1.0, "Screenshot upload should be fast"


class TestThumbnailPerformance:
    """Test thumbnail generation performance."""

    def test_thumbnail_status_polling(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test thumbnail status endpoint performance.

        Related to: TK-631 (background processing)
        """
        clip = sample_clips[0]

        times = []
        for _ in range(5):
            start = time.time()
            response = client.get(
                f"/api/files/clips/{clip.id}/thumbnail-status",
                headers=auth_headers
            )
            duration = time.time() - start
            times.append(duration)

            assert response.status_code == 200

        avg_time = sum(times) / len(times)
        print(f"\nThumbnail status check avg: {avg_time * 1000:.2f}ms")

        # Should be very fast (just DB lookup)
        assert avg_time < 0.05, "Status check should be instant"

    def test_thumbnail_serving_performance(
            self,
            client: TestClient,
            sample_clips
    ):
        """
        Test thumbnail serving performance.

        Related to: TK-632 (cache headers), TK-635 (file serving)
        """
        clip = sample_clips[0]

        if not clip.thumbnail_path:
            pytest.skip("Clip has no thumbnail")

        times = []
        for _ in range(3):
            start = time.time()
            response = client.get(f"/api/files/thumbnails/{clip.id}")
            duration = time.time() - start
            times.append(duration)

        avg_time = sum(times) / len(times)
        print(f"\nThumbnail serving avg: {avg_time * 1000:.2f}ms")

        # Check cache headers (TK-632)
        cache_control = response.headers.get('cache-control', '')
        print(f"Cache-Control: {cache_control}")

        assert 'public' in cache_control.lower(), "Should have public cache"
        assert avg_time < 0.1, "Thumbnail serving should be fast"


class TestStreamingPerformance:
    """Test video streaming performance."""

    def test_stream_initial_response_time(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test initial stream response time.

        Related to: TK-635 (streaming optimization)
        """
        # Find video clip
        video_clip = next(
            (c for c in sample_clips if c.clip_type.value == "video"),
            None
        )

        if not video_clip:
            pytest.skip("No video clips available")

        start = time.time()
        response = client.get(
            f"/api/files/stream/{video_clip.id}",
            headers=auth_headers
        )
        duration = time.time() - start

        print(f"\nStream initial response: {duration * 1000:.2f}ms")

        # Should start streaming quickly
        assert response.status_code in [200, 206]
        assert duration < 0.2, "Stream should start quickly"

    def test_stream_range_request_performance(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test range request performance.

        Related to: TK-635 (range request optimization)
        """
        video_clip = next(
            (c for c in sample_clips if c.clip_type.value == "video"),
            None
        )

        if not video_clip:
            pytest.skip("No video clips available")

        # Request specific range
        headers = {
            **auth_headers,
            "Range": "bytes=0-1023"  # First 1KB
        }

        start = time.time()
        response = client.get(
            f"/api/files/stream/{video_clip.id}",
            headers=headers
        )
        duration = time.time() - start

        print(f"\nRange request time: {duration * 1000:.2f}ms")

        assert response.status_code == 206  # Partial Content
        assert duration < 0.1, "Range request should be very fast"

    def test_stream_header_optimization(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test streaming response headers.

        Related to: TK-632 (cache), TK-635 (accept-ranges)
        """
        video_clip = next(
            (c for c in sample_clips if c.clip_type.value == "video"),
            None
        )

        if not video_clip:
            pytest.skip("No video clips available")

        response = client.get(
            f"/api/files/stream/{video_clip.id}",
            headers=auth_headers
        )

        print("\nStream headers:")
        print(f"  Accept-Ranges: {response.headers.get('accept-ranges')}")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        print(f"  Cache-Control: {response.headers.get('cache-control')}")

        assert 'accept-ranges' in response.headers, "Should support range requests"
        assert response.headers.get('accept-ranges') == 'bytes'


class TestFileDownloadPerformance:
    """Test file download performance."""

    def test_single_download_time(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test single file download performance.

        Related to: TK-635 (file serving optimization)
        """
        clip = sample_clips[0]

        start = time.time()
        response = client.get(
            f"/api/files/download/{clip.id}",
            headers=auth_headers
        )
        duration = time.time() - start

        print(f"\nSingle download time: {duration * 1000:.2f}ms")

        # Download should start quickly (streaming)
        assert response.status_code == 200
        assert duration < 0.5, "Download should start quickly"

    def test_bulk_download_preparation_time(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test bulk download ZIP preparation.

        Related to: TK-635 (ZIP streaming)
        """
        clip_ids = [c.id for c in sample_clips[:5]]

        start = time.time()
        response = client.post(
            "/api/files/download-bulk",
            json={"clip_ids": clip_ids},
            headers=auth_headers
        )
        duration = time.time() - start

        print(f"\nBulk download (5 files) time: {duration * 1000:.2f}ms")

        # Should start reasonably fast (streaming ZIP)
        assert response.status_code == 200
        assert duration < 2.0, "Bulk download should start in reasonable time"


class TestConcurrentFileOperations:
    """Test concurrent file operations."""

    def test_concurrent_thumbnail_serving(
            self,
            client: TestClient,
            sample_clips
    ):
        """
        Test concurrent thumbnail requests.

        Related to: TK-630 (connection pooling), TK-635 (file serving)
        """
        import concurrent.futures

        clips_with_thumbs = [c for c in sample_clips if c.thumbnail_path][:5]

        if len(clips_with_thumbs) < 3:
            pytest.skip("Not enough clips with thumbnails")

        def get_thumbnail(clip_id):
            start = time.time()
            response = client.get(f"/api/files/thumbnails/{clip_id}")
            return time.time() - start, response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(get_thumbnail, clip.id)
                for clip in clips_with_thumbs
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        times = [r[0] for r in results]
        statuses = [r[1] for r in results]

        print(f"\nConcurrent thumbnail serving:")
        print(f"  Average: {sum(times) / len(times) * 1000:.2f}ms")
        print(f"  Max: {max(times) * 1000:.2f}ms")
        print(f"  All successful: {all(s == 200 for s in statuses)}")

        assert all(s == 200 for s in statuses), "All should succeed"
        assert max(times) < 0.5, "Should handle concurrent requests well"

    def test_concurrent_streaming(
            self,
            client: TestClient,
            auth_headers: dict,
            sample_clips
    ):
        """
        Test concurrent video streaming.

        Related to: TK-635 (rate limiting for streams)
        """
        import concurrent.futures

        video_clips = [c for c in sample_clips if c.clip_type.value == "video"][:3]

        if len(video_clips) < 3:
            pytest.skip("Not enough video clips")

        def stream_video(clip_id):
            start = time.time()
            response = client.get(
                f"/api/files/stream/{clip_id}",
                headers=auth_headers
            )
            return time.time() - start, response.status_code

        # Simulate 3 concurrent streams (TK-635: max 3 per user)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(stream_video, clip.id)
                for clip in video_clips
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        times = [r[0] for r in results]
        statuses = [r[1] for r in results]

        print(f"\nConcurrent streaming (3 streams):")
        print(f"  Average start time: {sum(times) / len(times) * 1000:.2f}ms")
        print(f"  Max: {max(times) * 1000:.2f}ms")

        # All should start (after TK-635 might limit to 3)
        assert all(s in [200, 206] for s in statuses)


class TestStorageHealth:
    """Test storage system health."""

    def test_storage_accessibility(self, client: TestClient, auth_headers: dict):
        """
        Test storage health check.

        Related to: File processor storage checks
        """
        response = client.get("/api/files/health", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        print(f"\nStorage health:")
        print(f"  Status: {data.get('status')}")
        print(f"  Storage: {data.get('storage')}")
        print(f"  Free space: {data.get('free_space_gb')}GB")

        # Storage should be accessible
        assert data.get('storage') in ['available', 'skipped']

    def test_disk_space_monitoring(
            self,
            client: TestClient,
            admin_headers: dict
    ):
        """
        Test disk space in health endpoint.

        Related to: TK-637 (monitoring)
        """
        response = client.get("/health")

        assert response.status_code == 200

        data = response.json()
        print(f"\nSystem health:")
        print(f"  Status: {data.get('status')}")
        print(f"  Free space: {data.get('free_space_gb')}GB")

        # Should report disk space
        if 'free_space_gb' in data:
            assert data['free_space_gb'] > 0, "Should have free space"


@pytest.mark.benchmark
class TestFileBenchmarks:
    """Benchmark file operations."""

    def test_benchmark_thumbnail_serving(
            self,
            benchmark,
            client: TestClient,
            sample_clips
    ):
        """Benchmark thumbnail serving."""
        clip = next((c for c in sample_clips if c.thumbnail_path), None)

        if not clip:
            pytest.skip("No clip with thumbnail")

        def get_thumbnail():
            return client.get(f"/api/files/thumbnails/{clip.id}")

        result = benchmark(get_thumbnail)
        assert result.status_code == 200
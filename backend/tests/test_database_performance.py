"""
Database query performance tests.

Tests SQL query optimization, N+1 detection, and index usage.
Related to: TK-629 (SQL optimization), TK-630 (connection pooling)
"""
import time

import pytest
from app.models.award import Award
from app.models.award_type import AwardType
from app.models.clip import Clip
from app.models.user import User
from sqlalchemy import text, func
from sqlalchemy.orm import Session


class TestQueryOptimization:
    """Test query efficiency and N+1 problems."""

    def test_clips_list_query_count(
            self,
            db_session: Session,
            query_counter,
            sample_clips
    ):
        """
        Detect N+1 queries in clips listing.

        Related to: TK-629
        Expected after optimization: 1-3 queries total (not 1 per clip)
        """
        query_counter.count = 0

        # Simulate what /api/files/clips does
        clips = db_session.query(Clip).filter(
            Clip.is_deleted == False
        ).limit(20).all()

        # Access relationships (trigger lazy loads if not optimized)
        for clip in clips:
            _ = clip.uploader.username
            _ = len(clip.awards)

        print(f"\nClips list query count: {query_counter.count}")
        print(f"Clips loaded: {len(clips)}")
        print(f"Queries per clip: {query_counter.count / len(clips):.2f}")

        # Baseline: Currently might be high due to lazy loading
        # After TK-629 with selectinload/joinedload: should be ~3 queries
        assert query_counter.count > 0, "Should execute queries"

        # Log current state for comparison
        if query_counter.count > 20:
            print("WARNING: Possible N+1 problem detected!")
            print("After TK-629, this should be ~3 queries")

    def test_clip_with_awards_query_count(
            self,
            db_session: Session,
            query_counter,
            sample_clips,
            sample_awards
    ):
        """
        Test query count when loading clip with awards.

        Expected: 2-3 queries (clip + awards + users in one go)
        """
        query_counter.count = 0
        clip = sample_clips[0]

        # Reload from DB
        db_clip = db_session.query(Clip).filter(
            Clip.id == clip.id
        ).first()

        # Access awards (this might trigger N+1)
        for award in db_clip.awards:
            _ = award.user.username
            _ = award.award_name

        print(f"\nClip with awards query count: {query_counter.count}")
        print(f"Awards loaded: {len(db_clip.awards)}")

        # Should be optimized with joinedload
        assert query_counter.count < 10, "Should use eager loading"

    def test_awards_aggregation_query_count(
            self,
            db_session: Session,
            query_counter,
            sample_clips,
            sample_awards
    ):
        """
        Test query count for award statistics.

        Related to: TK-629 (aggregation optimization)
        """
        query_counter.count = 0

        # Simulate award stats query
        total_awards = db_session.query(func.count(Award.id)).scalar()

        most_popular = db_session.query(
            Award.award_name,
            func.count(Award.id).label('count')
        ).group_by(
            Award.award_name
        ).order_by(
            func.count(Award.id).desc()
        ).first()

        print(f"\nAward stats query count: {query_counter.count}")
        print(f"Total awards: {total_awards}")

        # Should be efficient aggregation
        assert query_counter.count < 5, "Aggregations should be efficient"


class TestIndexUsage:
    """Test if indexes are used effectively."""

    def test_created_at_sort_performance(
            self,
            db_session: Session,
            sample_clips
    ):
        """
        Test sorting by created_at performance.

        Related to: TK-629 (need index on created_at)
        """
        start = time.time()

        clips = db_session.query(Clip).filter(
            Clip.is_deleted == False
        ).order_by(
            Clip.created_at.desc()
        ).limit(20).all()

        duration = time.time() - start

        print(f"\nSort by created_at time: {duration * 1000:.2f}ms")
        print(f"Clips returned: {len(clips)}")

        # Should be fast with index
        assert duration < 0.1, "Indexed sort should be fast"

    def test_filter_by_uploader_performance(
            self,
            db_session: Session,
            sample_clips,
            test_user
    ):
        """
        Test filtering by uploader_id.

        Related to: TK-629 (uploader_id should have index)
        """
        start = time.time()

        clips = db_session.query(Clip).filter(
            Clip.uploader_id == test_user.id,
            Clip.is_deleted == False
        ).all()

        duration = time.time() - start

        print(f"\nFilter by uploader time: {duration * 1000:.2f}ms")
        print(f"Clips found: {len(clips)}")

        assert duration < 0.05, "Indexed filter should be very fast"

    def test_award_lookup_performance(
            self,
            db_session: Session,
            sample_clips,
            sample_awards
    ):
        """
        Test award lookup by clip_id.

        Related to: TK-629 (need composite index on clip_id + user_id)
        """
        clip = sample_clips[0]

        start = time.time()

        awards = db_session.query(Award).filter(
            Award.clip_id == clip.id
        ).all()

        duration = time.time() - start

        print(f"\nAward lookup time: {duration * 1000:.2f}ms")
        print(f"Awards found: {len(awards)}")

        assert duration < 0.05, "Award lookup should be fast"


class TestPaginationPerformance:
    """Test pagination efficiency."""

    def test_offset_pagination_performance(
            self,
            db_session: Session,
            sample_clips
    ):
        """
        Test current offset-based pagination.

        Related to: TK-633 (should move to cursor-based)
        """
        times = []

        for page in [1, 2, 3, 5, 10]:
            offset = (page - 1) * 20

            start = time.time()
            clips = db_session.query(Clip).filter(
                Clip.is_deleted == False
            ).order_by(
                Clip.created_at.desc()
            ).offset(offset).limit(20).all()
            duration = time.time() - start

            times.append((page, duration))

        print("\nOffset pagination performance:")
        for page, duration in times:
            print(f"  Page {page}: {duration * 1000:.2f}ms")

        # Offset pagination gets slower with higher pages
        # After TK-633 (cursor-based), all should be similar
        first_page_time = times[0][1]
        last_page_time = times[-1][1]

        print(f"First page: {first_page_time * 1000:.2f}ms")
        print(f"Last page: {last_page_time * 1000:.2f}ms")
        print(f"Slowdown: {last_page_time / first_page_time:.2f}x")

    def test_count_query_performance(
            self,
            db_session: Session,
            sample_clips
    ):
        """
        Test performance of count queries for pagination.

        Related to: TK-633 (cache count results)
        """
        start = time.time()

        total = db_session.query(Clip).filter(
            Clip.is_deleted == False
        ).count()

        duration = time.time() - start

        print(f"\nCount query time: {duration * 1000:.2f}ms")
        print(f"Total clips: {total}")

        # Count should be fast
        assert duration < 0.05, "Count should be fast with proper indexes"


class TestConnectionPooling:
    """Test database connection pooling."""

    def test_concurrent_db_access(
            self,
            db_session: Session,
            sample_clips
    ):
        """
        Test concurrent database access.

        Related to: TK-630 (connection pooling)
        """
        import concurrent.futures

        def query_clips():
            start = time.time()
            clips = db_session.query(Clip).filter(
                Clip.is_deleted == False
            ).limit(10).all()
            return time.time() - start, len(clips)

        # Simulate 5 concurrent queries
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(query_clips) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        times = [r[0] for r in results]

        print(f"\nConcurrent DB access:")
        print(f"  Average: {sum(times) / len(times) * 1000:.2f}ms")
        print(f"  Max: {max(times) * 1000:.2f}ms")
        print(f"  All successful: {all(r[1] > 0 for r in results)}")

        # All should succeed (no locks)
        assert all(r[1] > 0 for r in results), "All queries should succeed"


class TestQueryComplexity:
    """Test complex query performance."""

    def test_join_performance(
            self,
            db_session: Session,
            sample_clips,
            sample_awards
    ):
        """
        Test join query performance.

        Related to: TK-629 (optimize joins)
        """
        start = time.time()

        # Complex join query
        results = db_session.query(Clip).join(
            Award, Clip.id == Award.clip_id
        ).join(
            User, Award.user_id == User.id
        ).filter(
            Clip.is_deleted == False
        ).distinct().all()

        duration = time.time() - start

        print(f"\nJoin query time: {duration * 1000:.2f}ms")
        print(f"Results: {len(results)}")

        assert duration < 0.5, "Join queries should be reasonable"

    def test_aggregation_performance(
            self,
            db_session: Session,
            sample_clips,
            sample_awards
    ):
        """
        Test aggregation query performance.

        Related to: TK-629, TK-634 (cache aggregations)
        """
        start = time.time()

        # Aggregation: clips with award count
        results = db_session.query(
            Clip.id,
            Clip.filename,
            func.count(Award.id).label('award_count')
        ).outerjoin(
            Award, Clip.id == Award.clip_id
        ).filter(
            Clip.is_deleted == False
        ).group_by(
            Clip.id
        ).order_by(
            func.count(Award.id).desc()
        ).limit(10).all()

        duration = time.time() - start

        print(f"\nAggregation query time: {duration * 1000:.2f}ms")
        print(f"Results: {len(results)}")

        # Aggregations are expensive but should be cacheable (TK-634)
        assert duration < 0.3, "Aggregations should be optimized"


class TestDatabaseHealth:
    """Test database health and configuration."""

    def test_wal_mode_enabled(self, db_session: Session):
        """
        Verify WAL mode is enabled.

        Related to: TK-630 (SQLite optimization)
        """
        result = db_session.execute(text("PRAGMA journal_mode")).fetchone()
        journal_mode = result[0]

        print(f"\nJournal mode: {journal_mode}")

        assert journal_mode.lower() == 'wal', "WAL mode should be enabled"

    def test_foreign_keys_enabled(self, db_session: Session):
        """Verify foreign keys are enforced."""
        result = db_session.execute(text("PRAGMA foreign_keys")).fetchone()
        fk_enabled = result[0]

        print(f"\nForeign keys enabled: {bool(fk_enabled)}")

        assert fk_enabled == 1, "Foreign keys should be enabled"

    def test_cache_size(self, db_session: Session):
        """
        Check cache size configuration.

        Related to: TK-630 (increase cache for better performance)
        """
        result = db_session.execute(text("PRAGMA cache_size")).fetchone()
        cache_size = result[0]

        print(f"\nCache size: {cache_size} pages")

        # Negative values = KB, positive = pages
        if cache_size < 0:
            cache_mb = abs(cache_size) / 1024
            print(f"Cache size: {cache_mb:.2f}MB")

        # After TK-630, should be at least 64MB
        assert abs(cache_size) >= 1000, "Cache should be configured"

    def test_database_size(self, db_session: Session):
        """Check database file size and page count."""
        page_count = db_session.execute(text("PRAGMA page_count")).fetchone()[0]
        page_size = db_session.execute(text("PRAGMA page_size")).fetchone()[0]

        db_size_mb = (page_count * page_size) / (1024 * 1024)

        print(f"\nDatabase size:")
        print(f"  Pages: {page_count}")
        print(f"  Page size: {page_size} bytes")
        print(f"  Total: {db_size_mb:.2f}MB")

        # Just informational
        assert page_count > 0, "Database should have pages"


@pytest.mark.slow
class TestLargeDatasetPerformance:
    """Test performance with larger datasets."""

    def test_1000_clips_performance(self, db_session: Session, test_user):
        """
        Test performance with 1000 clips.

        Related to: TK-629, TK-633
        """
        # Create 1000 clips
        print("\nCreating 1000 test clips...")
        from app.models.clip import ClipType

        clips = []
        for i in range(1000):
            clip = Clip(
                filename=f"large_test_{i}.mp4",
                file_path=f"/tmp/large_{i}.mp4",
                clip_type=ClipType.VIDEO,
                file_size=1024 * 1024,
                uploader_id=test_user.id
            )
            clips.append(clip)

            if (i + 1) % 100 == 0:
                db_session.bulk_save_objects(clips)
                db_session.commit()
                clips = []

        if clips:
            db_session.bulk_save_objects(clips)
            db_session.commit()

        # Test query performance
        start = time.time()
        result = db_session.query(Clip).filter(
            Clip.is_deleted == False
        ).order_by(
            Clip.created_at.desc()
        ).limit(20).all()
        duration = time.time() - start

        print(f"Query time with 1000 clips: {duration * 1000:.2f}ms")

        # Should still be fast with proper indexes
        assert duration < 0.2, "Should scale well to 1000 clips"

        # Cleanup
        db_session.query(Clip).filter(
            Clip.filename.like('large_test_%')
        ).delete()
        db_session.commit()

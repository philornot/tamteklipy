"""
Test performance query dla /api/files/clips
Porównuje joinedload vs selectinload
"""
import sys
import time
from pathlib import Path

# Dodaj backend do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from sqlalchemy import text
from sqlalchemy.orm import joinedload, selectinload
from app.core.database import SessionLocal
from app.models.clip import Clip
from app.models.award import Award
from app.core.init_db import init_db  # ...added import

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modułowe zmienne do podsumowania
time_joinedload = None
time_selectinload = None


def setup_module(module):
    """Funkcja wywoływana przez pytest przed uruchomieniem testów w module.
    Tworzy tabele w bazie jeśli nie istnieją (wywołuje init_db()).
    """
    logger.info("Uruchamiam init_db() przed testami modułu test_query_perf.py")
    init_db()


# Helper: wykonuje joinedload i zwraca czas
def run_joinedload():
    db = SessionLocal()
    try:
        start = time.time()
        clips = db.query(Clip).options(
            joinedload(Clip.awards).joinedload(Award.user)
        ).filter(
            Clip.is_deleted == False
        ).order_by(Clip.created_at.desc()).limit(12).all()
        elapsed = time.time() - start

        logger.info(f"✓ Loaded {len(clips)} clips")
        logger.info(f"⏱️  Time: {elapsed * 1000:.2f}ms")
        total_awards = sum(len(clip.awards) for clip in clips)
        logger.info(f"📊 Total awards: {total_awards}")

        return elapsed
    finally:
        db.close()


# Helper: wykonuje selectinload i zwraca czas
def run_selectinload():
    db = SessionLocal()
    try:
        start = time.time()
        clips = db.query(Clip).options(
            selectinload(Clip.awards).selectinload(Award.user)
        ).filter(
            Clip.is_deleted == False
        ).order_by(Clip.created_at.desc()).limit(12).all()
        elapsed = time.time() - start

        logger.info(f"✓ Loaded {len(clips)} clips")
        logger.info(f"⏱️  Time: {elapsed * 1000:.2f}ms")
        total_awards = sum(len(clip.awards) for clip in clips)
        logger.info(f"📊 Total awards: {total_awards}")

        return elapsed
    finally:
        db.close()


def test_joinedload():
    """
    Test joinedload (stara metoda - O(N*M))
    """
    global time_joinedload
    elapsed = run_joinedload()
    # Zapisz wynik i zrób prostą asercję
    time_joinedload = elapsed
    assert isinstance(elapsed, float) and elapsed >= 0


def test_selectinload():
    """
    Test selectinload (nowa metoda - O(N+M))
    """
    global time_selectinload
    elapsed = run_selectinload()
    # Zapisz wynik i zrób prostą asercję
    time_selectinload = elapsed
    assert isinstance(elapsed, float) and elapsed >= 0


def test_explain_query():
    """
    EXPLAIN QUERY PLAN dla głównego query
    """
    db = SessionLocal()

    try:
        logger.info("")
        logger.info("=" * 60)
        logger.info("TEST 3: EXPLAIN QUERY PLAN")
        logger.info("=" * 60)

        # Test query z filtrami
        query_sql = """
        EXPLAIN QUERY PLAN
        SELECT clips.* 
        FROM clips 
        WHERE clips.is_deleted = 0 
        ORDER BY clips.created_at DESC 
        LIMIT 12
        """

        result = db.execute(text(query_sql))

        logger.info("\nQuery plan:")
        for row in result:
            logger.info(f"  {row}")

        # Sprawdź czy używa indexów
        result = db.execute(text(query_sql))
        plan_text = " ".join(str(row) for row in result)

        if "SCAN TABLE" in plan_text:
            logger.warning("⚠️  SCAN TABLE detected - brak użycia indexu!")
        else:
            logger.info("✓ Query używa indexów")

    finally:
        db.close()


def test_index_usage():
    """
    Sprawdź czy indexy są używane
    """
    db = SessionLocal()

    try:
        logger.info("")
        logger.info("=" * 60)
        logger.info("TEST 4: Index usage")
        logger.info("=" * 60)

        # Lista indexów
        result = db.execute(text("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='clips'"))

        logger.info("\nIndexy na tabeli 'clips':")
        for row in result:
            if row[0] and not row[0].startswith('sqlite_'):
                logger.info(f"  ✓ {row[0]}")
                if row[1]:
                    logger.info(f"    {row[1]}")

    finally:
        db.close()


def main():
    logger.info("🔍 Testing query performance for /api/files/clips")
    logger.info("")

    # Test 1: joinedload
    time_joinedload_local = run_joinedload()

    # Test 2: selectinload
    time_selectinload_local = run_selectinload()

    # Test 3: EXPLAIN
    test_explain_query()

    # Test 4: Indexy
    test_index_usage()

    # Podsumowanie
    logger.info("")
    logger.info("=" * 60)
    logger.info("PODSUMOWANIE")
    logger.info("=" * 60)
    logger.info(f"joinedload:   {time_joinedload_local * 1000:.2f}ms")
    logger.info(f"selectinload: {time_selectinload_local * 1000:.2f}ms")

    if time_selectinload_local < time_joinedload_local:
        improvement = ((time_joinedload_local - time_selectinload_local) / time_joinedload_local) * 100
        logger.info(f"✓ Poprawa: {improvement:.1f}% szybciej")
    else:
        logger.warning(f"⚠️  selectinload wolniejszy (może mała liczba rekordów)")

    # Acceptance criteria
    logger.info("")
    logger.info("Acceptance Criteria:")
    if time_selectinload_local < 0.2:
        logger.info(f"✓ Query time < 200ms ({time_selectinload_local * 1000:.0f}ms)")
    else:
        logger.warning(f"✗ Query time > 200ms ({time_selectinload_local * 1000:.0f}ms)")


if __name__ == "__main__":
    main()
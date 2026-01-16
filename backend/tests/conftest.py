"""
Performance test suite configuration and fixtures.

Provides reusable fixtures for performance testing.
"""
import os
import sys
import time
import pytest
from pathlib import Path
from typing import Generator

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.clip import Clip, ClipType
from app.models.award import Award
from app.models.award_type import AwardType

# Test database
TEST_DATABASE_URL = "sqlite:///./test_performance.db"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Disable SQL logging for performance tests
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Query counter for detecting N+1 problems
class QueryCounter:
    """Counts SQL queries executed during test."""

    def __init__(self):
        self.count = 0
        self.queries = []

    def __call__(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self.queries.append({
            'statement': statement,
            'parameters': parameters,
            'time': time.time()
        })


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create fresh database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def query_counter(db_session):
    """Track SQL queries for N+1 detection."""
    counter = QueryCounter()
    event.listen(engine, "before_cursor_execute", counter, named=True)

    yield counter

    event.remove(engine, "before_cursor_execute", counter)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with database override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session) -> User:
    """Create test user."""
    from app.core.security import hash_password

    user = User(
        username="testuser",
        email="test@test.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
        is_active=True,
        is_admin=False,
        award_scopes=["award:test"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture(scope="function")
def admin_user(db_session) -> User:
    """Create admin user."""
    from app.core.security import hash_password

    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Admin User",
        is_active=True,
        is_admin=True,
        award_scopes=[]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture(scope="function")
def auth_token(test_user) -> str:
    """Generate JWT token for test user."""
    return create_access_token(
        user_id=test_user.id,
        username=test_user.username,
        scopes=test_user.award_scopes
    )


@pytest.fixture(scope="function")
def admin_token(admin_user) -> str:
    """Generate JWT token for admin user."""
    return create_access_token(
        user_id=admin_user.id,
        username=admin_user.username,
        scopes=[]
    )


@pytest.fixture(scope="function")
def auth_headers(auth_token) -> dict:
    """Authorization headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def admin_headers(admin_token) -> dict:
    """Admin authorization headers."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def sample_clips(db_session, test_user, admin_user) -> list[Clip]:
    """Create sample clips for testing."""
    import tempfile
    import platform

    # Use platform-appropriate absolute paths
    if platform.system() == "Windows":
        base_path = Path("C:/temp/test_clips")
    else:
        base_path = Path("/tmp/test_clips")

    # Ensure directory exists (optional, for safety)
    base_path.mkdir(parents=True, exist_ok=True)

    clips = []
    for i in range(50):
        clip = Clip(
            filename=f"test_video_{i}.mp4",
            file_path=str(base_path / f"test_video_{i}.mp4"),  # Absolute path
            clip_type=ClipType.VIDEO if i % 2 == 0 else ClipType.SCREENSHOT,
            file_size=1024 * 1024 * (i + 1),
            duration=60 + i if i % 2 == 0 else None,
            width=1920,
            height=1080,
            uploader_id=test_user.id if i % 3 != 0 else admin_user.id,
            thumbnail_path=str(base_path / f"thumb_{i}.jpg") if i % 2 == 0 else None
        )
        db_session.add(clip)
        clips.append(clip)

    db_session.commit()

    for clip in clips:
        db_session.refresh(clip)

    return clips


@pytest.fixture(scope="function")
def sample_award_types(db_session) -> list[AwardType]:
    """Create sample award types."""
    award_types = [
        AwardType(
            name="award:epic",
            display_name="Epic Moment",
            description="For epic moments",
            icon="🔥",
            color="#FF4500",
            is_system_award=True
        ),
        AwardType(
            name="award:funny",
            display_name="Funny",
            description="For funny clips",
            icon="😂",
            color="#FFD700",
            is_system_award=True
        ),
        AwardType(
            name="award:pro",
            display_name="Pro Play",
            description="For pro plays",
            icon="⭐",
            color="#4169E1",
            is_system_award=True
        )
    ]

    for at in award_types:
        db_session.add(at)

    db_session.commit()

    for at in award_types:
        db_session.refresh(at)

    return award_types


@pytest.fixture(scope="function")
def sample_awards(db_session, sample_clips, test_user, admin_user, sample_award_types) -> list[Award]:
    """Create sample awards."""
    awards = []

    for i, clip in enumerate(sample_clips[:20]):
        for j, award_type in enumerate(sample_award_types):
            if (i + j) % 3 == 0:
                award = Award(
                    clip_id=clip.id,
                    user_id=test_user.id if j % 2 == 0 else admin_user.id,
                    award_name=award_type.name
                )
                db_session.add(award)
                awards.append(award)

    db_session.commit()

    for award in awards:
        db_session.refresh(award)

    return awards


class PerformanceMetrics:
    """Helper class for collecting performance metrics."""

    def __init__(self):
        self.response_times = []
        self.query_counts = []
        self.memory_usage = []

    def add_response_time(self, duration: float):
        """Add response time in seconds."""
        self.response_times.append(duration)

    def add_query_count(self, count: int):
        """Add query count."""
        self.query_counts.append(count)

    def add_memory_usage(self, bytes_used: int):
        """Add memory usage in bytes."""
        self.memory_usage.append(bytes_used)

    @property
    def avg_response_time(self) -> float:
        """Average response time in ms."""
        if not self.response_times:
            return 0.0
        return (sum(self.response_times) / len(self.response_times)) * 1000

    @property
    def max_response_time(self) -> float:
        """Max response time in ms."""
        if not self.response_times:
            return 0.0
        return max(self.response_times) * 1000

    @property
    def min_response_time(self) -> float:
        """Min response time in ms."""
        if not self.response_times:
            return 0.0
        return min(self.response_times) * 1000

    @property
    def avg_queries(self) -> float:
        """Average queries per request."""
        if not self.query_counts:
            return 0.0
        return sum(self.query_counts) / len(self.query_counts)

    @property
    def max_queries(self) -> int:
        """Max queries in single request."""
        if not self.query_counts:
            return 0
        return max(self.query_counts)

    def report(self) -> str:
        """Generate performance report."""
        return f"""
Performance Metrics:
  Response Times:
    - Average: {self.avg_response_time:.2f}ms
    - Min: {self.min_response_time:.2f}ms
    - Max: {self.max_response_time:.2f}ms
  Query Counts:
    - Average: {self.avg_queries:.1f} queries/request
    - Max: {self.max_queries} queries/request
  Total Requests: {len(self.response_times)}
"""


@pytest.fixture
def perf_metrics():
    """Fixture providing performance metrics collector."""
    return PerformanceMetrics()
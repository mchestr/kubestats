import uuid
from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic_core import MultiHostUrl
from sqlalchemy import Engine
from sqlmodel import Session, create_engine, text

from kubestats.core.config import settings
from kubestats.core.db import init_db
from kubestats.main import app
from kubestats.models import Repository
from kubestats.tests.utils.user import authentication_token_from_email
from kubestats.tests.utils.utils import get_superuser_token_headers


def prep_db() -> None:
    """Create the database engine for testing."""
    engine = create_engine(
        str(
            MultiHostUrl.build(
                scheme="postgresql+psycopg2",
                username=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                path="postgres",
            )
        ),
        isolation_level="AUTOCOMMIT",
    )

    with engine.connect() as conn:
        try:
            # Ensure the database is created
            conn.execute(text("DROP DATABASE IF EXISTS test_db"))
        except Exception as e:
            print(f"Error dropping database: {e}")

        conn.execute(text("CREATE DATABASE test_db"))


def apply_migrations() -> None:
    """Apply Alembic migrations to the test database."""
    print("Applying migrations to the test database...")

    alembic_ini_path = "alembic.ini"
    alembic_cfg = Config(alembic_ini_path)
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied successfully")


@pytest.fixture(scope="session", autouse=True)
def engine() -> Generator[Engine, None, None]:
    """Create the database engine for testing."""
    prep_db()
    db_url = str(
        MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            path="test_db",
        )
    )
    test_engine = create_engine(db_url)
    apply_migrations()
    yield test_engine
    # No cleanup needed for the engine in this case


@pytest.fixture(scope="session", autouse=True)
def db(engine: Engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email="test@example.com", db=db
    )


@pytest.fixture
def sample_repository(db: Session) -> Repository:
    """Create a sample repository for testing."""
    # Ensure session is in a good state
    if db.in_transaction():
        transaction = db.get_transaction()
        if transaction is not None and transaction.is_active:
            try:
                db.rollback()
            except Exception:
                pass

    # Generate unique IDs to avoid conflicts
    unique_id = uuid.uuid4()
    github_id = hash(str(unique_id)) % 10000000  # Generate a positive integer

    repository = Repository(
        id=str(unique_id),
        name=f"test-repo-{unique_id.hex[:8]}",
        full_name=f"testuser/test-repo-{unique_id.hex[:8]}",
        owner="testuser",
        github_id=abs(github_id),  # Ensure positive
        description="A test repository",
        language="Python",
        default_branch="main",
        created_at=datetime.now(timezone.utc),
        discovered_at=datetime.now(timezone.utc),
    )

    try:
        db.add(repository)
        db.commit()
        db.refresh(repository)
        return repository
    except Exception:
        db.rollback()
        raise

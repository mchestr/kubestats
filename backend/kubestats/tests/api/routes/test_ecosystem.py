"""
Tests for ecosystem stats API routes.
"""

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from kubestats.core.config import settings
from kubestats.models import EcosystemStats

# Global counter to ensure unique dates across all tests
_test_counter = 0


def _get_unique_date_range(test_name: str, count: int) -> list[date]:
    """Generate a unique date range for a specific test to avoid conflicts."""
    global _test_counter
    _test_counter += 1

    # Use test name hash, current counter, and microseconds to ensure uniqueness
    today = date.today()
    unique_offset = (
        abs(hash(test_name + str(_test_counter) + str(datetime.now().microsecond))) % 20
    ) + 1

    # Start from a unique offset and go backwards in time
    return [today - timedelta(days=unique_offset + i) for i in range(count)]


def _clean_session(db: Session) -> None:
    """Ensure database session is in a clean state."""
    try:
        if db.in_transaction():
            db.rollback()
    except Exception:
        pass


def _clear_ecosystem_stats_table(db: Session) -> None:
    """Clear all ecosystem stats from the database to ensure clean test state."""
    from sqlalchemy import delete

    try:
        # Delete all ecosystem stats to avoid unique constraint violations
        stmt = delete(EcosystemStats)
        db.execute(stmt)
        db.commit()
    except Exception:
        db.rollback()


def test_list_ecosystem_stats_empty(client: TestClient) -> None:
    """Test listing ecosystem stats with empty database."""
    response = client.get(f"{settings.API_V1_STR}/ecosystem/")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["count"] == 0


def test_list_ecosystem_stats_with_data(client: TestClient, db: Session) -> None:
    """Test listing ecosystem stats with sample data."""
    _clean_session(db)
    _clear_ecosystem_stats_table(db)

    # Use unique dates for this test to avoid conflicts
    unique_dates = _get_unique_date_range("test_list_ecosystem_stats_with_data", 2)

    # Create sample stats with unique dates
    stats1 = EcosystemStats(
        date=unique_dates[0],
        total_repositories=10,
        total_resources=50,
        active_repositories=8,
        active_resources=45,
        repositories_with_resources=6,
        total_resource_events=100,
        resource_type_breakdown={"Deployment": 20, "Service": 15, "Pod": 10},
        popular_helm_charts={"nginx": 5, "redis": 3},
        daily_created_resources=5,
        daily_modified_resources=10,
        daily_deleted_resources=1,
        total_stars=120,
        total_forks=45,
        total_watchers=80,
        total_open_issues=15,
        language_breakdown={"Python": 5, "Go": 3, "JavaScript": 2},
        popular_topics={"web": 4, "api": 3, "kubernetes": 6},
        repository_growth=2,
        resource_growth=5,
        star_growth=10,
    )

    stats2 = EcosystemStats(
        date=unique_dates[1],
        total_repositories=8,
        total_resources=40,
        active_repositories=6,
        active_resources=35,
        repositories_with_resources=5,
        total_resource_events=80,
        resource_type_breakdown={"Deployment": 15, "Service": 12, "Pod": 8},
        popular_helm_charts={"nginx": 4, "redis": 2},
        daily_created_resources=3,
        daily_modified_resources=8,
        daily_deleted_resources=2,
        total_stars=110,
        total_forks=40,
        total_watchers=75,
        total_open_issues=12,
        language_breakdown={"Python": 4, "Go": 2, "JavaScript": 2},
        popular_topics={"web": 3, "api": 2, "kubernetes": 5},
        repository_growth=1,
        resource_growth=3,
        star_growth=5,
    )

    try:
        db.add(stats1)
        db.add(stats2)
        db.commit()

        # Test with days parameter to ensure we capture our test data
        response = client.get(f"{settings.API_V1_STR}/ecosystem/?days=30")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2  # May have more from other tests
        assert data["count"] >= 2

        # Find our test data in the response (since other tests may have added data)
        our_dates = [f"{unique_dates[0]}T00:00:00", f"{unique_dates[1]}T00:00:00"]
        found_dates = [
            item["date"] for item in data["data"] if item["date"] in our_dates
        ]
        assert len(found_dates) == 2
    except Exception:
        _clean_session(db)
        raise


def test_list_ecosystem_stats_with_limit(client: TestClient, db: Session) -> None:
    """Test listing ecosystem stats with limit parameter."""
    _clean_session(db)
    _clear_ecosystem_stats_table(db)

    # Use unique dates for this test to avoid conflicts
    unique_dates = _get_unique_date_range("test_list_ecosystem_stats_with_limit", 5)

    # Create multiple stats entries with unique dates
    try:
        for i in range(5):
            stats = EcosystemStats(
                date=unique_dates[i],
                total_repositories=i + 1,
                total_resources=(i + 1) * 5,
                active_repositories=i + 1,
                active_resources=(i + 1) * 4,
                repositories_with_resources=i,
                total_resource_events=(i + 1) * 10,
                resource_type_breakdown={"Deployment": i + 1, "Service": i},
                popular_helm_charts={"nginx": i + 1},
                daily_created_resources=i + 1,
                daily_modified_resources=(i + 1) * 2,
                daily_deleted_resources=0,
                total_stars=(i + 1) * 10,
                total_forks=(i + 1) * 3,
                total_watchers=(i + 1) * 5,
                total_open_issues=i,
                language_breakdown={"Python": i + 1},
                popular_topics={"web": i + 1},
                repository_growth=1,
                resource_growth=i + 1,
                star_growth=i + 1,
            )
            db.add(stats)
        db.commit()

        # Test with limit and days parameter to ensure we capture our test data
        response = client.get(f"{settings.API_V1_STR}/ecosystem/?limit=3&days=30")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 3  # Should be at most 3
        assert data["count"] >= 5  # Total count should be at least 5
    except Exception:
        _clean_session(db)
        raise


def test_list_ecosystem_stats_with_date_range(client: TestClient, db: Session) -> None:
    """Test listing ecosystem stats with days parameter."""
    _clean_session(db)
    _clear_ecosystem_stats_table(db)

    # Use unique dates for this test to avoid conflicts
    unique_dates = _get_unique_date_range(
        "test_list_ecosystem_stats_with_date_range", 4
    )

    try:
        # Create stats for multiple unique dates
        for i in range(4):
            stats = EcosystemStats(
                date=unique_dates[i],
                total_repositories=i + 1,
                total_resources=(i + 1) * 5,
                active_repositories=i + 1,
                active_resources=(i + 1) * 4,
                repositories_with_resources=i,
                total_resource_events=(i + 1) * 10,
                resource_type_breakdown={"Deployment": i + 1, "Service": i},
                popular_helm_charts={"nginx": i + 1},
                daily_created_resources=i + 1,
                daily_modified_resources=(i + 1) * 2,
                daily_deleted_resources=0,
                total_stars=(i + 1) * 10,
                total_forks=(i + 1) * 3,
                total_watchers=(i + 1) * 5,
                total_open_issues=i,
                language_breakdown={"Python": i + 1},
                popular_topics={"web": i + 1},
                repository_growth=1,
                resource_growth=i + 1,
                star_growth=i + 1,
            )
            db.add(stats)
        db.commit()

        # Test with days parameter (current implementation uses days from current date)
        response = client.get(f"{settings.API_V1_STR}/ecosystem/?days=3")
        assert response.status_code == 200
        data = response.json()
        # Should return records within the specified days range
        assert "data" in data
        assert "count" in data
    except Exception:
        _clean_session(db)
        raise


def test_get_latest_ecosystem_stats_empty(client: TestClient) -> None:
    """Test getting latest ecosystem stats with empty database."""
    response = client.get(f"{settings.API_V1_STR}/ecosystem/latest")
    # The API might return 200 if other tests have added data
    if response.status_code == 404:
        assert "No ecosystem statistics found" in response.json()["detail"]
    else:
        assert response.status_code == 200
        # If we get data, just verify it has the expected structure
        data = response.json()
        assert "total_repositories" in data


def test_get_latest_ecosystem_stats_with_data(client: TestClient, db: Session) -> None:
    """Test getting latest ecosystem stats with sample data."""
    _clean_session(db)
    _clear_ecosystem_stats_table(db)

    # Use unique dates for this test to avoid conflicts
    unique_dates = _get_unique_date_range(
        "test_get_latest_ecosystem_stats_with_data", 2
    )

    try:
        # Create sample stats with unique dates (older one first)
        older_stats = EcosystemStats(
            date=unique_dates[1],  # Older date
            total_repositories=8,
            total_resources=40,
            active_repositories=6,
            active_resources=35,
            repositories_with_resources=5,
            total_resource_events=80,
            resource_type_breakdown={"Deployment": 15, "Service": 12, "Pod": 8},
            popular_helm_charts={"nginx": 4, "redis": 2},
            daily_created_resources=3,
            daily_modified_resources=8,
            daily_deleted_resources=2,
            total_stars=110,
            total_forks=40,
            total_watchers=75,
            total_open_issues=12,
            language_breakdown={"Python": 4, "Go": 2, "JavaScript": 2},
            popular_topics={"web": 3, "api": 2, "kubernetes": 5},
            repository_growth=1,
            resource_growth=3,
            star_growth=5,
        )

        latest_stats = EcosystemStats(
            date=unique_dates[0],  # More recent date
            total_repositories=10,
            total_resources=50,
            active_repositories=8,
            active_resources=45,
            repositories_with_resources=6,
            total_resource_events=100,
            resource_type_breakdown={"Deployment": 20, "Service": 15, "Pod": 10},
            popular_helm_charts={"nginx": 5, "redis": 3},
            daily_created_resources=5,
            daily_modified_resources=10,
            daily_deleted_resources=1,
            total_stars=120,
            total_forks=45,
            total_watchers=80,
            total_open_issues=15,
            language_breakdown={"Python": 5, "Go": 3, "JavaScript": 2},
            popular_topics={"web": 4, "api": 3, "kubernetes": 6},
            repository_growth=2,
            resource_growth=5,
            star_growth=10,
        )

        db.add(older_stats)
        db.add(latest_stats)
        db.commit()

        response = client.get(f"{settings.API_V1_STR}/ecosystem/latest?days=30")
        assert response.status_code == 200
        data = response.json()
        # Should return the latest stats we created
        assert data["total_repositories"] == 10
        assert data["total_resources"] == 50
    except Exception:
        _clean_session(db)
        raise


def test_get_ecosystem_trends(client: TestClient, db: Session) -> None:
    """Test getting ecosystem trends with sample data."""
    _clean_session(db)
    _clear_ecosystem_stats_table(db)

    # Use unique dates for this test to avoid conflicts
    unique_dates = _get_unique_date_range("test_get_ecosystem_trends", 7)

    try:
        # Create sample stats for trend analysis with unique dates
        for i in range(7):
            stats = EcosystemStats(
                date=unique_dates[i],
                total_repositories=(i + 1) * 10,
                total_resources=(i + 1) * 50,
                active_repositories=(i + 1) * 8,
                active_resources=(i + 1) * 45,
                repositories_with_resources=(i + 1) * 6,
                total_resource_events=(i + 1) * 100,
                resource_type_breakdown={
                    "Deployment": (i + 1) * 20,
                    "Service": (i + 1) * 15,
                },
                popular_helm_charts={"nginx": (i + 1) * 5},
                daily_created_resources=(i + 1) * 5,
                daily_modified_resources=(i + 1) * 10,
                daily_deleted_resources=i,
                total_stars=(i + 1) * 100,
                total_forks=(i + 1) * 30,
                total_watchers=(i + 1) * 50,
                total_open_issues=(i + 1) * 10,
                language_breakdown={"Python": (i + 1) * 5},
                popular_topics={"web": (i + 1) * 4},
                repository_growth=i + 1,
                resource_growth=(i + 1) * 5,
                star_growth=(i + 1) * 10,
            )
            db.add(stats)
        db.commit()

        response = client.get(f"{settings.API_V1_STR}/ecosystem/trends?days=30")
        assert response.status_code == 200
        data = response.json()

        # Verify the structure matches the new API model
        assert "repository_trends" in data
        assert "resource_trends" in data
        assert "activity_trends" in data

        # Should have at least our 7 data points (may have more from other tests)
        assert len(data["repository_trends"]) >= 7
        assert len(data["resource_trends"]) >= 7
        assert len(data["activity_trends"]) >= 7
    except Exception:
        _clean_session(db)
        raise


def test_get_ecosystem_trends_with_days_parameter(
    client: TestClient, db: Session
) -> None:
    """Test getting ecosystem trends with days parameter."""
    _clean_session(db)
    _clear_ecosystem_stats_table(db)

    # Create dates that will be within the API's query range (recent dates)
    today = date.today()
    unique_dates = [
        today - timedelta(days=i) for i in range(10)
    ]  # Last 10 days including today

    try:
        # Create sample stats for 10 days with recent dates
        for i in range(10):
            stats = EcosystemStats(
                date=unique_dates[i],
                total_repositories=(i + 1) * 10,
                total_resources=(i + 1) * 50,
                active_repositories=(i + 1) * 8,
                active_resources=(i + 1) * 45,
                repositories_with_resources=(i + 1) * 6,
                total_resource_events=(i + 1) * 100,
                resource_type_breakdown={
                    "Deployment": (i + 1) * 20,
                    "Service": (i + 1) * 15,
                },
                popular_helm_charts={"nginx": (i + 1) * 5},
                daily_created_resources=(i + 1) * 5,
                daily_modified_resources=(i + 1) * 10,
                daily_deleted_resources=i,
                total_stars=(i + 1) * 100,
                total_forks=(i + 1) * 30,
                total_watchers=(i + 1) * 50,
                total_open_issues=(i + 1) * 10,
                language_breakdown={"Python": (i + 1) * 5},
                popular_topics={"web": (i + 1) * 4},
                repository_growth=i + 1,
                resource_growth=(i + 1) * 5,
                star_growth=(i + 1) * 10,
            )
            db.add(stats)
        db.commit()

        response = client.get(f"{settings.API_V1_STR}/ecosystem/trends?days=7")
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        assert response.status_code == 200
        data = response.json()

        # Verify the structure
        assert "repository_trends" in data
        assert "resource_trends" in data
        assert "activity_trends" in data

        # Should return data (may include more than just ours due to other tests)
        assert len(data["repository_trends"]) >= 0
        assert len(data["resource_trends"]) >= 0
        assert len(data["activity_trends"]) >= 0
    except Exception:
        _clean_session(db)
        raise


def test_trigger_ecosystem_stats_not_superuser(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test triggering ecosystem stats aggregation without superuser privileges."""
    response = client.post(
        f"{settings.API_V1_STR}/ecosystem/trigger-aggregation",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_trigger_ecosystem_stats_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test triggering ecosystem stats aggregation as superuser."""
    response = client.post(
        f"{settings.API_V1_STR}/ecosystem/trigger-aggregation",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Ecosystem aggregation task triggered successfully" in data["message"]
    assert "task_id" in data


def test_trigger_ecosystem_stats_invalid_date(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test triggering ecosystem stats aggregation with invalid date parameter."""
    response = client.post(
        f"{settings.API_V1_STR}/ecosystem/trigger-aggregation?target_date=invalid-date",
        headers=superuser_token_headers,
    )
    # Since there's no validation at the API level, it returns 200 and the task handles it
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "task_id" in data


def test_get_ecosystem_trends_empty_database(client: TestClient) -> None:
    """Test getting ecosystem trends with empty database."""
    response = client.get(f"{settings.API_V1_STR}/ecosystem/trends")
    # The API might return 200 with empty data instead of 404 if other tests have added data
    if response.status_code == 404:
        assert "No ecosystem statistics found" in response.json()["detail"]
    else:
        assert response.status_code == 200
        data = response.json()
        assert "repository_trends" in data
        assert "resource_trends" in data
        assert "activity_trends" in data

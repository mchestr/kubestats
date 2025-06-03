"""
Tests for ecosystem stats aggregation tasks.
"""

from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session, select

from kubestats.models import EcosystemStats, Repository
from kubestats.tasks.aggregate_ecosystem_stats import (
    aggregate_daily_ecosystem_stats,
    calculate_daily_activity,
    calculate_growth_metrics,
    calculate_repository_stats,
    calculate_resource_stats,
)


def test_calculate_repository_stats_empty_database(db: Session) -> None:
    """Test repository stats calculation with empty database."""
    stats = calculate_repository_stats(db)

    assert stats["total_repositories"] == 0
    assert stats["repositories_with_resources"] == 0
    assert stats["language_breakdown"] == {}
    assert stats["popular_topics"] == {}


def test_calculate_repository_stats_with_data(
    db: Session, sample_repository: Repository
) -> None:
    """Test repository stats calculation with sample data."""
    # Modify the sample repository to have known data
    sample_repository.language = "Python"
    sample_repository.topics = ["web", "api", "python"]
    sample_repository.created_at = datetime(2024, 1, 10, tzinfo=timezone.utc)
    sample_repository.discovered_at = datetime(2024, 1, 14, tzinfo=timezone.utc)
    db.add(sample_repository)
    db.commit()

    stats = calculate_repository_stats(db)

    assert stats["total_repositories"] == 1
    assert stats["repositories_with_resources"] == 0  # no resources yet
    assert "Python" in stats["language_breakdown"]
    assert stats["language_breakdown"]["Python"] == 1
    # Check that topics were processed (should have at least one)
    assert len(stats["popular_topics"]) >= 1


def test_calculate_resource_stats_empty_database(db: Session) -> None:
    """Test resource stats calculation with empty database."""
    stats = calculate_resource_stats(db)

    assert stats["total_resources"] == 0
    assert stats["active_resources"] == 0
    assert stats["total_resource_events"] == 0
    assert stats["popular_helm_charts"] == {}
    assert stats["resource_type_breakdown"] == {}


def test_calculate_daily_activity_empty_database(db: Session) -> None:
    """Test daily activity calculation with empty database."""
    target_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
    stats = calculate_daily_activity(db, target_date)

    assert stats["daily_created_resources"] == 0
    assert stats["daily_modified_resources"] == 0
    assert stats["daily_deleted_resources"] == 0


def test_calculate_growth_metrics_no_previous_data(db: Session) -> None:
    """Test growth metrics calculation without previous day data."""
    target_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
    current_stats = {
        "total_repositories": 10,
        "active_resources": 50,
        "total_stars": 100,
    }

    growth_stats = calculate_growth_metrics(db, current_stats, target_date)

    # Without previous data, all growth should be 0
    assert growth_stats["repository_growth"] == 0
    assert growth_stats["resource_growth"] == 0
    assert growth_stats["star_growth"] == 0


def test_calculate_growth_metrics_with_previous_data(db: Session) -> None:
    """Test growth metrics calculation with previous day data."""
    # Create previous day's stats
    previous_date = date(2024, 1, 14)
    previous_stats = EcosystemStats(
        date=previous_date,
        total_repositories=8,
        total_resources=40,
        active_repositories=6,
        active_resources=40,  # This is what the calculation uses
        repositories_with_resources=5,
        total_resource_events=50,
        resource_type_breakdown={"Deployment": 15, "Service": 12},
        popular_helm_charts={"nginx": 4, "redis": 2},
        daily_created_resources=3,
        daily_modified_resources=8,
        daily_deleted_resources=2,
        total_stars=80,
        total_forks=20,
        total_watchers=15,
        total_open_issues=5,
        language_breakdown={"Python": 4, "Go": 2},
        popular_topics={"web": 3, "api": 2},
        repository_growth=0,
        resource_growth=0,
        star_growth=0,
        calculation_duration_seconds=1.5,
    )
    db.add(previous_stats)
    db.commit()

    # Current day's stats
    target_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
    current_stats = {
        "total_repositories": 10,
        "active_resources": 50,
        "total_stars": 100,
    }

    growth_stats = calculate_growth_metrics(db, current_stats, target_date)

    # Calculate expected growth
    # Repository growth: 10 - 8 = 2
    assert growth_stats["repository_growth"] == 2
    # Resource growth: 50 - 40 = 10 (active_resources)
    assert growth_stats["resource_growth"] == 10
    # Star growth: 100 - 80 = 20
    assert growth_stats["star_growth"] == 20


@patch("kubestats.tasks.aggregate_ecosystem_stats.calculate_repository_stats")
@patch("kubestats.tasks.aggregate_ecosystem_stats.calculate_resource_stats")
@patch("kubestats.tasks.aggregate_ecosystem_stats.calculate_daily_activity")
@patch("kubestats.tasks.aggregate_ecosystem_stats.calculate_growth_metrics")
@patch("kubestats.tasks.aggregate_ecosystem_stats.calculate_metrics_aggregates")
def test_aggregate_daily_ecosystem_stats_success(
    mock_metrics: Mock,
    mock_growth: Mock,
    mock_activity: Mock,
    mock_resources: Mock,
    mock_repos: Mock,
    db: Session,
) -> None:
    """Test successful daily ecosystem stats aggregation."""
    target_date = date(2024, 1, 15)

    # Mock the individual calculation functions to return dictionaries
    mock_repos.return_value = {
        "total_repositories": 10,
        "repositories_with_resources": 6,
        "language_breakdown": {"Python": 5, "Go": 3},
        "popular_topics": {"web": 4, "api": 2},
    }

    mock_resources.return_value = {
        "total_resources": 50,
        "active_resources": 45,
        "resource_type_breakdown": {"Deployment": 20, "Service": 15},
        "popular_helm_charts": {"nginx": 5, "redis": 3},
        "total_resource_events": 100,
    }

    mock_activity.return_value = {
        "daily_created_resources": 5,
        "daily_modified_resources": 10,
        "daily_deleted_resources": 1,
    }

    mock_metrics.return_value = {
        "total_stars": 200,
        "total_forks": 50,
        "total_watchers": 30,
        "total_open_issues": 15,
    }

    mock_growth.return_value = {
        "repository_growth": 2,
        "resource_growth": 5,
        "star_growth": 10,
    }

    # Execute the task
    result = aggregate_daily_ecosystem_stats(target_date.isoformat())

    # Verify the task completed successfully
    assert result["status"] == "success"
    assert result["date"] == "2024-01-15T00:00:00+00:00"

    # Verify the stats were saved to the database
    stats = db.exec(
        select(EcosystemStats).where(EcosystemStats.date == target_date)
    ).first()

    assert stats is not None
    assert stats.total_repositories == 10
    assert stats.total_resources == 50
    assert stats.active_resources == 45
    assert stats.daily_created_resources == 5
    assert stats.repository_growth == 2


def test_aggregate_daily_ecosystem_stats_duplicate_date(db: Session) -> None:
    """Test aggregation task with duplicate date (should skip existing record)."""
    target_date = date(2024, 1, 16)  # Use different date to avoid conflicts

    # Create existing stats for the same date
    existing_stats = EcosystemStats(
        date=target_date,
        total_repositories=5,
        total_resources=25,
        active_repositories=4,
        active_resources=20,
        repositories_with_resources=3,
        total_resource_events=30,
        resource_type_breakdown={"Pod": 10},
        popular_helm_charts={"postgres": 3},
        daily_created_resources=2,
        daily_modified_resources=5,
        daily_deleted_resources=0,
        total_stars=50,
        total_forks=10,
        total_watchers=8,
        total_open_issues=3,
        language_breakdown={"Go": 3},
        popular_topics={"cli": 2},
        repository_growth=0,
        resource_growth=0,
        star_growth=0,
        calculation_duration_seconds=1.0,
    )
    db.add(existing_stats)
    db.commit()

    # Execute the task (should skip the existing record)
    result = aggregate_daily_ecosystem_stats(target_date.isoformat())

    # Verify the task was skipped
    assert result["status"] == "skipped"
    assert "Stats already exist for this date" in result["reason"]

    # Verify only one record exists for this date
    stats_count = db.exec(
        select(EcosystemStats).where(EcosystemStats.date == target_date)
    ).all()
    assert len(stats_count) == 1


def test_aggregate_daily_ecosystem_stats_invalid_date() -> None:
    """Test aggregation task with invalid date format."""
    # The task should handle invalid date formats by retrying and eventually failing
    # Since it's a Celery task, exceptions are handled by the retry mechanism
    with pytest.raises(ValueError):
        aggregate_daily_ecosystem_stats("invalid-date")


@patch("kubestats.tasks.aggregate_ecosystem_stats.calculate_repository_stats")
def test_aggregate_daily_ecosystem_stats_database_error(
    mock_repos: Mock, db: Session
) -> None:
    """Test aggregation task with database error."""
    # Mock the self object to prevent retries in tests
    with patch(
        "kubestats.tasks.aggregate_ecosystem_stats.aggregate_daily_ecosystem_stats.retry"
    ) as mock_retry:
        mock_repos.side_effect = Exception("Database connection error")
        mock_retry.side_effect = Exception(
            "Database connection error"
        )  # Make retry also raise

        # The task should handle database errors
        with pytest.raises(Exception) as exc_info:
            aggregate_daily_ecosystem_stats("2024-01-17")  # Use different date

        assert "Database connection error" in str(exc_info.value)

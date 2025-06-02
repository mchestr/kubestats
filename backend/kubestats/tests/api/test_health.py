import datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from kubestats.api.health import system_health_check


def test_system_health_check_healthy(db: Session) -> None:
    """Test system health check returns healthy status when all services are up."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_from_url.return_value = mock_redis

        # Execute
        result = system_health_check(db)

        # Assert
        assert result["status"] == "healthy"
        assert result["redis_status"] == "healthy"
        assert result["database_status"] == "healthy"
        assert "timestamp" in result

        # Verify timestamp is valid ISO format
        datetime.datetime.fromisoformat(result["timestamp"])

        # Verify mocks were called
        mock_redis_from_url.assert_called_once()
        mock_redis.ping.assert_called_once()


def test_system_health_check_redis_unhealthy(db: Session) -> None:
    """Test system health check returns unhealthy status when Redis is down."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup
        mock_redis = Mock()
        mock_redis.ping.return_value = False
        mock_redis_from_url.return_value = mock_redis

        # Execute
        result = system_health_check(db)

        # Assert
        assert result["status"] == "healthy"  # Overall status is still healthy
        assert result["redis_status"] == "unhealthy"
        assert result["database_status"] == "healthy"
        assert "timestamp" in result


def test_system_health_check_redis_exception(db: Session) -> None:
    """Test system health check handles Redis connection exceptions."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup
        mock_redis_from_url.side_effect = Exception("Redis connection failed")

        # Execute
        result = system_health_check(db)

        # Assert
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Redis connection failed" in result["error"]
        assert "timestamp" in result


def test_system_health_check_database_exception() -> None:
    """Test system health check handles database connection exceptions."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup Redis to work
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_from_url.return_value = mock_redis

        # Setup database session that raises exception
        mock_session = Mock()
        mock_session.exec.side_effect = Exception("Database connection failed")

        # Execute
        result = system_health_check(mock_session)

        # Assert
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Database connection failed" in result["error"]
        assert "timestamp" in result


def test_system_health_check_redis_ping_exception(db: Session) -> None:
    """Test system health check handles Redis ping exceptions."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Redis ping failed")
        mock_redis_from_url.return_value = mock_redis

        # Execute
        result = system_health_check(db)

        # Assert
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Redis ping failed" in result["error"]
        assert "timestamp" in result


def test_health_endpoint_returns_200(client: TestClient) -> None:
    """Test health endpoint returns 200 status code."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_from_url.return_value = mock_redis

        # Execute
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["redis_status"] == "healthy"
        assert data["database_status"] == "healthy"


def test_health_endpoint_returns_unhealthy_status(client: TestClient) -> None:
    """Test health endpoint returns unhealthy status when services fail."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup
        mock_redis_from_url.side_effect = Exception("Service unavailable")

        # Execute
        response = client.get("/health")

        # Assert
        assert response.status_code == 200  # HTTP status is still 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
        assert "Service unavailable" in data["error"]


def test_health_endpoint_response_format(client: TestClient) -> None:
    """Test health endpoint returns expected response format."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_from_url.return_value = mock_redis

        # Execute
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = ["timestamp", "status"]
        for field in required_fields:
            assert field in data

        # When healthy, should have service-specific status fields
        if data["status"] == "healthy":
            assert "redis_status" in data
            assert "database_status" in data

        # Timestamp should be valid ISO format
        datetime.datetime.fromisoformat(data["timestamp"])


def test_health_check_timestamp_format(db: Session) -> None:
    """Test that health check timestamp is in correct ISO format."""
    with patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url:
        # Setup
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_from_url.return_value = mock_redis

        # Execute
        result = system_health_check(db)

        # Assert
        timestamp_str = result["timestamp"]

        # Should be able to parse as ISO format
        parsed_timestamp = datetime.datetime.fromisoformat(timestamp_str)

        # Should be recent (within last minute)
        now = datetime.datetime.now(datetime.UTC)
        time_diff = abs((now - parsed_timestamp).total_seconds())
        assert time_diff < 60  # Less than 1 minute difference


def test_health_check_uses_settings_redis_url(db: Session) -> None:
    """Test that health check uses Redis URL from settings."""
    with (
        patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url,
        patch("kubestats.api.health.settings") as mock_settings,
    ):
        # Setup
        mock_settings.REDIS_URL = "redis://test:6379/0"
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_from_url.return_value = mock_redis

        # Execute
        system_health_check(db)

        # Assert
        mock_redis_from_url.assert_called_once_with("redis://test:6379/0")


def test_health_check_logs_error_on_failure(db: Session) -> None:
    """Test that health check logs errors when services fail."""
    with (
        patch("kubestats.api.health.redis.Redis.from_url") as mock_redis_from_url,
        patch("kubestats.api.health.logger") as mock_logger,
    ):
        # Setup
        error_message = "Redis connection timeout"
        mock_redis_from_url.side_effect = Exception(error_message)

        # Execute
        result = system_health_check(db)

        # Assert
        assert result["status"] == "unhealthy"
        mock_logger.error.assert_called_once()

        # Verify the logged message contains the error
        logged_message = mock_logger.error.call_args[0][0]
        assert "System health check failed" in logged_message
        assert error_message in logged_message

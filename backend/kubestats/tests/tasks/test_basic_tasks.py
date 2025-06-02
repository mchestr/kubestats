from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch

from kubestats.tasks.basic_tasks import (
    system_health_check,
)


@patch("redis.Redis.from_url")
@patch("psutil.cpu_percent")
@patch("psutil.virtual_memory")
@patch("kubestats.tasks.basic_tasks.datetime")
def test_system_health_check_success(
    mock_datetime: Any, mock_memory: Any, mock_cpu: Any, mock_redis: Any
) -> None:
    """Test successful system health check."""
    # Mock datetime
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.utcnow.return_value = timestamp

    # Mock dependencies
    mock_redis_instance = Mock()
    mock_redis_instance.ping.return_value = True
    mock_redis.return_value = mock_redis_instance

    mock_cpu.return_value = 25.5

    mock_memory_obj = Mock()
    mock_memory_obj.percent = 65.2
    mock_memory.return_value = mock_memory_obj

    # Execute task
    result = system_health_check.run()

    # Assertions
    assert result["status"] == "healthy"
    assert result["redis_status"] == "healthy"
    assert result["cpu_percent"] == 25.5
    assert result["memory_percent"] == 65.2
    assert "timestamp" in result


@patch("redis.Redis.from_url")
@patch("kubestats.tasks.basic_tasks.datetime")
def test_system_health_check_redis_failure(mock_datetime: Any, mock_redis: Any) -> None:
    """Test system health check with Redis failure."""
    # Mock datetime
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.utcnow.return_value = timestamp

    # Mock Redis connection failure
    mock_redis.side_effect = Exception("Redis connection failed")

    result = system_health_check.run()

    assert result["status"] == "unhealthy"
    assert "Redis connection failed" in result["error"]
    assert "timestamp" in result


@patch("redis.Redis.from_url")
@patch("psutil.cpu_percent")
@patch("kubestats.tasks.basic_tasks.datetime")
def test_system_health_check_psutil_failure(
    mock_datetime: Any, mock_cpu: Any, mock_redis: Any
) -> None:
    """Test system health check with psutil failure."""
    # Mock datetime
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.utcnow.return_value = timestamp

    # Mock Redis to be successful
    mock_redis_instance = Mock()
    mock_redis_instance.ping.return_value = True
    mock_redis.return_value = mock_redis_instance

    mock_cpu.side_effect = Exception("CPU monitoring failed")

    result = system_health_check.run()

    assert result["status"] == "unhealthy"
    assert "CPU monitoring failed" in result["error"]

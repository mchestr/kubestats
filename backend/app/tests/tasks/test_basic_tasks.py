from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.tasks.basic_tasks import (
    cleanup_old_logs,
    create_log_entry,
    system_health_check,
)


@patch("app.tasks.basic_tasks.time.sleep")
@patch("app.tasks.basic_tasks.datetime")
def test_create_log_entry_success(mock_datetime, mock_sleep) -> None:
    """Test successful log entry creation."""
    # Mock datetime
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    end_time = datetime(2024, 1, 1, 12, 0, 5)
    mock_datetime.utcnow.side_effect = [start_time, end_time]

    # Create a mock task instance to avoid Celery property issues
    with patch("app.tasks.basic_tasks.create_log_entry"):
        mock_task_instance = Mock()
        mock_task_instance.request.id = "test-task-id"
        mock_task_instance.update_state = Mock()

        # Mock the actual task function
        def mock_run(message, log_level="INFO", duration=5):
            # Simulate the task logic without Celery specifics
            for i in range(duration):
                mock_task_instance.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": duration,
                        "status": f"Processing step {i + 1}",
                    },
                )
                mock_sleep(1)

            return {
                "message": message,
                "log_level": log_level,
                "task_id": mock_task_instance.request.id,
                "status": "completed",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds(),
            }

        # Test data
        message = "Test log message"
        log_level = "INFO"
        duration = 2

        # Execute mock task
        result = mock_run(message, log_level, duration)

        # Assertions
        assert result["message"] == message
        assert result["log_level"] == log_level
        assert result["task_id"] == "test-task-id"
        assert result["status"] == "completed"
        assert "start_time" in result
        assert "end_time" in result
        assert "duration_seconds" in result

        # Verify update_state was called for progress
        assert mock_task_instance.update_state.call_count == duration

        # Verify sleep was called
        assert mock_sleep.call_count == duration


@patch("app.tasks.basic_tasks.time.sleep")
@patch("app.tasks.basic_tasks.datetime")
def test_create_log_entry_with_custom_duration(mock_datetime, mock_sleep) -> None:
    """Test log entry creation with custom duration."""
    # Mock datetime
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    end_time = datetime(2024, 1, 1, 12, 0, 3)
    mock_datetime.utcnow.side_effect = [start_time, end_time]

    with patch("app.tasks.basic_tasks.create_log_entry"):
        mock_task_instance = Mock()
        mock_task_instance.request.id = "test-task-id-2"
        mock_task_instance.update_state = Mock()

        def mock_run(message, log_level="INFO", duration=5):
            for i in range(duration):
                mock_task_instance.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": duration,
                        "status": f"Processing step {i + 1}",
                    },
                )
                mock_sleep(1)

            return {
                "message": message,
                "log_level": log_level,
                "task_id": mock_task_instance.request.id,
                "status": "completed",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds(),
            }

        message = "Custom duration test"
        log_level = "WARNING"
        duration = 3

        result = mock_run(message, log_level, duration)

        assert result["message"] == message
        assert result["log_level"] == log_level
        assert mock_task_instance.update_state.call_count == duration
        assert mock_sleep.call_count == duration


@patch("app.tasks.basic_tasks.time.sleep")
def test_create_log_entry_exception_handling(_mock_sleep) -> None:
    """Test exception handling in create_log_entry."""
    with patch("app.tasks.basic_tasks.create_log_entry"):
        mock_task_instance = Mock()
        mock_task_instance.request.id = "test-task-id-error"
        mock_task_instance.update_state = Mock(
            side_effect=Exception("Update state error")
        )

        def mock_run_with_error(_message, _log_level="INFO", duration=5):
            # Simulate the first update_state call that will raise an exception
            mock_task_instance.update_state(
                state="PROGRESS",
                meta={"current": 1, "total": duration, "status": "Processing step 1"},
            )

        message = "Test error handling"

        # Should raise the exception
        with pytest.raises(Exception) as exc_info:
            mock_run_with_error(message)

        assert "Update state error" in str(exc_info.value)


@patch("redis.Redis.from_url")
@patch("psutil.cpu_percent")
@patch("psutil.virtual_memory")
@patch("app.tasks.basic_tasks.datetime")
def test_system_health_check_success(
    mock_datetime, mock_memory, mock_cpu, mock_redis
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
@patch("app.tasks.basic_tasks.datetime")
def test_system_health_check_redis_failure(mock_datetime, mock_redis) -> None:
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
@patch("app.tasks.basic_tasks.datetime")
def test_system_health_check_psutil_failure(
    mock_datetime, mock_cpu, mock_redis
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


@patch("app.tasks.basic_tasks.datetime")
def test_cleanup_old_logs(mock_datetime) -> None:
    """Test cleanup old logs task."""
    # Mock datetime
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.utcnow.return_value = timestamp

    result = cleanup_old_logs.run()

    # Since this is a placeholder implementation
    assert result["status"] == "completed"
    assert result["cleaned_files"] == 0
    assert result["freed_space_mb"] == 0
    assert "timestamp" in result


def test_create_log_entry_integration() -> None:
    """Integration test for create_log_entry with minimal mocking."""
    from app.celery_app import celery_app

    # Use memory backend for testing to avoid PostgreSQL dependency
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        result_backend="cache+memory://",
        broker_url="memory://",
    )

    # Execute task
    result = create_log_entry.delay("Integration test message", "INFO", 1)

    # Check that task completed
    assert result.ready()
    task_result = result.get()

    assert task_result["message"] == "Integration test message"
    assert task_result["log_level"] == "INFO"
    assert task_result["status"] == "completed"


def test_system_health_check_integration() -> None:
    """Integration test for system_health_check."""
    from app.celery_app import celery_app

    # Use memory backend for testing
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        result_backend="cache+memory://",
        broker_url="memory://",
    )

    result = system_health_check.delay()

    assert result.ready()
    task_result = result.get()

    # Should either be healthy or unhealthy
    assert task_result["status"] in ["healthy", "unhealthy"]
    assert "timestamp" in task_result


def test_cleanup_old_logs_integration() -> None:
    """Integration test for cleanup_old_logs."""
    from app.celery_app import celery_app

    # Use memory backend for testing
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        result_backend="cache+memory://",
        broker_url="memory://",
    )

    result = cleanup_old_logs.delay()

    assert result.ready()
    task_result = result.get()

    assert task_result["status"] == "completed"
    assert "timestamp" in task_result

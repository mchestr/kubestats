from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.core.config import settings


@patch('app.api.routes.tasks.create_log_entry.delay')
def test_trigger_log_task_success(
    mock_task_delay, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test successful task triggering."""
    # Mock the task result
    mock_result = Mock()
    mock_result.id = "test-task-id-123"
    mock_task_delay.return_value = mock_result

    # Test data
    task_data = {
        "message": "Test log message",
        "log_level": "INFO",
        "duration": 5
    }

    # Make request
    response = client.post(
        f"{settings.API_V1_STR}/tasks/trigger",
        headers=superuser_token_headers,
        json=task_data,
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "test-task-id-123"
    assert data["status"] == "PENDING"
    assert "Test log message" in data["message"]

    # Verify task was called with correct parameters
    mock_task_delay.assert_called_once_with(
        message="Test log message",
        log_level="INFO",
        duration=5
    )


@patch('app.api.routes.tasks.system_health_check.delay')
def test_trigger_health_check_success(
    mock_task_delay, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test successful health check triggering."""
    # Mock the task result
    mock_result = Mock()
    mock_result.id = "health-check-task-456"
    mock_task_delay.return_value = mock_result

    # Make request
    response = client.post(
        f"{settings.API_V1_STR}/tasks/health-check",
        headers=superuser_token_headers,
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "health-check-task-456"
    assert data["status"] == "PENDING"
    assert "Health check" in data["message"]

    # Verify task was called
    mock_task_delay.assert_called_once()


def test_trigger_task_unauthorized(client: TestClient) -> None:
    """Test task triggering without proper authorization."""
    task_data = {
        "message": "Unauthorized test",
        "log_level": "INFO",
        "duration": 3
    }

    # Make request without authentication
    response = client.post(f"{settings.API_V1_STR}/tasks/trigger", json=task_data)

    # Should be unauthorized
    assert response.status_code == 401


@patch('app.api.routes.tasks.celery_app.AsyncResult')
def test_get_task_status_success(
    mock_async_result, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test successful task status retrieval."""
    # Mock the AsyncResult
    mock_result = Mock()
    mock_result.status = "SUCCESS"
    mock_result.result = {"message": "Task completed"}
    mock_result.traceback = None
    mock_result.date_done = None
    mock_result.name = "app.tasks.basic_tasks.create_log_entry"
    mock_result.worker = "worker-1"
    mock_result.retries = 0
    mock_async_result.return_value = mock_result

    # Make request
    task_id = "test-task-123"
    response = client.get(
        f"{settings.API_V1_STR}/tasks/status/{task_id}",
        headers=superuser_token_headers,
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "SUCCESS"
    assert data["result"] == {"message": "Task completed"}

    # Verify AsyncResult was called with correct task_id
    mock_async_result.assert_called_once_with(task_id)


@patch('app.api.routes.tasks.get_task_status_from_db')
def test_list_tasks_success(
    mock_get_tasks, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test successful task listing."""
    # Mock task data
    mock_tasks = [
        {
            "task_id": "task-1",
            "status": "SUCCESS",
            "result": {"message": "Task 1 completed"},
            "traceback": None,
            "date_done": "2024-01-01T00:00:00",
            "name": "app.tasks.basic_tasks.create_log_entry",
            "worker": "worker-1",
            "retries": 0
        },
        {
            "task_id": "task-2",
            "status": "PENDING",
            "result": None,
            "traceback": None,
            "date_done": None,
            "name": "app.tasks.basic_tasks.system_health_check",
            "worker": None,
            "retries": 0
        }
    ]
    mock_get_tasks.return_value = mock_tasks

    # Make request
    response = client.get(
        f"{settings.API_V1_STR}/tasks/list",
        headers=superuser_token_headers,
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["task_id"] == "task-1"
    assert data[0]["status"] == "SUCCESS"
    assert data[1]["task_id"] == "task-2"
    assert data[1]["status"] == "PENDING"


@patch('app.api.routes.tasks.celery_app.control.inspect')
def test_get_worker_status_success(
    mock_inspect, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test successful worker status retrieval."""
    # Mock inspect result
    mock_i = Mock()
    mock_i.active.return_value = {"worker1": []}
    mock_i.scheduled.return_value = {"worker1": []}
    mock_i.reserved.return_value = {"worker1": []}
    mock_i.stats.return_value = {"worker1": {"total": 10}}
    mock_inspect.return_value = mock_i

    # Make request
    response = client.get(
        f"{settings.API_V1_STR}/tasks/workers",
        headers=superuser_token_headers,
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "active" in data
    assert "scheduled" in data
    assert "reserved" in data
    assert "stats" in data
    assert data["active"] == {"worker1": []}
    assert data["stats"] == {"worker1": {"total": 10}}


def test_task_routes_require_superuser(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test that all task routes require superuser permissions."""
    # Test various endpoints without proper superuser auth
    endpoints = [
        ("POST", f"{settings.API_V1_STR}/tasks/trigger", {"message": "test"}),
        ("POST", f"{settings.API_V1_STR}/tasks/health-check", {}),
        ("GET", f"{settings.API_V1_STR}/tasks/status/test-id", {}),
        ("GET", f"{settings.API_V1_STR}/tasks/list", {}),
        ("GET", f"{settings.API_V1_STR}/tasks/workers", {}),
    ]

    for method, endpoint, data in endpoints:
        if method == "POST":
            response = client.post(endpoint, headers=normal_user_token_headers, json=data)
        else:
            response = client.get(endpoint, headers=normal_user_token_headers)

        # Should be unauthorized (401) or forbidden (403)
        assert response.status_code in [401, 403]


@patch('app.api.routes.tasks.create_log_entry.delay')
def test_trigger_task_validation_error(
    mock_task_delay, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test task triggering with invalid data."""
    # Test with invalid data (missing required field)
    invalid_data = {
        "log_level": "INFO",
        "duration": 5
        # missing "message" field
    }

    response = client.post(
        f"{settings.API_V1_STR}/tasks/trigger",
        headers=superuser_token_headers,
        json=invalid_data,
    )

    # Should return validation error
    assert response.status_code == 422

    # Task should not be called
    mock_task_delay.assert_not_called()


@patch('app.api.routes.tasks.create_log_entry.delay')
def test_trigger_task_celery_error(
    mock_task_delay, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test task triggering when Celery raises an error."""
    # Mock Celery error
    mock_task_delay.side_effect = Exception("Celery connection failed")

    task_data = {
        "message": "Test message",
        "log_level": "INFO",
        "duration": 3
    }

    response = client.post(
        f"{settings.API_V1_STR}/tasks/trigger",
        headers=superuser_token_headers,
        json=task_data,
    )

    # Should return server error
    assert response.status_code == 500
    data = response.json()
    assert "Failed to trigger task" in data["detail"]


def test_task_trigger_request_validation() -> None:
    """Test TaskTriggerRequest model validation."""
    from app.api.routes.tasks import TaskTriggerRequest

    # Valid request
    valid_request = TaskTriggerRequest(
        message="Test message",
        log_level="INFO",
        duration=5
    )
    assert valid_request.message == "Test message"
    assert valid_request.log_level == "INFO"
    assert valid_request.duration == 5

    # Test default values
    minimal_request = TaskTriggerRequest(message="Test")
    assert minimal_request.log_level == "INFO"
    assert minimal_request.duration == 5

    # Test with different log levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        request = TaskTriggerRequest(message="Test", log_level=level)
        assert request.log_level == level


def test_task_response_model() -> None:
    """Test TaskResponse model."""
    from app.api.routes.tasks import TaskResponse

    response = TaskResponse(
        task_id="test-123",
        status="PENDING",
        message="Task started"
    )

    assert response.task_id == "test-123"
    assert response.status == "PENDING"
    assert response.message == "Task started"


def test_task_status_response_model() -> None:
    """Test TaskStatusResponse model."""
    from app.api.routes.tasks import TaskStatusResponse

    # With all fields
    response = TaskStatusResponse(
        task_id="test-456",
        status="SUCCESS",
        result={"key": "value"},
        traceback=None,
        date_done="2024-01-01T00:00:00",
        name="task.name",
        worker="worker-1",
        retries=2
    )

    assert response.task_id == "test-456"
    assert response.status == "SUCCESS"
    assert response.result == {"key": "value"}

    # With minimal fields
    minimal_response = TaskStatusResponse(
        task_id="test-789",
        status="PENDING"
    )

    assert minimal_response.task_id == "test-789"
    assert minimal_response.status == "PENDING"
    assert minimal_response.result is None

@patch('app.api.routes.tasks.celery_app.AsyncResult')
def test_get_task_status_with_exception_result(
    mock_async_result, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test task status retrieval when result contains an exception (tests the PydanticSerializationError fix)."""
    # Mock the AsyncResult with an exception as the result
    mock_result = Mock()
    mock_result.status = "FAILURE"
    mock_result.result = AttributeError("'NoneType' object has no attribute 'foo'")
    mock_result.traceback = "Traceback (most recent call last):\n  File \"test.py\", line 1, in <module>\n    foo.bar\nAttributeError: 'NoneType' object has no attribute 'foo'"
    mock_result.date_done = None
    mock_result.name = "app.tasks.basic_tasks.create_log_entry"
    mock_result.worker = "worker-1"
    mock_result.retries = 1
    mock_async_result.return_value = mock_result

    # Make request
    task_id = "failed-task-123"
    response = client.get(
        f"{settings.API_V1_STR}/tasks/status/{task_id}",
        headers=superuser_token_headers,
    )

    # Assertions - should succeed and serialize the exception as a string
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "FAILURE"
    # The exception should be serialized as a string in the format "ExceptionType: message"
    assert data["result"] == "AttributeError: 'NoneType' object has no attribute 'foo'"
    assert "Traceback" in data["traceback"]

    # Verify AsyncResult was called with correct task_id
    mock_async_result.assert_called_once_with(task_id)

def test_task_status_response_exception_serialization() -> None:
    """Test that TaskStatusResponse properly serializes exceptions in the result field."""
    import json

    from app.api.routes.tasks import TaskStatusResponse

    # Create a response with an exception as the result
    exception = ValueError("Invalid input data")
    response = TaskStatusResponse(
        task_id="exception-test",
        status="FAILURE",
        result=exception
    )

    # Should be able to serialize to JSON without error
    json_data = response.model_dump_json()
    parsed = json.loads(json_data)

    # The exception should be converted to a string
    assert parsed["result"] == "ValueError: Invalid input data"
    assert parsed["task_id"] == "exception-test"
    assert parsed["status"] == "FAILURE"

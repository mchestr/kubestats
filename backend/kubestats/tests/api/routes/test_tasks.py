from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from typing import Any

from fastapi.testclient import TestClient

from kubestats.api.routes.tasks import ensure_utc_isoformat, router


def test_ensure_utc_isoformat_naive() -> None:
    dt: datetime = datetime(2024, 6, 5, 12, 34, 56, 789000)
    result: str | None = ensure_utc_isoformat(dt)
    if result is not None:
        assert result.endswith("+00:00")
        assert result.startswith("2024-06-05T12:34:56.789000")


def test_ensure_utc_isoformat_aware() -> None:
    dt: datetime = datetime(2024, 6, 5, 12, 34, 56, 789000, tzinfo=timezone.utc)
    result: str | None = ensure_utc_isoformat(dt)
    if result is not None:
        assert result.endswith("+00:00")
        assert result.startswith("2024-06-05T12:34:56.789000")


def test_ensure_utc_isoformat_none() -> None:
    assert ensure_utc_isoformat(None) is None


# Example test for the /tasks/ endpoint (requires test client and DB fixture)
client: TestClient = TestClient(router)


def test_list_tasks_date_done_utc(monkeypatch) -> None:
    # Patch DB session and CeleryTaskMeta
    class FakeTask:
        task_id: str = "abc123"
        status: str = "SUCCESS"
        result: str = "ok"
        date_done: datetime = datetime(2024, 6, 5, 12, 34, 56, 789000)  # naive
        traceback: str | None = None
        name: str = "mytask"
        args: str = "{}"
        kwargs: str = "{}"
        worker: str = "worker1"
        retries: int = 0

    fake_results = [FakeTask()]
    fake_session = MagicMock()
    fake_session.exec.return_value = fake_results
    with patch("kubestats.api.routes.tasks.get_db", return_value=fake_session):
        with TestClient(router) as test_client:
            response = test_client.get("/tasks/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert "date_done" in data[0]
            assert data[0]["date_done"].endswith("+00:00")


def test_trigger_periodic_task_success(monkeypatch) -> None:
    fake_user: MagicMock = MagicMock()
    fake_user.id = 1
    fake_result: MagicMock = MagicMock()
    fake_result.id = "taskid123"
    fake_send_task: MagicMock = MagicMock(return_value=fake_result)
    fake_beat_schedule: dict[str, dict[str, Any]] = {
        "mytask": {"task": "mytask", "args": [1], "kwargs": {"foo": "bar"}}
    }
    with (
        patch(
            "kubestats.api.routes.tasks.get_current_active_superuser",
            return_value=fake_user,
        ),
        patch("kubestats.api.routes.tasks.celery_app.send_task", fake_send_task),
        patch(
            "kubestats.api.routes.tasks.celery_app.conf.beat_schedule",
            fake_beat_schedule,
        ),
    ):
        with TestClient(router) as test_client:
            response = test_client.post("/trigger-periodic/mytask")
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "taskid123"
            assert data["status"] == "PENDING"
            assert "triggered successfully" in data["message"]


def test_trigger_periodic_task_not_found(monkeypatch) -> None:
    fake_user: MagicMock = MagicMock()
    fake_user.id = 1
    fake_beat_schedule: dict[str, dict[str, Any]] = {}
    with (
        patch(
            "kubestats.api.routes.tasks.get_current_active_superuser",
            return_value=fake_user,
        ),
        patch(
            "kubestats.api.routes.tasks.celery_app.conf.beat_schedule",
            fake_beat_schedule,
        ),
    ):
        with TestClient(router) as test_client:
            response = test_client.post("/trigger-periodic/unknown")
            assert response.status_code == 404
            assert "not found" in response.text


def test_get_task_status_success(monkeypatch) -> None:
    class FakeAsyncResult:
        status: str = "SUCCESS"
        result: str = "ok"
        traceback: str | None = None
        date_done: datetime = datetime(2024, 6, 5, 12, 34, 56, 789000)
        name: str = "mytask"
        worker: str = "worker1"
        retries: int = 0

    with patch(
        "kubestats.api.routes.tasks.celery_app.AsyncResult",
        return_value=FakeAsyncResult(),
    ):
        with TestClient(router) as test_client:
            response = test_client.get("/status/abc123")
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "abc123"
            assert data["status"] == "SUCCESS"
            assert data["date_done"].endswith("+00:00")


def test_get_task_status_error(monkeypatch) -> None:
    def raise_error(task_id: str) -> None:
        raise Exception("fail")

    with patch(
        "kubestats.api.routes.tasks.celery_app.AsyncResult", side_effect=raise_error
    ):
        with TestClient(router) as test_client:
            response = test_client.get("/status/abc123")
            assert response.status_code == 500
            assert "Failed to get task status" in response.text


def test_get_worker_status_success(monkeypatch) -> None:
    fake_inspector: MagicMock = MagicMock()
    fake_inspector.active.return_value = {"worker1": []}
    fake_inspector.scheduled.return_value = {"worker1": []}
    fake_inspector.reserved.return_value = {"worker1": []}
    fake_inspector.stats.return_value = {"worker1": {"total": {"mytask": 2}}}
    fake_beat_schedule: dict[str, dict[str, Any]] = {
        "periodic1": {
            "task": "mytask",
            "schedule": "every 5m",
            "enabled": True,
            "args": [],
            "kwargs": {},
        }
    }
    with (
        patch(
            "kubestats.api.routes.tasks.celery_app.control.inspect",
            return_value=fake_inspector,
        ),
        patch(
            "kubestats.api.routes.tasks.celery_app.conf.beat_schedule",
            fake_beat_schedule,
        ),
    ):
        with TestClient(router) as test_client:
            response = test_client.get("/workers")
            assert response.status_code == 200
            data = response.json()
            assert "active" in data
            assert "periodic_tasks" in data
            assert data["periodic_tasks"][0]["name"] == "periodic1"
            assert data["periodic_tasks"][0]["total_run_count"] == 2


def test_get_worker_status_error(monkeypatch) -> None:
    def raise_error() -> None:
        raise Exception("fail")

    with patch(
        "kubestats.api.routes.tasks.celery_app.control.inspect", side_effect=raise_error
    ):
        with TestClient(router) as test_client:
            response = test_client.get("/workers")
            assert response.status_code == 500
            assert "Failed to get worker status" in response.text

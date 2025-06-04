from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from kubestats.api.deps import get_current_active_superuser
from kubestats.api.routes.tasks import ensure_utc_isoformat
from kubestats.main import app


def override_get_current_active_superuser() -> MagicMock:
    fake_user = MagicMock()
    fake_user.id = 1
    return fake_user


def test_ensure_utc_isoformat_naive() -> None:
    dt: datetime = datetime(2024, 6, 5, 12, 34, 56, 789000)
    result: str | None = ensure_utc_isoformat(dt)
    if result is not None:
        assert result.endswith("+00:00") or result.endswith("Z")
        assert result.startswith("2024-06-05T12:34:56.789000")


def test_ensure_utc_isoformat_aware() -> None:
    dt: datetime = datetime(2024, 6, 5, 12, 34, 56, 789000, tzinfo=timezone.utc)
    result: str | None = ensure_utc_isoformat(dt)
    if result is not None:
        assert result.endswith("+00:00") or result.endswith("Z")
        assert result.startswith("2024-06-05T12:34:56.789000")


def test_ensure_utc_isoformat_none() -> None:
    assert ensure_utc_isoformat(None) is None


# Example test for the /tasks/ endpoint (requires test client and DB fixture)
client: TestClient = TestClient(app)


def test_list_tasks_date_done_utc(monkeypatch: MonkeyPatch) -> None:
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

    fake_results = MagicMock(all=lambda: [FakeTask()])
    fake_session = MagicMock()
    fake_session.exec.return_value = fake_results

    app.dependency_overrides[get_current_active_superuser] = (
        override_get_current_active_superuser
    )
    with (
        patch("kubestats.api.routes.tasks.get_db", return_value=fake_session),
        patch("sqlmodel.orm.session.Session.exec", return_value=fake_results),
    ):
        headers = {"Authorization": "Bearer testtoken"}
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/tasks/tasks/", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert "date_done" in data[0]
            assert isinstance(data[0]["date_done"], str)
            assert data[0]["date_done"].endswith("+00:00") or data[0][
                "date_done"
            ].endswith("Z")
    app.dependency_overrides = {}


def test_trigger_periodic_task_success(monkeypatch: MonkeyPatch) -> None:
    fake_result: MagicMock = MagicMock()
    fake_result.id = "taskid123"
    fake_send_task: MagicMock = MagicMock(return_value=fake_result)
    fake_beat_schedule: dict[str, dict[str, Any]] = {
        "mytask": {"task": "mytask", "args": [1], "kwargs": {"foo": "bar"}}
    }

    app.dependency_overrides[get_current_active_superuser] = (
        override_get_current_active_superuser
    )
    with (
        patch("kubestats.api.routes.tasks.celery_app.send_task", fake_send_task),
        patch.dict(
            "kubestats.api.routes.tasks.celery_app.conf.__dict__",
            {"beat_schedule": fake_beat_schedule},
            clear=False,
        ),
    ):
        headers = {"Authorization": "Bearer testtoken"}
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/v1/tasks/trigger-periodic/mytask", headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "taskid123"
            assert data["status"] == "PENDING"
            assert "triggered successfully" in data["message"]
    app.dependency_overrides = {}


def test_trigger_periodic_task_not_found(monkeypatch: MonkeyPatch) -> None:
    fake_beat_schedule: dict[str, dict[str, Any]] = {}

    app.dependency_overrides[get_current_active_superuser] = (
        override_get_current_active_superuser
    )
    with (
        patch.dict(
            "kubestats.api.routes.tasks.celery_app.conf.__dict__",
            {"beat_schedule": fake_beat_schedule},
            clear=False,
        ),
    ):
        headers = {"Authorization": "Bearer testtoken"}
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/v1/tasks/trigger-periodic/unknown", headers=headers
            )
            assert response.status_code == 404
            assert "not found" in response.text
    app.dependency_overrides = {}


def test_get_task_status_success(monkeypatch: MonkeyPatch) -> None:
    class FakeAsyncResult:
        status: str = "SUCCESS"
        result: str = "ok"
        traceback: str | None = None
        date_done: datetime = datetime(2024, 6, 5, 12, 34, 56, 789000)
        name: str = "mytask"
        worker: str = "worker1"
        retries: int = 0

    app.dependency_overrides[get_current_active_superuser] = (
        override_get_current_active_superuser
    )
    with patch(
        "kubestats.api.routes.tasks.celery_app.AsyncResult",
        return_value=FakeAsyncResult(),
    ):
        headers = {"Authorization": "Bearer testtoken"}
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/tasks/status/abc123", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "abc123"
            assert data["status"] == "SUCCESS"
            assert data["date_done"].endswith("+00:00") or data["date_done"].endswith(
                "Z"
            )
    app.dependency_overrides = {}


def test_get_task_status_error(monkeypatch: MonkeyPatch) -> None:
    def raise_error(task_id: str) -> None:
        raise Exception("fail")

    app.dependency_overrides[get_current_active_superuser] = (
        override_get_current_active_superuser
    )
    with patch(
        "kubestats.api.routes.tasks.celery_app.AsyncResult", side_effect=raise_error
    ):
        headers = {"Authorization": "Bearer testtoken"}
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/tasks/status/abc123", headers=headers)
            assert response.status_code == 500
            assert "Failed to get task status" in response.text
    app.dependency_overrides = {}


def test_get_worker_status_success(monkeypatch: MonkeyPatch) -> None:
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

    app.dependency_overrides[get_current_active_superuser] = (
        override_get_current_active_superuser
    )
    with (
        patch(
            "kubestats.api.routes.tasks.celery_app.control.inspect",
            return_value=fake_inspector,
        ),
        patch.dict(
            "kubestats.api.routes.tasks.celery_app.conf.__dict__",
            {"beat_schedule": fake_beat_schedule},
            clear=False,
        ),
    ):
        headers = {"Authorization": "Bearer testtoken"}
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/tasks/workers", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "active" in data
            assert "periodic_tasks" in data
            assert data["periodic_tasks"][0]["name"] == "periodic1"
            assert data["periodic_tasks"][0]["total_run_count"] == 2
    app.dependency_overrides = {}


def test_get_worker_status_error(monkeypatch: MonkeyPatch) -> None:
    def raise_error() -> None:
        raise Exception("fail")

    app.dependency_overrides[get_current_active_superuser] = (
        override_get_current_active_superuser
    )
    with patch(
        "kubestats.api.routes.tasks.celery_app.control.inspect", side_effect=raise_error
    ):
        headers = {"Authorization": "Bearer testtoken"}
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/tasks/workers", headers=headers)
            assert response.status_code == 500
            assert "Failed to get worker status" in response.text
    app.dependency_overrides = {}

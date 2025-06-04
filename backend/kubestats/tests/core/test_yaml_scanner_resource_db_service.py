import uuid
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from kubestats.core.yaml_scanner.models import ChangeSet, ResourceData
from kubestats.core.yaml_scanner.resource_db_service import (
    KubernetesResource,
    ResourceDatabaseService,
)
from kubestats.models import utc_now


class DummyResource:
    def __init__(
        self, key: str, file_hash: str = "h", status: str = "ACTIVE", **kwargs: Any
    ) -> None:
        self._key = key
        self.file_hash = file_hash
        self.status = status
        self.api_version = kwargs.get("api_version", "v1")
        self.kind = kwargs.get("kind", "Pod")
        self.name = kwargs.get("name", "foo")
        self.namespace = kwargs.get("namespace", "default")
        self.file_path = kwargs.get("file_path", "foo.yaml")
        self.version = kwargs.get("version", None)
        self.data = kwargs.get("data", {})
        self.id = kwargs.get("id", uuid.uuid4())
        self.repository_id = kwargs.get("repository_id", uuid.uuid4())
        self.deleted_at = None
        self.updated_at = utc_now()

    def resource_key(self) -> str:
        return self._key


@pytest.fixture
def service() -> ResourceDatabaseService:
    return ResourceDatabaseService()


@pytest.fixture
def session() -> MagicMock:
    return MagicMock()


def make_resource_data(key: str, file_hash: str = "h", **kwargs: Any) -> ResourceData:
    rd = ResourceData(
        api_version=kwargs.get("api_version", "v1"),
        kind=kwargs.get("kind", "Pod"),
        file_path=kwargs.get("file_path", "foo.yaml"),
        file_hash=file_hash,
        name=kwargs.get("name", "foo"),
        namespace=kwargs.get("namespace", "default"),
        version=kwargs.get("version", None),
        data=kwargs.get("data", {}),
    )
    rd.resource_key = lambda: key  # type: ignore
    return rd


def test_get_existing_resources(
    service: ResourceDatabaseService, session: MagicMock
) -> None:
    r1 = cast(KubernetesResource, DummyResource("k1"))
    r2 = cast(KubernetesResource, DummyResource("k2"))
    session.exec.return_value.all.return_value = [r1, r2]
    result = service.get_existing_resources(session, uuid.uuid4())
    assert result["k1"] == r1
    assert result["k2"] == r2


def test_get_deleted_resource(
    service: ResourceDatabaseService, session: MagicMock
) -> None:
    rd = make_resource_data(
        "k1", api_version="v1", kind="Pod", name="foo", namespace="default"
    )
    dummy = cast(KubernetesResource, DummyResource(
        "k1",
        status="DELETED",
        api_version="v1",
        kind="Pod",
        name="foo",
        namespace="default",
    ))
    session.exec.return_value.first.return_value = dummy
    result = service.get_deleted_resource(session, uuid.uuid4(), rd)
    assert result == dummy


def test_compare_resources_create_modify_delete(
    service: ResourceDatabaseService, session: MagicMock
) -> None:
    # One existing, one scanned (modified), one new, one deleted
    existing: dict[str, KubernetesResource] = {
        "k1": cast(KubernetesResource, DummyResource("k1", file_hash="h1")),
        "k2": cast(KubernetesResource, DummyResource("k2", file_hash="h2")),
    }
    scanned = [
        make_resource_data("k1", file_hash="h2"),
        make_resource_data("k3", file_hash="h3"),
    ]
    session.exec.return_value.first.return_value = None
    changeset = service.compare_resources(existing, scanned, session, uuid.uuid4())
    assert len(changeset.modified) == 1
    assert len(changeset.created) == 1
    assert len(changeset.deleted) == 1
    assert changeset.modified[0].type == "MODIFIED"
    assert changeset.created[0].type == "CREATED"
    assert changeset.deleted[0].type == "DELETED"


def test_compare_resources_resurrected(
    service: ResourceDatabaseService, session: MagicMock
) -> None:
    # Not in active, but in deleted
    existing: dict[str, KubernetesResource] = {}
    scanned = [make_resource_data("k1", file_hash="h1")]
    dummy = cast(KubernetesResource, DummyResource("k1", status="DELETED", file_hash="old"))
    session.exec.return_value.first.return_value = dummy
    changeset = service.compare_resources(existing, scanned, session, uuid.uuid4())
    assert len(changeset.modified) == 1
    assert changeset.modified[0].type == "RESURRECTED"


def test_apply_scan_results_creates_and_commits(
    service: ResourceDatabaseService, session: MagicMock
) -> None:
    # Patch methods to track calls
    service.get_existing_resources = MagicMock(return_value={})  # type: ignore
    service.compare_resources = MagicMock()  # type: ignore
    cs = ChangeSet()
    cs.created.append(MagicMock(resource_data=MagicMock()))
    cs.modified.append(
        MagicMock(
            existing_resource=MagicMock(), resource_data=MagicMock(), type="MODIFIED"
        )
    )
    cs.deleted.append(MagicMock(existing_resource=MagicMock()))
    service.compare_resources.return_value = cs
    # Patch private methods using patch.object context manager
    with (
        patch.object(
            service, "_create_resource", return_value=(MagicMock(), MagicMock())
        ),
        patch.object(
            service, "_update_resource", return_value=(MagicMock(), MagicMock())
        ),
        patch.object(
            service, "_resurrect_resource", return_value=(MagicMock(), MagicMock())
        ),
        patch.object(
            service, "_delete_resource", return_value=(MagicMock(), MagicMock())
        ),
    ):
        session.commit = MagicMock()
        result = service.apply_scan_results(session, uuid.uuid4(), [MagicMock()])
        assert result.created_count == 1
        assert result.modified_count == 1
        assert result.deleted_count == 1
        session.commit.assert_called()


def test_apply_scan_results_rollback_on_exception(
    service: ResourceDatabaseService, session: MagicMock
) -> None:
    service.get_existing_resources = MagicMock(side_effect=Exception("fail"))  # type: ignore
    session.rollback = MagicMock()
    with pytest.raises(Exception):  # noqa: B017
        service.apply_scan_results(session, uuid.uuid4(), [MagicMock()])
    session.rollback.assert_called()


def test_get_repository_resource_count(
    service: ResourceDatabaseService, session: MagicMock
) -> None:
    session.exec.return_value.all.return_value = [1, 2, 3]
    count = service.get_repository_resource_count(session, uuid.uuid4())
    assert count == 3


def test_create_update_delete_resource_methods(
    service: ResourceDatabaseService, session: MagicMock
) -> None:
    # These methods should add to session and return tuple
    class DummyRD(ResourceData):
        def __init__(self) -> None:
            super().__init__(
                api_version="v1",
                kind="Pod",
                name="foo",
                namespace="default",
                file_path="foo.yaml",
                file_hash="h",
                version="1.0",
                data={"foo": "bar"},
            )

    class DummyKR(DummyResource):
        def __init__(self) -> None:
            super().__init__(
                key="foo",
                api_version="v1",
                kind="Pod",
                name="foo",
                namespace="default",
                file_path="foo.yaml",
                file_hash="h",
                version="1.0",
                data={"foo": "bar"},
                status="ACTIVE",
            )

    # _create_resource
    kr, ev = service._create_resource(session, uuid.uuid4(), DummyRD(), uuid.uuid4())
    assert hasattr(kr, "repository_id")
    assert hasattr(ev, "event_type")
    # _resurrect_resource
    kr2, ev2 = service._resurrect_resource(session, cast(KubernetesResource, DummyKR()), DummyRD(), uuid.uuid4())
    assert hasattr(kr2, "status")
    assert ev2.event_type == "RESURRECTED"
    # _update_resource
    kr3, ev3 = service._update_resource(session, cast(KubernetesResource, DummyKR()), DummyRD(), uuid.uuid4())
    assert hasattr(kr3, "file_hash")
    assert ev3.event_type == "MODIFIED"
    # _delete_resource
    kr4, ev4 = service._delete_resource(session, cast(KubernetesResource, DummyKR()), uuid.uuid4())
    assert kr4.status == "DELETED"
    assert ev4.event_type == "DELETED"

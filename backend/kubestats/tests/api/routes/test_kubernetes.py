import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlmodel import Session

from kubestats.core.config import settings
from kubestats.models import KubernetesResource, Repository


def _clean_kubernetes_resources(db: Session) -> None:
    try:
        db.execute(delete(KubernetesResource))
        db.commit()
    except Exception:
        db.rollback()


def make_resource(
    repository_id: Any,
    kind: str = "Deployment",
    api_version: str = "apps/v1",
    name: str | None = None,
    namespace: str = "default",
    file_path: str = "/manifests/deploy.yaml",
    file_hash: str | None = None,
    version: str | None = None,
    data: dict[str, Any] | None = None,
    status: str = "ACTIVE",
    deleted_at: datetime | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> KubernetesResource:
    now = datetime.now(timezone.utc)
    return KubernetesResource(
        id=uuid.uuid4(),
        repository_id=repository_id,
        api_version=api_version,
        kind=kind,
        name=name or f"test-{uuid.uuid4().hex[:8]}",
        namespace=namespace,
        file_path=file_path,
        file_hash=file_hash or uuid.uuid4().hex,
        version=version,
        data=data or {"spec": {}},
        status=status,
        deleted_at=deleted_at,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


def test_list_kubernetes_resources_empty(client: TestClient, db: Session) -> None:
    _clean_kubernetes_resources(db)
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["count"] == 0


def test_list_kubernetes_resources_single(
    client: TestClient, db: Session, sample_repository: Repository
) -> None:
    _clean_kubernetes_resources(db)
    resource = make_resource(repository_id=sample_repository.id)
    db.add(resource)
    db.commit()
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == str(resource.id)
    assert data["data"][0]["repository_id"] == str(sample_repository.id)


def test_list_kubernetes_resources_filter_repository(
    client: TestClient, db: Session, sample_repository: Repository
) -> None:
    _clean_kubernetes_resources(db)
    resource = make_resource(repository_id=sample_repository.id)
    db.add(resource)
    db.commit()
    # Wrong repo
    response = client.get(
        f"{settings.API_V1_STR}/kubernetes/resources?repository_id=not-a-real-id"
    )
    assert response.status_code == 422
    # Correct repo
    response = client.get(
        f"{settings.API_V1_STR}/kubernetes/resources?repository_id={sample_repository.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["id"] == str(resource.id)


def test_list_kubernetes_resources_filter_kind(
    client: TestClient, db: Session, sample_repository: Repository
) -> None:
    _clean_kubernetes_resources(db)
    resource = make_resource(repository_id=sample_repository.id, kind="Service")
    db.add(resource)
    db.commit()
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?kind=Service")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["kind"] == "Service"
    # Wrong kind
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?kind=Deployment")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_list_kubernetes_resources_filter_api_version(
    client: TestClient, db: Session, sample_repository: Repository
) -> None:
    _clean_kubernetes_resources(db)
    resource = make_resource(repository_id=sample_repository.id, api_version="v1")
    db.add(resource)
    db.commit()
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?api_version=v1")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["api_version"] == "v1"
    # Wrong version
    response = client.get(
        f"{settings.API_V1_STR}/kubernetes/resources?api_version=apps/v1"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_list_kubernetes_resources_filter_namespace(
    client: TestClient, db: Session, sample_repository: Repository
) -> None:
    _clean_kubernetes_resources(db)
    resource = make_resource(repository_id=sample_repository.id, namespace="foo")
    db.add(resource)
    db.commit()
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?namespace=foo")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["namespace"] == "foo"
    # Wrong namespace
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?namespace=bar")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_list_kubernetes_resources_filter_status_single(
    client: TestClient, db: Session, sample_repository: Repository
) -> None:
    _clean_kubernetes_resources(db)
    resource = make_resource(repository_id=sample_repository.id, status="DELETED")
    db.add(resource)
    db.commit()
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?status=DELETED")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["status"] == "DELETED"
    # Wrong status
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?status=ACTIVE")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_list_kubernetes_resources_filter_status_list(
    client: TestClient, db: Session, sample_repository: Repository
) -> None:
    _clean_kubernetes_resources(db)
    r1 = make_resource(repository_id=sample_repository.id, status="ACTIVE")
    r2 = make_resource(repository_id=sample_repository.id, status="DELETED")
    r3 = make_resource(repository_id=sample_repository.id, status="MODIFIED")
    db.add(r1)
    db.add(r2)
    db.add(r3)
    db.commit()
    response = client.get(
        f"{settings.API_V1_STR}/kubernetes/resources?status=ACTIVE,DELETED"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    statuses = {item["status"] for item in data["data"]}
    assert statuses == {"ACTIVE", "DELETED"}


def test_list_kubernetes_resources_pagination(
    client: TestClient, db: Session, sample_repository: Repository
) -> None:
    _clean_kubernetes_resources(db)
    for i in range(5):
        db.add(make_resource(repository_id=sample_repository.id, name=f"res-{i}"))
    db.commit()
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["count"] == 5
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["count"] == 5
    response = client.get(f"{settings.API_V1_STR}/kubernetes/resources?skip=4&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["count"] == 5

import uuid

from kubestats.core.yaml_scanner import models
from kubestats.core.yaml_scanner.resource_db_service import KubernetesResource


def test_resource_data_to_dict_and_key() -> None:
    rd = models.ResourceData(
        api_version="v1",
        kind="Pod",
        file_path="foo/bar.yaml",
        file_hash="abc123",
        name="mypod",
        namespace="default",
        version="1.0.0",
        data={"foo": "bar"},
    )
    d = rd.to_dict()
    assert d["api_version"] == "v1"
    assert d["kind"] == "Pod"
    assert d["name"] == "mypod"
    assert d["namespace"] == "default"
    assert d["file_path"] == "foo/bar.yaml"
    assert d["version"] == "1.0.0"
    assert d["data"] == {"foo": "bar"}
    key = rd.resource_key()
    assert key == "v1:Pod:default:mypod:foo/bar.yaml"

    # No namespace
    rd2 = models.ResourceData(
        api_version="v1",
        kind="Pod",
        file_path="foo/bar.yaml",
        file_hash="abc123",
        name="mypod",
    )
    key2 = rd2.resource_key()
    assert key2 == "v1:Pod:mypod:foo/bar.yaml"


def test_resource_change_properties() -> None:
    # resource_data only
    rd = models.ResourceData(
        api_version="v1",
        kind="Pod",
        file_path="foo/bar.yaml",
        file_hash="abc123",
        name="mypod",
        namespace="default",
    )
    rc = models.ResourceChange(type="CREATED", resource_data=rd)
    assert rc.resource_name == "mypod"
    assert rc.resource_namespace == "default"
    assert rc.resource_kind == "Pod"
    assert rc.resource_api_version == "v1"
    assert rc.file_path == "foo/bar.yaml"

    # existing_resource only (mock)
    class Dummy(KubernetesResource):
        name = "ex"
        namespace = "ns"
        kind = "Kind"
        api_version = "apiv"
        file_path = "fpath"

        def resource_key(self) -> str:
            return "dummykey"

    rc2 = models.ResourceChange(type="DELETED", existing_resource=Dummy())
    assert rc2.resource_name == "ex"
    assert rc2.resource_namespace == "ns"
    assert rc2.resource_kind == "Kind"
    assert rc2.resource_api_version == "apiv"
    assert rc2.file_path == "fpath"

    # neither
    rc3 = models.ResourceChange(type="DELETED")
    assert rc3.resource_name == "unknown"
    assert rc3.resource_namespace is None
    assert rc3.resource_kind == "unknown"
    assert rc3.resource_api_version == "unknown"
    assert rc3.file_path is None


def test_changeset_init_and_lists() -> None:
    cs = models.ChangeSet()
    assert cs.created == []
    assert cs.modified == []
    assert cs.deleted == []
    rc1 = models.ResourceChange(type="CREATED")
    rc2 = models.ResourceChange(type="MODIFIED")
    rc3 = models.ResourceChange(type="DELETED")
    cs.created.append(rc1)
    cs.modified.append(rc2)
    cs.deleted.append(rc3)
    assert cs.created == [rc1]
    assert cs.modified == [rc2]
    assert cs.deleted == [rc3]


def test_scanresult_fields() -> None:
    scan_id = uuid.uuid4()
    sr = models.ScanResult(
        created_count=1,
        modified_count=2,
        deleted_count=3,
        total_resources=4,
        sync_run_id=scan_id,
        scan_duration_seconds=1.23,
    )
    assert sr.created_count == 1
    assert sr.modified_count == 2
    assert sr.deleted_count == 3
    assert sr.total_resources == 4
    assert sr.sync_run_id == scan_id
    assert sr.scan_duration_seconds == 1.23

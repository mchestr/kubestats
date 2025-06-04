from typing import Any

from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner


class DummyScanner(ResourceScanner):
    @property
    def resource_types(self) -> set[tuple[str, str]]:
        return {("foo.io", "Bar")}

    def post_process(self, resources: list[ResourceData]) -> None:
        self._post_processed = True


def test_parse_document_and_scan() -> None:
    scanner = DummyScanner()
    doc: dict[str, Any] = {
        "apiVersion": "foo.io/v1",
        "kind": "Bar",
        "metadata": {"name": "baz", "namespace": "ns"},
        "spec": {"x": 1},
    }
    rd = scanner.parse_document("foo.yaml", doc)
    assert isinstance(rd, ResourceData)
    assert rd.api_version == "foo.io/v1"
    assert rd.kind == "Bar"
    assert rd.name == "baz"
    assert rd.namespace == "ns"
    assert rd.file_path == "foo.yaml"
    assert rd.data == {"x": 1}
    # scan returns None if not supported
    doc2: dict[str, Any] = {"apiVersion": "other.io/v1", "kind": "Bar"}
    assert scanner.scan("foo.yaml", doc2) is None
    # scan returns ResourceData if supported
    doc3: dict[str, Any] = {
        "apiVersion": "foo.io/v1",
        "kind": "Bar",
        "metadata": {"name": "baz"},
    }
    assert isinstance(scanner.scan("foo.yaml", doc3), ResourceData)


def test_is_supported_resource() -> None:
    scanner = DummyScanner()
    # Supported
    assert scanner.is_supported_resource("foo.io/v1", "Bar") == scanner
    # Not supported
    assert scanner.is_supported_resource("foo.io/v1", "Other") is None
    assert scanner.is_supported_resource("other.io/v1", "Bar") is None


def test_post_process_and_validate() -> None:
    scanner = DummyScanner()
    resources: list[ResourceData] = [
        ResourceData(api_version="foo.io/v1", kind="Bar", file_path="f", file_hash="h")
    ]
    scanner.post_process(resources)
    assert hasattr(scanner, "_post_processed")
    # validate_resource always True by default
    assert scanner.validate_resource(resources[0])


def test_extract_additional_data() -> None:
    scanner = DummyScanner()
    doc: dict[str, Any] = {"spec": {"foo": "bar"}}
    assert scanner.extract_additional_data(doc) == {"foo": "bar"}
    doc2: dict[str, Any] = {"metadata": {"name": "baz"}}
    assert scanner.extract_additional_data(doc2) == {}

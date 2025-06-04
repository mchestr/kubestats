from pathlib import Path
from typing import Any

from pytest import MonkeyPatch

from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.repository_scanner import RepositoryScanner


def test_find_yaml_files_filters_hidden(tmp_path: Path) -> None:
    # Create visible and hidden files/dirs
    (tmp_path / "foo.yaml").write_text("apiVersion: v1\nkind: Pod\n")
    (tmp_path / ".hidden.yaml").write_text("apiVersion: v1\nkind: Pod\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "bar.yaml").write_text("apiVersion: v1\nkind: Pod\n")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "baz.yaml").write_text("apiVersion: v1\nkind: Pod\n")
    scanner = RepositoryScanner()
    files = scanner.find_yaml_files(tmp_path)
    files_str = [str(f) for f in files]
    assert any("foo.yaml" in f for f in files_str)
    assert any("bar.yaml" in f for f in files_str)
    assert not any(".hidden.yaml" in f for f in files_str)
    assert not any("baz.yaml" in f for f in files_str)


def test_parse_yaml_file_handles_empty_and_invalid(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.yaml"
    file_path.write_text("")
    scanner = RepositoryScanner()
    assert scanner.parse_yaml_file(file_path) == []
    # Invalid YAML
    bad_path = tmp_path / "bad.yaml"
    bad_path.write_text("::not yaml::")
    assert scanner.parse_yaml_file(bad_path) == [{"::not yaml:": None}]


def test_parse_yaml_file_valid(tmp_path: Path) -> None:
    file_path = tmp_path / "good.yaml"
    file_path.write_text(
        """apiVersion: v1\nkind: Pod\n---\napiVersion: v2\nkind: Service\n"""
    )
    scanner = RepositoryScanner()
    docs = scanner.parse_yaml_file(file_path)
    assert isinstance(docs, list)
    assert len(docs) == 2
    assert docs[0]["apiVersion"] == "v1"
    assert docs[1]["apiVersion"] == "v2"


def test_process_yaml_file_and_document(monkeypatch: MonkeyPatch) -> None:
    scanner = RepositoryScanner()
    # Patch parse_yaml_file to return two docs
    monkeypatch.setattr(
        scanner,
        "parse_yaml_file",
        lambda fp: [
            {"apiVersion": "a", "kind": "b"},
            {"apiVersion": "c", "kind": "d"},
        ],
    )
    # Patch process_document to return ResourceData for first, None for second
    rd = ResourceData(api_version="a", kind="b", file_path="f", file_hash="h")

    def fake_process_document(
        rel: str, doc: dict[str, Any], idx: int = 0
    ) -> ResourceData | None:
        return rd if idx == 0 else None

    monkeypatch.setattr(scanner, "process_document", fake_process_document)
    result = scanner.process_yaml_file(Path("/repo/file.yaml"), Path("/repo"))
    assert result == [rd]


def test_process_document_skips_invalid(monkeypatch: MonkeyPatch) -> None:
    scanner = RepositoryScanner()
    # Not a dict
    assert scanner.process_document("foo.yaml", {}) is None
    # Missing apiVersion/kind
    assert scanner.process_document("foo.yaml", {"kind": "Pod"}) is None
    assert scanner.process_document("foo.yaml", {"apiVersion": "v1"}) is None
    # Not supported resource
    monkeypatch.setattr(
        scanner.flux_scanner, "is_supported_resource", lambda a, k: False
    )
    doc = {"apiVersion": "v1", "kind": "Pod"}
    assert scanner.process_document("foo.yaml", doc) is None


def test_process_document_valid(monkeypatch: MonkeyPatch) -> None:
    scanner = RepositoryScanner()
    monkeypatch.setattr(
        scanner.flux_scanner, "is_supported_resource", lambda a, k: True
    )
    rd = ResourceData(api_version="v1", kind="Pod", file_path="foo.yaml", file_hash="h")
    monkeypatch.setattr(scanner.flux_scanner, "parse_document", lambda fp, doc: rd)
    monkeypatch.setattr(scanner, "_validate_resource_data", lambda r: True)
    doc = {"apiVersion": "v1", "kind": "Pod"}
    assert scanner.process_document("foo.yaml", doc) == rd


def test_process_document_invalid_resource(monkeypatch: MonkeyPatch) -> None:
    scanner = RepositoryScanner()
    monkeypatch.setattr(
        scanner.flux_scanner, "is_supported_resource", lambda a, k: True
    )
    rd = ResourceData(api_version="v1", kind="Pod", file_path="foo.yaml", file_hash="h")
    monkeypatch.setattr(scanner.flux_scanner, "parse_document", lambda fp, doc: rd)
    monkeypatch.setattr(scanner, "_validate_resource_data", lambda r: False)
    doc = {"apiVersion": "v1", "kind": "Pod"}
    assert scanner.process_document("foo.yaml", doc) is None


def test_scan_directory_post_process(monkeypatch: MonkeyPatch) -> None:
    scanner = RepositoryScanner()
    # Patch find_yaml_files to return two files
    monkeypatch.setattr(
        scanner,
        "find_yaml_files",
        lambda repo: [Path("/repo/a.yaml"), Path("/repo/b.yaml")],
    )
    # Patch process_yaml_file to return ResourceData
    rd1 = ResourceData(api_version="v1", kind="Pod", file_path="a.yaml", file_hash="h1")
    rd2 = ResourceData(
        api_version="v2", kind="Service", file_path="b.yaml", file_hash="h2"
    )

    def fake_process_yaml_file(fp: Path, root: Path) -> list[ResourceData]:
        return [rd1] if "a.yaml" in str(fp) else [rd2]

    monkeypatch.setattr(
        scanner,
        "process_yaml_file",
        fake_process_yaml_file,
    )
    called = {}

    def fake_post_process(resources: list[ResourceData]) -> None:
        called["called"] = True

    monkeypatch.setattr(scanner.flux_scanner, "post_process", fake_post_process)
    resources = scanner.scan_directory(Path("/repo"))
    assert rd1 in resources and rd2 in resources
    assert called["called"]


def test_scan_directory_handles_exceptions(monkeypatch: MonkeyPatch) -> None:
    scanner = RepositoryScanner()
    monkeypatch.setattr(
        scanner,
        "find_yaml_files",
        lambda repo: [Path("/repo/a.yaml"), Path("/repo/b.yaml")],
    )

    # First file raises, second returns ResourceData
    def proc(fp: Path, root: Path) -> list[ResourceData]:
        if "a.yaml" in str(fp):
            raise Exception("fail")
        return [
            ResourceData(
                api_version="v2", kind="Service", file_path="b.yaml", file_hash="h2"
            )
        ]

    monkeypatch.setattr(scanner, "process_yaml_file", proc)
    monkeypatch.setattr(scanner.flux_scanner, "post_process", lambda resources: None)
    resources = scanner.scan_directory(Path("/repo"))
    assert len(resources) == 1
    assert resources[0].kind == "Service"


def test__validate_resource_data() -> None:
    scanner = RepositoryScanner()
    # All required fields
    rd = ResourceData(api_version="a", kind="b", name="n", file_path="f", file_hash="h")
    assert scanner._validate_resource_data(rd)
    # Missing fields
    rd2 = ResourceData(api_version="a", kind="b", file_path="f", file_hash="h")
    assert not scanner._validate_resource_data(rd2)
    rd3 = ResourceData(api_version="a", kind="b", name="n", file_path="f", file_hash="")
    assert not scanner._validate_resource_data(rd3)

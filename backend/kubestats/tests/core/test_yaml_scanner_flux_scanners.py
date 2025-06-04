from typing import Any

import pytest

from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners.flux import (
    FluxResourceScanner,
    GitRepositoryResourceScanner,
    HelmReleaseResourceScanner,
    KustomizationResourceScanner,
    OciRepositoryResourceScanner,
)


def test_flux_resource_scanner_resource_types() -> None:
    scanner = FluxResourceScanner()
    types = scanner.resource_types
    assert ("helm.toolkit.fluxcd.io/v2", "HelmRelease") in types
    assert ("source.toolkit.fluxcd.io", "GitRepository") in types
    assert ("kustomize.toolkit.fluxcd.io", "Kustomization") in types
    assert ("source.toolkit.fluxcd.io", "OCIRepository") in types


def test_flux_resource_scanner_is_supported_resource() -> None:
    scanner = FluxResourceScanner()
    assert scanner.is_supported_resource("helm.toolkit.fluxcd.io/v2", "HelmRelease")
    assert scanner.is_supported_resource("source.toolkit.fluxcd.io", "GitRepository")
    assert scanner.is_supported_resource("kustomize.toolkit.fluxcd.io", "Kustomization")
    assert scanner.is_supported_resource("source.toolkit.fluxcd.io", "OCIRepository")
    assert scanner.is_supported_resource("not.flux.io", "Unknown") is None


def test_flux_resource_scanner_parse_document_success() -> None:
    scanner = FluxResourceScanner()
    doc: dict[str, Any] = {
        "apiVersion": "helm.toolkit.fluxcd.io/v2",
        "kind": "HelmRelease",
        "metadata": {"name": "foo"},
        "spec": {"chart": {"spec": {"version": "1.2.3"}}},
    }
    rd = scanner.parse_document("foo.yaml", doc)
    assert isinstance(rd, ResourceData)
    assert rd.version == "1.2.3"
    assert rd.name == "foo"


def test_flux_resource_scanner_parse_document_no_scanner() -> None:
    scanner = FluxResourceScanner()
    doc: dict[str, Any] = {"apiVersion": "not.flux.io/v1", "kind": "Unknown"}
    with pytest.raises(ValueError):
        scanner.parse_document("foo.yaml", doc)


def test_flux_resource_scanner_post_process_namespace_and_version() -> None:
    scanner = FluxResourceScanner()
    # Kustomization sets targetNamespace for other resources in same path
    kustom = ResourceData(
        api_version="kustomize.toolkit.fluxcd.io/v1",
        kind="Kustomization",
        file_path="foo/bar/kustom.yaml",
        file_hash="h",
        data={"targetNamespace": "ns1"},
    )
    helm = ResourceData(
        api_version="helm.toolkit.fluxcd.io/v2",
        kind="HelmRelease",
        file_path="foo/bar/helm.yaml",
        file_hash="h2",
        data={"chartRef": {"name": "mychart"}},
    )
    oci = ResourceData(
        api_version="source.toolkit.fluxcd.io/v1",
        kind="OCIRepository",
        file_path="foo/bar/oci.yaml",
        file_hash="h3",
        name="mychart",
        version="2.0.0",
    )
    resources = [kustom, helm, oci]
    scanner.post_process(resources)
    # HelmRelease should get version from oci
    assert helm.version == "2.0.0"
    # HelmRelease should get namespace from kustomization
    assert helm.namespace == "ns1"


def test_helm_release_resource_scanner_parse_document() -> None:
    scanner = HelmReleaseResourceScanner()
    doc: dict[str, Any] = {
        "apiVersion": "helm.toolkit.fluxcd.io/v2",
        "kind": "HelmRelease",
        "metadata": {"name": "foo"},
        "spec": {"chart": {"spec": {"version": "1.2.3"}}},
    }
    rd = scanner.parse_document("foo.yaml", doc)
    assert rd.version == "1.2.3"
    assert rd.name == "foo"


def test_git_repository_resource_scanner() -> None:
    scanner = GitRepositoryResourceScanner()
    assert scanner.resource_types == {("source.toolkit.fluxcd.io", "GitRepository")}
    doc: dict[str, Any] = {
        "apiVersion": "source.toolkit.fluxcd.io/v1",
        "kind": "GitRepository",
        "metadata": {"name": "foo"},
    }
    rd = scanner.parse_document("foo.yaml", doc)
    assert rd.name == "foo"
    scanner.post_process([rd])  # should not raise


def test_kustomization_resource_scanner() -> None:
    scanner = KustomizationResourceScanner()
    assert scanner.resource_types == {("kustomize.toolkit.fluxcd.io", "Kustomization")}
    doc: dict[str, Any] = {
        "apiVersion": "kustomize.toolkit.fluxcd.io/v1",
        "kind": "Kustomization",
        "metadata": {"name": "foo"},
    }
    rd = scanner.parse_document("foo.yaml", doc)
    assert rd.name == "foo"
    scanner.post_process([rd])  # should not raise


def test_oci_repository_resource_scanner() -> None:
    scanner = OciRepositoryResourceScanner()
    assert scanner.resource_types == {("source.toolkit.fluxcd.io", "OCIRepository")}
    doc: dict[str, Any] = {
        "apiVersion": "source.toolkit.fluxcd.io/v1",
        "kind": "OCIRepository",
        "metadata": {"name": "foo"},
        "spec": {"ref": {"tag": "v1.0.0"}},
    }
    rd = scanner.parse_document("foo.yaml", doc)
    assert rd.version == "v1.0.0"
    assert rd.name == "foo"
    scanner.post_process([rd])  # should not raise

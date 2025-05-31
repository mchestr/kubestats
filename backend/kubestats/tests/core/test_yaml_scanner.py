"""
Tests for YAML scanner functionality
"""

from unittest.mock import Mock

from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.parser import YAMLParser
from kubestats.core.yaml_scanner.resource_extractor import ResourceExtractor


def test_parse_oci_repository_helmrelease_chartref_pattern():
    """Test parsing OCIRepository + HelmRelease with chartRef pattern"""
    yaml_content = """---
# yaml-language-server: $schema=https://kubernetes-schemas.pages.dev/source.toolkit.fluxcd.io/ocirepository_v1.json
apiVersion: source.toolkit.fluxcd.io/v1
kind: OCIRepository
metadata:
  name: grafana
spec:
  interval: 5m
  layerSelector:
    mediaType: application/vnd.cncf.helm.chart.content.v1.tar+gzip
    operation: copy
  ref:
    tag: 9.2.1
  url: oci://ghcr.io/grafana/helm-charts/grafana
---
# yaml-language-server: $schema=https://kubernetes-schemas.pages.dev/helm.toolkit.fluxcd.io/helmrelease_v2.json
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: grafana
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: grafana
  install:
    remediation:
      retries: -1
  upgrade:
    cleanupOnFail: true
    remediation:
      retries: 3
  values:
    deploymentStrategy:
      type: Recreate
"""
    parser = YAMLParser()
    resources = parser.parse_multi_document_yaml(yaml_content, "grafana.yaml")

    assert len(resources) == 2

    # Find OCIRepository
    oci_repo = next((r for r in resources if r.kind == "OCIRepository"), None)
    assert oci_repo is not None
    assert oci_repo.name == "grafana"
    assert oci_repo.api_version == "source.toolkit.fluxcd.io/v1"
    assert oci_repo.spec["ref"]["tag"] == "9.2.1"
    assert oci_repo.spec["url"] == "oci://ghcr.io/grafana/helm-charts/grafana"

    # Find HelmRelease
    helm_release = next((r for r in resources if r.kind == "HelmRelease"), None)
    assert helm_release is not None
    assert helm_release.name == "grafana"
    assert helm_release.api_version == "helm.toolkit.fluxcd.io/v2"
    assert helm_release.spec["chartRef"]["kind"] == "OCIRepository"
    assert helm_release.spec["chartRef"]["name"] == "grafana"


def test_parse_helmrepository_helmrelease_chart_spec_pattern():
    """Test parsing HelmRepository + HelmRelease with chart.spec pattern"""
    yaml_content = """---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: cloudnative-pg
spec:
  interval: 15m
  chart:
    spec:
      chart: cloudnative-pg
      version: 0.24.0
      sourceRef:
        kind: HelmRepository
        name: cloudnative-pg
        namespace: flux-system
      interval: 15m
  maxHistory: 2
  install:
    remediation:
      retries: -1
  upgrade:
    cleanupOnFail: false
    remediation:
      retries: 3
  uninstall:
    keepHistory: false
  values:
    crds:
      create: true
"""
    parser = YAMLParser()
    resources = parser.parse_multi_document_yaml(yaml_content, "cloudnative-pg.yaml")

    assert len(resources) == 1

    # Find HelmRelease
    helm_release = resources[0]
    assert helm_release.kind == "HelmRelease"
    assert helm_release.name == "cloudnative-pg"
    assert helm_release.api_version == "helm.toolkit.fluxcd.io/v2"
    assert helm_release.spec["chart"]["spec"]["chart"] == "cloudnative-pg"
    assert helm_release.spec["chart"]["spec"]["version"] == "0.24.0"
    assert helm_release.spec["chart"]["spec"]["sourceRef"]["kind"] == "HelmRepository"
    assert helm_release.spec["chart"]["spec"]["sourceRef"]["name"] == "cloudnative-pg"


def test_parse_single_document_yaml():
    """Test parsing single document YAML"""
    yaml_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test
  template:
    spec:
      containers:
      - name: main
        image: nginx:1.21
"""
    parser = YAMLParser()
    resource = parser.parse_yaml_content(yaml_content, "deployment.yaml")

    assert resource is not None
    assert resource.kind == "Deployment"
    assert resource.name == "test-deployment"
    assert resource.namespace == "default"
    assert resource.spec["replicas"] == 3


def test_parse_invalid_yaml():
    """Test parsing invalid YAML returns None"""
    parser = YAMLParser()
    resource = parser.parse_yaml_content("invalid: yaml: content:", "invalid.yaml")
    assert resource is None


def test_parse_non_kubernetes_yaml():
    """Test parsing non-Kubernetes YAML returns None"""
    yaml_content = """
name: test
description: This is not a Kubernetes resource
"""
    parser = YAMLParser()
    resource = parser.parse_yaml_content(yaml_content, "non-k8s.yaml")
    assert resource is None


def test_is_target_resource():
    """Test resource type filtering"""
    parser = YAMLParser()

    # Test Flux resources
    assert parser.is_target_resource("helm.toolkit.fluxcd.io/v2", "HelmRelease")
    assert parser.is_target_resource("source.toolkit.fluxcd.io/v1", "OCIRepository")

    # Test Kubernetes resources
    assert parser.is_target_resource("apps/v1", "Deployment")
    assert parser.is_target_resource("v1", "Service")

    # Test non-target resources
    assert not parser.is_target_resource("v1", "Pod")
    assert not parser.is_target_resource("custom.io/v1", "CustomResource")


def test_extract_helmrelease_chartref_metrics():
    """Test extracting metrics from HelmRelease with chartRef pattern"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    # Create mock resource
    mock_resource = Mock()
    mock_resource.id = "test-uuid"

    # Create ResourceData for HelmRelease with chartRef
    resource_data = ResourceData(
        api_version="helm.toolkit.fluxcd.io/v2",
        kind="HelmRelease",
        name="grafana",
        namespace=None,
        file_path="grafana.yaml",
        file_hash="test-hash",
        metadata={"name": "grafana"},
        spec={
            "interval": "1h",
            "chartRef": {"kind": "OCIRepository", "name": "grafana"},
        },
        raw_content={},
    )

    metrics = extractor.extract_resource_metrics(resource_data, mock_resource)

    assert metrics is not None
    assert metrics.chart_name == "grafana"
    assert metrics.source_revision == "grafana"
    # Version should be None here, resolved from OCIRepository later
    assert metrics.chart_version is None


def test_extract_helmrelease_chart_spec_metrics():
    """Test extracting metrics from HelmRelease with chart.spec pattern"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    # Create mock resource
    mock_resource = Mock()
    mock_resource.id = "test-uuid"

    # Create ResourceData for HelmRelease with chart.spec
    resource_data = ResourceData(
        api_version="helm.toolkit.fluxcd.io/v2",
        kind="HelmRelease",
        name="cloudnative-pg",
        namespace=None,
        file_path="cloudnative-pg.yaml",
        file_hash="test-hash",
        metadata={"name": "cloudnative-pg"},
        spec={
            "interval": "15m",
            "chart": {
                "spec": {
                    "chart": "cloudnative-pg",
                    "version": "0.24.0",
                    "sourceRef": {
                        "kind": "HelmRepository",
                        "name": "cloudnative-pg",
                        "namespace": "flux-system",
                    },
                }
            },
        },
        raw_content={},
    )

    metrics = extractor.extract_resource_metrics(resource_data, mock_resource)

    assert metrics is not None
    assert metrics.chart_name == "cloudnative-pg"
    assert metrics.chart_version == "0.24.0"
    assert metrics.chart_repository == "cloudnative-pg"
    assert metrics.source_revision == "cloudnative-pg"


def test_extract_ocirepository_metrics():
    """Test extracting metrics from OCIRepository"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    # Create mock resource
    mock_resource = Mock()
    mock_resource.id = "test-uuid"

    # Create ResourceData for OCIRepository
    resource_data = ResourceData(
        api_version="source.toolkit.fluxcd.io/v1",
        kind="OCIRepository",
        name="grafana",
        namespace=None,
        file_path="grafana.yaml",
        file_hash="test-hash",
        metadata={"name": "grafana"},
        spec={
            "interval": "5m",
            "ref": {"tag": "9.2.1"},
            "url": "oci://ghcr.io/grafana/helm-charts/grafana",
        },
        raw_content={},
    )

    metrics = extractor.extract_resource_metrics(resource_data, mock_resource)

    assert metrics is not None
    assert metrics.chart_version == "9.2.1"
    assert metrics.chart_repository == "oci://ghcr.io/grafana/helm-charts/grafana"


def test_extract_deployment_metrics():
    """Test extracting metrics from Deployment"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    # Create mock resource
    mock_resource = Mock()
    mock_resource.id = "test-uuid"

    # Create ResourceData for Deployment
    resource_data = ResourceData(
        api_version="apps/v1",
        kind="Deployment",
        name="test-app",
        namespace="default",
        file_path="deployment.yaml",
        file_hash="test-hash",
        metadata={"name": "test-app"},
        spec={
            "replicas": 3,
            "template": {
                "spec": {
                    "containers": [
                        {"name": "main", "image": "nginx:1.21"},
                        {"name": "sidecar", "image": "busybox:latest"},
                    ]
                }
            },
        },
        raw_content={},
    )

    metrics = extractor.extract_resource_metrics(resource_data, mock_resource)

    assert metrics is not None
    assert metrics.replicas == 3
    assert metrics.image_versions["main"] == "nginx:1.21"
    assert metrics.image_versions["sidecar"] == "busybox:latest"


def test_find_chartref_references():
    """Test finding chartRef references in HelmRelease"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    resource_data = ResourceData(
        api_version="helm.toolkit.fluxcd.io/v2",
        kind="HelmRelease",
        name="grafana",
        namespace=None,
        file_path="grafana.yaml",
        file_hash="test-hash",
        metadata={"name": "grafana"},
        spec={"chartRef": {"kind": "OCIRepository", "name": "grafana"}},
        raw_content={},
    )

    references = extractor.find_resource_references(resource_data)

    assert len(references) == 1
    ref = references[0]
    assert ref["type"] == "chartRef"
    assert ref["path"] == "spec.chartRef"
    assert ref["target_name"] == "grafana"
    assert ref["target_kind"] == "OCIRepository"
    assert ref["target_api_version"] == "source.toolkit.fluxcd.io/v1"


def test_find_chart_spec_references():
    """Test finding chart.spec.sourceRef references in HelmRelease"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    resource_data = ResourceData(
        api_version="helm.toolkit.fluxcd.io/v2",
        kind="HelmRelease",
        name="cloudnative-pg",
        namespace=None,
        file_path="cloudnative-pg.yaml",
        file_hash="test-hash",
        metadata={"name": "cloudnative-pg"},
        spec={
            "chart": {
                "spec": {
                    "chart": "cloudnative-pg",
                    "version": "0.24.0",
                    "sourceRef": {
                        "kind": "HelmRepository",
                        "name": "cloudnative-pg",
                        "namespace": "flux-system",
                    },
                }
            }
        },
        raw_content={},
    )

    references = extractor.find_resource_references(resource_data)

    assert len(references) == 1
    ref = references[0]
    assert ref["type"] == "sourceRef"
    assert ref["path"] == "spec.chart.spec.sourceRef"
    assert ref["target_name"] == "cloudnative-pg"
    assert ref["target_kind"] == "HelmRepository"
    assert ref["target_api_version"] == "source.toolkit.fluxcd.io/v1beta2"
    assert ref["version"] == "0.24.0"


def test_extract_references_method():
    """Test the extract_references method used for testing"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    resource_data = ResourceData(
        api_version="helm.toolkit.fluxcd.io/v2",
        kind="HelmRelease",
        name="grafana",
        namespace=None,
        file_path="grafana.yaml",
        file_hash="test-hash",
        metadata={"name": "grafana"},
        spec={"chartRef": {"kind": "OCIRepository", "name": "grafana"}},
        raw_content={},
    )

    reference_objects = extractor.extract_references(resource_data)

    assert len(reference_objects) == 1
    ref_obj = reference_objects[0]
    assert ref_obj.reference_type == "chartRef"
    assert ref_obj.target_kind == "OCIRepository"
    assert ref_obj.target_name == "grafana"
    assert ref_obj.target_api_version == "source.toolkit.fluxcd.io/v1"


def test_get_api_version_for_kind():
    """Test API version mapping for different resource kinds"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    assert (
        extractor._get_api_version_for_kind("OCIRepository")
        == "source.toolkit.fluxcd.io/v1"
    )
    assert (
        extractor._get_api_version_for_kind("HelmRepository")
        == "source.toolkit.fluxcd.io/v1beta2"
    )
    assert (
        extractor._get_api_version_for_kind("GitRepository")
        == "source.toolkit.fluxcd.io/v1beta2"
    )
    assert (
        extractor._get_api_version_for_kind("UnknownKind")
        == "source.toolkit.fluxcd.io/v1beta2"
    )


def test_resolve_cross_resource_versions():
    """Test resolving versions from referenced resources"""
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    # Create OCIRepository resource data
    oci_repo_data = ResourceData(
        api_version="source.toolkit.fluxcd.io/v1",
        kind="OCIRepository",
        name="grafana",
        namespace=None,
        file_path="grafana.yaml",
        file_hash="test-hash",
        metadata={"name": "grafana"},
        spec={
            "ref": {"tag": "9.2.1"},
            "url": "oci://ghcr.io/grafana/helm-charts/grafana",
        },
        raw_content={},
    )

    # Create HelmRelease resource data with chartRef
    helm_release_data = ResourceData(
        api_version="helm.toolkit.fluxcd.io/v2",
        kind="HelmRelease",
        name="grafana",
        namespace=None,
        file_path="grafana.yaml",
        file_hash="test-hash",
        metadata={"name": "grafana"},
        spec={"chartRef": {"kind": "OCIRepository", "name": "grafana"}},
        raw_content={},
    )

    # Create mock resources and metrics
    mock_oci_resource = Mock()
    mock_oci_resource.id = "oci-uuid"
    mock_helm_resource = Mock()
    mock_helm_resource.id = "helm-uuid"

    # Extract initial metrics
    oci_metrics = extractor.extract_resource_metrics(oci_repo_data, mock_oci_resource)
    helm_metrics = extractor.extract_resource_metrics(
        helm_release_data, mock_helm_resource
    )

    # Verify initial state
    assert oci_metrics.chart_version == "9.2.1"
    assert helm_metrics.chart_version is None  # No version initially

    # Create resources and metrics maps
    resources = {
        oci_repo_data.resource_key(): oci_repo_data,
        helm_release_data.resource_key(): helm_release_data,
    }
    metrics_map = {
        oci_repo_data.resource_key(): oci_metrics,
        helm_release_data.resource_key(): helm_metrics,
    }

    # Resolve cross-resource versions
    extractor.resolve_cross_resource_versions(resources, metrics_map)

    # Verify version was resolved
    assert (
        helm_metrics.chart_version == "9.2.1"
    )  # Should now have version from OCIRepository
    assert (
        helm_metrics.chart_repository == "oci://ghcr.io/grafana/helm-charts/grafana"
    )  # Should also have repository URL


def test_grafana_oci_repository_scenario():
    """Test the complete Grafana OCIRepository scenario"""
    yaml_content = """---
apiVersion: source.toolkit.fluxcd.io/v1
kind: OCIRepository
metadata:
  name: grafana
spec:
  interval: 5m
  layerSelector:
    mediaType: application/vnd.cncf.helm.chart.content.v1.tar+gzip
    operation: copy
  ref:
    tag: 9.2.1
  url: oci://ghcr.io/grafana/helm-charts/grafana
---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: grafana
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: grafana
  install:
    remediation:
      retries: -1
  upgrade:
    cleanupOnFail: true
    remediation:
      retries: 3
  values:
    deploymentStrategy:
      type: Recreate
"""

    parser = YAMLParser()
    resources = parser.parse_multi_document_yaml(yaml_content, "grafana.yaml")

    # Verify parsing
    assert len(resources) == 2

    # Create mock session and extractor
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    # Test OCIRepository metrics
    oci_repo = next((r for r in resources if r.kind == "OCIRepository"), None)
    mock_oci_resource = Mock()
    mock_oci_resource.id = "oci-uuid"

    oci_metrics = extractor.extract_resource_metrics(oci_repo, mock_oci_resource)
    assert oci_metrics.chart_version == "9.2.1"
    assert oci_metrics.chart_repository == "oci://ghcr.io/grafana/helm-charts/grafana"

    # Test HelmRelease metrics
    helm_release = next((r for r in resources if r.kind == "HelmRelease"), None)
    mock_helm_resource = Mock()
    mock_helm_resource.id = "helm-uuid"

    helm_metrics = extractor.extract_resource_metrics(helm_release, mock_helm_resource)
    assert helm_metrics.chart_name == "grafana"
    assert helm_metrics.source_revision == "grafana"
    # Initially no version (will be resolved from OCIRepository)
    assert helm_metrics.chart_version is None

    # Test version resolution
    resources_dict = {
        oci_repo.resource_key(): oci_repo,
        helm_release.resource_key(): helm_release,
    }
    metrics_map = {
        oci_repo.resource_key(): oci_metrics,
        helm_release.resource_key(): helm_metrics,
    }

    # Resolve cross-resource versions
    extractor.resolve_cross_resource_versions(resources_dict, metrics_map)

    # Now HelmRelease should have version from OCIRepository
    assert helm_metrics.chart_version == "9.2.1"
    assert helm_metrics.chart_repository == "oci://ghcr.io/grafana/helm-charts/grafana"

    # Test references
    helm_references = extractor.find_resource_references(helm_release)
    assert len(helm_references) == 1
    ref = helm_references[0]
    assert ref["type"] == "chartRef"
    assert ref["target_name"] == "grafana"
    assert ref["target_kind"] == "OCIRepository"


def test_cloudnative_pg_helm_repository_scenario():
    """Test the complete CloudNative-PG HelmRepository scenario"""
    yaml_content = """---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: cloudnative-pg
spec:
  interval: 15m
  chart:
    spec:
      chart: cloudnative-pg
      version: 0.24.0
      sourceRef:
        kind: HelmRepository
        name: cloudnative-pg
        namespace: flux-system
      interval: 15m
  maxHistory: 2
  install:
    remediation:
      retries: -1
  upgrade:
    cleanupOnFail: false
    remediation:
      retries: 3
  uninstall:
    keepHistory: false
  values:
    crds:
      create: true
"""

    parser = YAMLParser()
    resources = parser.parse_multi_document_yaml(yaml_content, "cloudnative-pg.yaml")

    # Verify parsing
    assert len(resources) == 1

    # Create mock session and extractor
    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    # Test HelmRelease metrics
    helm_release = resources[0]
    mock_helm_resource = Mock()
    mock_helm_resource.id = "helm-uuid"

    helm_metrics = extractor.extract_resource_metrics(helm_release, mock_helm_resource)
    assert helm_metrics.chart_name == "cloudnative-pg"
    assert helm_metrics.chart_version == "0.24.0"
    assert helm_metrics.chart_repository == "cloudnative-pg"
    assert helm_metrics.source_revision == "cloudnative-pg"

    # Test references
    helm_references = extractor.find_resource_references(helm_release)
    assert len(helm_references) == 1
    ref = helm_references[0]
    assert ref["type"] == "sourceRef"
    assert ref["target_name"] == "cloudnative-pg"
    assert ref["target_kind"] == "HelmRepository"
    assert ref["target_namespace"] == "flux-system"
    assert ref["version"] == "0.24.0"


def test_extract_resource_references_with_version_resolution():
    """Test that chartRef references resolve versions from OCIRepository"""
    import uuid
    from unittest.mock import Mock

    mock_session = Mock()
    extractor = ResourceExtractor(mock_session)

    # Create OCIRepository resource data
    oci_repo_data = ResourceData(
        api_version="source.toolkit.fluxcd.io/v1",
        kind="OCIRepository",
        name="grafana",
        namespace=None,
        file_path="grafana.yaml",
        file_hash="test-hash",
        metadata={"name": "grafana"},
        spec={
            "ref": {"tag": "9.2.1"},
            "url": "oci://ghcr.io/grafana/helm-charts/grafana",
        },
        raw_content={},
    )

    # Create HelmRelease resource data with chartRef
    helm_release_data = ResourceData(
        api_version="helm.toolkit.fluxcd.io/v2",
        kind="HelmRelease",
        name="grafana",
        namespace=None,
        file_path="grafana.yaml",
        file_hash="test-hash",
        metadata={"name": "grafana"},
        spec={"chartRef": {"kind": "OCIRepository", "name": "grafana"}},
        raw_content={},
    )

    # Create resources map
    resources = {
        oci_repo_data.resource_key(): oci_repo_data,
        helm_release_data.resource_key(): helm_release_data,
    }

    # Mock the source resource resolution
    extractor._resolve_source_resource = Mock(return_value=uuid.uuid4())
    extractor._resolve_reference_target = Mock(return_value=uuid.uuid4())

    repository_id = uuid.uuid4()

    # Extract references
    extractor.extract_resource_references(resources, repository_id)

    # Check that session.add was called
    assert mock_session.add.called

    # Get the reference that was added
    added_reference = mock_session.add.call_args[0][0]

    # Verify the reference has the resolved version
    assert added_reference.reference_type == "chartRef"
    assert added_reference.target_kind == "OCIRepository"
    assert added_reference.target_name == "grafana"
    assert (
        added_reference.referenced_version == "9.2.1"
    )  # Should be resolved from OCIRepository

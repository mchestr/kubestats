import { useQuery } from "@tanstack/react-query"
import type React from "react"
import { useMemo, useState } from "react"
import { KubernetesService, RepositoriesService } from "../../client/sdk.gen"
import { ResourceDetailsDrawer } from "./ResourceDetailsDrawer"
import { ResourceFilters } from "./ResourceFilters"
import { ResourceSummary } from "./ResourceSummary"
import { ResourceTable } from "./ResourceTable"

const PAGE_SIZE = 25

export const ResourceDashboard: React.FC = () => {
  // Filter and pagination state
  const [repositoryId, setRepositoryId] = useState<string | null>(null)
  const [kind, setKind] = useState<string | null>(null)
  const [namespace, setNamespace] = useState<string | null>(null)
  const [status, setStatus] = useState<string[]>([])
  const [apiVersion, setApiVersion] = useState<string | null>(null)
  const [search, setSearch] = useState<string>("")
  const [page, setPage] = useState(1)
  const [selectedResource, setSelectedResource] = useState<any | null>(null)

  // Fetch repositories for filter dropdown
  const {
    data: repositoriesData,
    isLoading: isLoadingRepos,
    isError: isErrorRepos,
  } = useQuery({
    queryKey: ["repositories"],
    queryFn: () =>
      RepositoriesService.repositoriesReadRepositories({
        query: { limit: 1000 },
      }),
  })

  // Fetch resources with filters and pagination
  const {
    data: resourcesData,
    isLoading: isLoadingResources,
    isError: isErrorResources,
  } = useQuery({
    queryKey: [
      "kubernetes-resources",
      repositoryId,
      kind,
      namespace,
      status.join(","),
      apiVersion,
      search,
      page,
      PAGE_SIZE,
    ],
    queryFn: () =>
      KubernetesService.kubernetesListKubernetesResources({
        query: {
          repository_id: repositoryId || undefined,
          kind: kind || undefined,
          namespace: namespace || undefined,
          status: status.length ? status.join(",") : undefined,
          api_version: apiVersion || undefined,
          skip: (page - 1) * PAGE_SIZE,
          limit: PAGE_SIZE,
        },
      }),
  })

  // Extract unique kinds, namespaces, apiVersions, statuses from resources for filter dropdowns
  const filterOptions = useMemo(() => {
    const kinds = new Set<string>()
    const namespaces = new Set<string>()
    const apiVersions = new Set<string>()
    const statuses = new Set<string>()
    for (const r of resourcesData?.data?.data || []) {
      if (r.kind) kinds.add(r.kind)
      if (r.namespace) namespaces.add(r.namespace)
      if (r.api_version) apiVersions.add(r.api_version)
      if (r.status) statuses.add(r.status)
    }
    return {
      kinds: Array.from(kinds),
      namespaces: Array.from(namespaces),
      apiVersions: Array.from(apiVersions),
      statuses: Array.from(statuses),
    }
  }, [resourcesData])

  // Handlers for filters
  const handleRepositoryChange = (id: string | null) => {
    setRepositoryId(id)
    setPage(1)
  }
  const handleKindChange = (k: string | null) => {
    setKind(k)
    setPage(1)
  }
  const handleNamespaceChange = (ns: string | null) => {
    setNamespace(ns)
    setPage(1)
  }
  const handleStatusChange = (s: string[]) => {
    setStatus(s)
    setPage(1)
  }
  const handleApiVersionChange = (v: string | null) => {
    setApiVersion(v)
    setPage(1)
  }
  const handleSearchChange = (s: string) => {
    setSearch(s)
    setPage(1)
  }
  const handlePageChange = (p: number) => setPage(p)

  // Table row click handler
  const handleRowClick = (resource: any) => setSelectedResource(resource)
  const handleDrawerClose = () => setSelectedResource(null)

  // Loading and error states
  if (isLoadingRepos || isLoadingResources) {
    return (
      <div style={{ padding: 32 }}>
        <h1>Kubernetes Resources Dashboard</h1>
        <p>Loading...</p>
      </div>
    )
  }
  if (isErrorRepos || isErrorResources) {
    return (
      <div style={{ padding: 32 }}>
        <h1>Kubernetes Resources Dashboard</h1>
        <p style={{ color: "red" }}>Error loading data.</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 32 }}>
      <h1>Kubernetes Resources Dashboard</h1>
      <ResourceFilters
        repositories={repositoriesData?.data?.data || []}
        filterOptions={filterOptions}
        repositoryId={repositoryId}
        kind={kind}
        namespace={namespace}
        status={status}
        apiVersion={apiVersion}
        search={search}
        onRepositoryChange={handleRepositoryChange}
        onKindChange={handleKindChange}
        onNamespaceChange={handleNamespaceChange}
        onStatusChange={handleStatusChange}
        onApiVersionChange={handleApiVersionChange}
        onSearchChange={handleSearchChange}
      />
      <ResourceSummary resources={resourcesData?.data?.data ?? []} />
      <ResourceTable
        resources={resourcesData?.data?.data ?? []}
        count={resourcesData?.data?.count ?? 0}
        page={page}
        pageSize={PAGE_SIZE}
        onPageChange={handlePageChange}
        onRowClick={handleRowClick}
      />
      <ResourceDetailsDrawer
        open={!!selectedResource}
        onClose={handleDrawerClose}
        resource={selectedResource}
      />
    </div>
  )
}

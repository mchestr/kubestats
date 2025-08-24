import { useQuery } from "@tanstack/react-query"
import type React from "react"
import { useMemo, useState } from "react"
import { Kubernetes, Repositories } from "../../client/sdk.gen"
import { RepositoryDrilldownDrawer } from "./RepositoryDrilldownDrawer"
import { ResourceFilters } from "./ResourceFilters"
import { ResourceSummary } from "./ResourceSummary"
import { ResourceTable } from "./ResourceTable"

const PAGE_SIZE = 25

export const ResourceDashboard: React.FC = () => {
  // Filter and pagination state
  const [repositoryId, setRepositoryId] = useState<string | null>(null)
  const [kind, setKind] = useState<string | null>(null)
  const [apiVersion, setApiVersion] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [selectedGroup, setSelectedGroup] = useState<any | null>(null)

  // Fetch repositories for filter dropdown
  const {
    data: repositoriesData,
    isLoading: isLoadingRepos,
    isError: isErrorRepos,
  } = useQuery({
    queryKey: ["repositories"],
    queryFn: () =>
      Repositories.repositoriesReadRepositories({
        query: { limit: 1000 },
      }),
  })

  // Fetch grouped resources with filters and pagination
  const {
    data: groupedData,
    isLoading: isLoadingResources,
    isError: isErrorResources,
  } = useQuery({
    queryKey: [
      "kubernetes-grouped-resources",
      repositoryId,
      kind,
      apiVersion,
      page,
      PAGE_SIZE,
    ],
    queryFn: () =>
      Kubernetes.kubernetesListGroupedKubernetesResources({
        query: {
          repository_id: repositoryId || undefined,
          kind: kind || undefined,
          api_version: apiVersion || undefined,
          skip: (page - 1) * PAGE_SIZE,
          limit: PAGE_SIZE,
        },
      }),
  })

  // Extract unique kinds and apiVersions for filter dropdowns
  const filterOptions = useMemo(() => {
    const kinds = new Set<string>()
    const apiVersions = new Set<string>()
    for (const g of groupedData?.data?.data || []) {
      if (g.kind) kinds.add(g.kind)
    }
    return {
      kinds: Array.from(kinds),
      namespaces: [], // placeholder for prop shape
      apiVersions: Array.from(apiVersions),
      statuses: [], // placeholder for prop shape
    }
  }, [groupedData])

  // Prepare sorted resources by total_count descending
  const sortedResources = useMemo(() => {
    return (groupedData?.data?.data ?? [])
      .slice()
      .sort((a, b) => (b.total_count ?? 0) - (a.total_count ?? 0))
  }, [groupedData])

  // Handlers for filters
  const handleRepositoryChange = (id: string | null) => {
    setRepositoryId(id)
    setPage(1)
  }
  const handleKindChange = (k: string | null) => {
    setKind(k)
    setPage(1)
  }
  const handleApiVersionChange = (v: string | null) => {
    setApiVersion(v)
    setPage(1)
  }
  const handlePageChange = (p: number) => setPage(p)

  // Table row click handler (for drill-down)
  const handleRowClick = (group: any) => setSelectedGroup(group)
  const handleDrawerClose = () => setSelectedGroup(null)

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
        namespace={null}
        status={[]}
        apiVersion={apiVersion}
        search={""}
        onRepositoryChange={handleRepositoryChange}
        onKindChange={handleKindChange}
        onNamespaceChange={() => {}}
        onStatusChange={() => {}}
        onApiVersionChange={handleApiVersionChange}
        onSearchChange={() => {}}
      />
      <ResourceSummary
        resources={sortedResources}
        total={groupedData?.data?.count ?? 0}
      />
      <ResourceTable
        resources={sortedResources}
        count={groupedData?.data?.count ?? 0}
        page={page}
        pageSize={PAGE_SIZE}
        onPageChange={handlePageChange}
        onRowClick={handleRowClick}
      />
      <RepositoryDrilldownDrawer
        open={!!selectedGroup}
        onClose={handleDrawerClose}
        group={selectedGroup}
      />
    </div>
  )
}

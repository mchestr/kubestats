import {
  Box,
  Button,
  Card,
  Container,
  Flex,
  HStack,
  Heading,
  IconButton,
  Stack,
  Table,
  Text,
} from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink } from "@tanstack/react-router"
import { useMemo, useState } from "react"
import {
  FiCheck,
  FiChevronDown,
  FiChevronUp,
  FiEye,
  FiGitBranch,
  FiHardDrive,
  FiLayers,
  FiMoreVertical,
  FiRefreshCw,
  FiShield,
  FiStar,
  FiTrash2,
} from "react-icons/fi"

import type { RepositoriesPublic } from "../../client"
import { Repositories } from "../../client"
import useAuth from "../../hooks/useAuth"
import useCustomToast from "../../hooks/useCustomToast"
import { DeleteConfirmationModal } from "../ui/delete-confirmation-modal"
import { MenuContent, MenuItem, MenuRoot, MenuTrigger } from "../ui/menu"
import { Pagination } from "../ui/pagination"
import {
  type RepositoryFilters,
  RepositoryFiltersComponent,
} from "../ui/repository-filters"
import { SyncButton } from "../ui/sync-button"
import { getSyncStatusBadge } from "./repository-utils"

// Types for sorting
type SortField =
  | "name"
  | "stars"
  | "size"
  | "resource_count"
  | "sync_status"
  | "last_sync_at"
  | "discovered_at"
type SortDirection = "asc" | "desc"

interface SortState {
  field: SortField | null
  direction: SortDirection
}

function RepositoriesPage() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { user } = useAuth()

  // State for filters, pagination, and sorting
  const [filters, setFilters] = useState<RepositoryFilters>({
    search: "",
    syncStatus: "",
  })
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)
  const [sortState, setSortState] = useState<SortState>({
    field: null,
    direction: "asc",
  })

  // State for delete confirmation modal
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [repositoryToDelete, setRepositoryToDelete] = useState<{
    id: string
    name: string
  } | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const {
    data: repositories,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["repositories"],
    queryFn: () =>
      Repositories.repositoriesReadRepositories({
        query: { limit: 1000 },
      }),
  })

  const repositoryData = repositories?.data as RepositoriesPublic | undefined

  // Filter, sort, and paginate repositories
  const { paginatedRepositories, totalFilteredItems } = useMemo(() => {
    const allRepos = repositoryData?.data || []

    // Apply filters
    const filtered = allRepos.filter((repo) => {
      // Search filter
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase()
        const matchesName = repo.name.toLowerCase().includes(searchTerm)
        const matchesFullName = repo.full_name
          .toLowerCase()
          .includes(searchTerm)
        if (!matchesName && !matchesFullName) {
          return false
        }
      }

      // Sync status filter
      if (filters.syncStatus) {
        const repoSyncStatus = repo.sync_status || "pending"
        if (repoSyncStatus !== filters.syncStatus) {
          return false
        }
      }

      return true
    })

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      if (!sortState.field) return 0

      let aField: any = null
      let bField: any = null

      switch (sortState.field) {
        case "name":
          aField = a.name?.toLowerCase() || ""
          bField = b.name?.toLowerCase() || ""
          break
        case "stars":
          aField = a.latest_metrics?.stars_count || 0
          bField = b.latest_metrics?.stars_count || 0
          break
        case "size":
          aField = a.latest_metrics?.size || 0
          bField = b.latest_metrics?.size || 0
          break
        case "resource_count":
          aField = a.last_scan_total_resources || 0
          bField = b.last_scan_total_resources || 0
          break
        case "sync_status":
          aField = a.sync_status || "pending"
          bField = b.sync_status || "pending"
          break
        case "last_sync_at":
          aField = a.last_sync_at ? new Date(a.last_sync_at) : new Date(0)
          bField = b.last_sync_at ? new Date(b.last_sync_at) : new Date(0)
          break
        case "discovered_at":
          aField = new Date(a.discovered_at)
          bField = new Date(b.discovered_at)
          break
        default:
          return 0
      }

      // Handle null/undefined values
      if (aField == null && bField == null) return 0
      if (aField == null) return sortState.direction === "asc" ? 1 : -1
      if (bField == null) return sortState.direction === "asc" ? -1 : 1

      if (aField < bField) {
        return sortState.direction === "asc" ? -1 : 1
      }
      if (aField > bField) {
        return sortState.direction === "asc" ? 1 : -1
      }
      return 0
    })

    // Apply pagination
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    const paginated = sorted.slice(startIndex, endIndex)

    return {
      paginatedRepositories: paginated,
      totalFilteredItems: sorted.length,
    }
  }, [repositoryData?.data, filters, sortState, currentPage, itemsPerPage])

  // Handle pagination changes
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage)
    setCurrentPage(1) // Reset to first page when changing page size
  }

  // Handle filter changes
  const handleFiltersChange = (newFilters: RepositoryFilters) => {
    setFilters(newFilters)
    setCurrentPage(1) // Reset to first page when filtering
  }

  // Handle sorting
  const handleSort = (field: SortField) => {
    let direction: SortDirection = "asc"
    if (sortState.field === field && sortState.direction === "asc") {
      direction = "desc"
    }
    setSortState({ field, direction })
  }

  // Render sort icon for table headers
  const renderSortIcon = (field: SortField) => {
    if (sortState.field !== field) {
      return (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleSort(field)}
          aria-label={`Sort by ${field}`}
          p={1}
          minW="auto"
          h="auto"
        >
          <FiChevronUp opacity={0.3} />
        </Button>
      )
    }

    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleSort(field)}
        aria-label={`Sort by ${field}`}
        p={1}
        minW="auto"
        h="auto"
        colorPalette="blue"
      >
        {sortState.direction === "asc" ? <FiChevronUp /> : <FiChevronDown />}
      </Button>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`
    }
    return num.toString()
  }

  const formatSize = (sizeInKB: number) => {
    if (sizeInKB >= 1000000) {
      return `${(sizeInKB / 1000000).toFixed(1)} GB`
    }
    if (sizeInKB >= 1000) {
      return `${(sizeInKB / 1000).toFixed(1)} MB`
    }
    return `${sizeInKB} KB`
  }

  const handleTriggerSync = async (repositoryId: string) => {
    try {
      await Repositories.repositoriesTriggerRepositorySyncSingle({
        path: { repository_id: repositoryId },
      })
      showSuccessToast("Sync triggered for repository")
      // Refresh the repositories list
      await queryClient.invalidateQueries({ queryKey: ["repositories"] })
    } catch (error) {
      showErrorToast("Failed to trigger sync")
    }
  }

  const handleTriggerAllSync = async () => {
    try {
      await Repositories.repositoriesTriggerRepositorySyncAll({})
      showSuccessToast("Sync triggered for all repositories")
      // Refresh the repositories list
      await queryClient.invalidateQueries({ queryKey: ["repositories"] })
    } catch (error) {
      showErrorToast("Failed to trigger sync for all repositories")
    }
  }

  const handleBlockRepository = async (repositoryId: string) => {
    try {
      await Repositories.repositoriesBlockRepository({
        path: { repository_id: repositoryId },
      })
      showSuccessToast("Repository has been blocked")
      // Refresh the repositories list
      await queryClient.invalidateQueries({ queryKey: ["repositories"] })
    } catch (error) {
      showErrorToast("Failed to block repository")
    }
  }

  const handleApproveRepository = async (repositoryId: string) => {
    try {
      await Repositories.repositoriesApproveRepository({
        path: { repository_id: repositoryId },
      })
      showSuccessToast("Repository has been approved")
      // Refresh the repositories list
      await queryClient.invalidateQueries({ queryKey: ["repositories"] })
    } catch (error) {
      showErrorToast("Failed to approve repository")
    }
  }

  const handleDeleteRepositoryClick = (
    repositoryId: string,
    repositoryName: string,
  ) => {
    setRepositoryToDelete({ id: repositoryId, name: repositoryName })
    setDeleteModalOpen(true)
  }

  const handleDeleteRepository = async () => {
    if (!repositoryToDelete) return

    setIsDeleting(true)
    try {
      await Repositories.repositoriesDeleteRepository({
        path: { repository_id: repositoryToDelete.id },
      })
      showSuccessToast(`Repository ${repositoryToDelete.name} has been deleted`)
      // Refresh the repositories list
      await queryClient.invalidateQueries({ queryKey: ["repositories"] })
      setDeleteModalOpen(false)
      setRepositoryToDelete(null)
    } catch (error) {
      showErrorToast("Failed to delete repository")
    } finally {
      setIsDeleting(false)
    }
  }

  const handleDeleteModalClose = () => {
    if (!isDeleting) {
      setDeleteModalOpen(false)
      setRepositoryToDelete(null)
    }
  }

  if (isLoading) {
    return (
      <Container maxW="full">
        <Text>Loading repositories...</Text>
      </Container>
    )
  }

  if (isError) {
    return (
      <Container maxW="full">
        <Text color="red.500">Error loading repositories</Text>
      </Container>
    )
  }

  return (
    <Container maxW="full">
      <Stack gap={6}>
        <Flex justifyContent="space-between" alignItems="center">
          <Heading size="lg">
            <HStack gap={2}>
              <FiGitBranch />
              <Text>Repositories</Text>
            </HStack>
          </Heading>
          <SyncButton onSync={() => handleTriggerAllSync()} colorPalette="blue">
            Sync All
          </SyncButton>
        </Flex>

        <Text color="gray.600">
          View and manage repository synchronization status. Repositories are
          automatically synced periodically, but you can trigger manual syncs as
          needed.
        </Text>

        {/* Filters integrated with table */}
        <Stack gap={0}>
          <RepositoryFiltersComponent
            filters={filters}
            onFiltersChange={handleFiltersChange}
          />

          <Card.Root borderTopRadius="none">
            <Table.Root variant="outline">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>
                    <HStack gap={2}>
                      <Text>Repository</Text>
                      {renderSortIcon("name")}
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>
                    <HStack gap={2}>
                      <FiStar size={14} />
                      <Text>Stars</Text>
                      {renderSortIcon("stars")}
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>
                    <HStack gap={2}>
                      <FiHardDrive size={14} />
                      <Text>Size</Text>
                      {renderSortIcon("size")}
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>
                    <HStack gap={2}>
                      <FiLayers size={14} />
                      <Text>Resources</Text>
                      {renderSortIcon("resource_count")}
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>
                    <HStack gap={2}>
                      <Text>Sync Status</Text>
                      {renderSortIcon("sync_status")}
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>
                    <HStack gap={2}>
                      <Text>Last Sync</Text>
                      {renderSortIcon("last_sync_at")}
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>
                    <HStack gap={2}>
                      <Text>Discovered</Text>
                      {renderSortIcon("discovered_at")}
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>Actions</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {paginatedRepositories.map((repo) => (
                  <Table.Row key={repo.id}>
                    <Table.Cell>
                      <Stack gap={1}>
                        <RouterLink
                          to="/repositories/$repositoryId"
                          params={{ repositoryId: repo.id }}
                        >
                          <Text
                            fontWeight="medium"
                            color="blue.500"
                            _hover={{
                              color: "blue.600",
                              textDecoration: "underline",
                            }}
                            cursor="pointer"
                          >
                            {repo.name}
                          </Text>
                        </RouterLink>
                        <Text fontSize="sm" color="fg.muted">
                          {repo.full_name}
                        </Text>
                      </Stack>
                    </Table.Cell>
                    <Table.Cell>
                      <HStack gap={1}>
                        <FiStar size={12} color="#f59e0b" />
                        <Text fontSize="sm">
                          {repo.latest_metrics?.stars_count
                            ? formatNumber(repo.latest_metrics.stars_count)
                            : "0"}
                        </Text>
                      </HStack>
                    </Table.Cell>
                    <Table.Cell>
                      <HStack gap={1}>
                        <FiHardDrive size={12} color="#8b5cf6" />
                        <Text fontSize="sm">
                          {repo.latest_metrics?.size
                            ? formatSize(repo.latest_metrics.size)
                            : "0 KB"}
                        </Text>
                      </HStack>
                    </Table.Cell>
                    <Table.Cell>
                      <HStack gap={1}>
                        <FiLayers size={12} color="#10b981" />
                        <Text fontSize="sm">
                          {repo.last_scan_total_resources != null
                            ? formatNumber(repo.last_scan_total_resources)
                            : "N/A"}
                        </Text>
                      </HStack>
                    </Table.Cell>
                    <Table.Cell>{getSyncStatusBadge(repo)}</Table.Cell>
                    <Table.Cell>
                      <Text fontSize="sm" color="fg.muted">
                        {repo.last_sync_at
                          ? formatDate(repo.last_sync_at)
                          : "Never"}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text fontSize="sm" color="fg.muted">
                        {formatDate(repo.discovered_at)}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <MenuRoot>
                        <MenuTrigger asChild>
                          <IconButton
                            aria-label="More actions"
                            variant="outline"
                            size="sm"
                            colorPalette="gray"
                          >
                            <FiMoreVertical />
                          </IconButton>
                        </MenuTrigger>
                        <MenuContent>
                          <MenuItem
                            value="view"
                            gap={2}
                            py={2}
                            style={{ cursor: "pointer" }}
                            asChild
                          >
                            <RouterLink
                              to="/repositories/$repositoryId"
                              params={{ repositoryId: repo.id }}
                            >
                              <FiEye />
                              <Text>View</Text>
                            </RouterLink>
                          </MenuItem>
                          <MenuItem
                            value="sync"
                            gap={2}
                            py={2}
                            onClick={() => handleTriggerSync(repo.id)}
                            style={{ cursor: "pointer" }}
                          >
                            <FiRefreshCw />
                            <Text>Sync</Text>
                          </MenuItem>
                          {user?.is_superuser && (
                            <>
                              {repo.sync_status !== "blocked" &&
                                repo.sync_status !== "pending_approval" && (
                                  <MenuItem
                                    value="block"
                                    gap={2}
                                    py={2}
                                    onClick={() =>
                                      handleBlockRepository(repo.id)
                                    }
                                    style={{ cursor: "pointer" }}
                                  >
                                    <FiShield />
                                    <Text>Block</Text>
                                  </MenuItem>
                                )}
                              {(repo.sync_status === "blocked" ||
                                repo.sync_status === "pending_approval") && (
                                <MenuItem
                                  value="approve"
                                  gap={2}
                                  py={2}
                                  onClick={() =>
                                    handleApproveRepository(repo.id)
                                  }
                                  style={{ cursor: "pointer" }}
                                >
                                  <FiCheck />
                                  <Text>Approve</Text>
                                </MenuItem>
                              )}
                              <MenuItem
                                value="delete"
                                gap={2}
                                py={2}
                                onClick={() =>
                                  handleDeleteRepositoryClick(
                                    repo.id,
                                    repo.full_name,
                                  )
                                }
                                style={{ cursor: "pointer" }}
                                colorPalette="red"
                              >
                                <FiTrash2 />
                                <Text>Delete</Text>
                              </MenuItem>
                            </>
                          )}
                        </MenuContent>
                      </MenuRoot>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>

            {paginatedRepositories.length === 0 && (
              <Box p={8} textAlign="center">
                <Text color="fg.muted">
                  {totalFilteredItems === 0 &&
                  !filters.search &&
                  !filters.syncStatus
                    ? "No repositories found"
                    : "No repositories match the current filters"}
                </Text>
                <Text fontSize="sm" color="fg.muted" mt={2}>
                  {totalFilteredItems === 0 &&
                  !filters.search &&
                  !filters.syncStatus
                    ? "Repositories will appear here once they are discovered"
                    : "Try adjusting your search criteria or filters"}
                </Text>
              </Box>
            )}
          </Card.Root>

          {/* Pagination */}
          {totalFilteredItems > 0 && (
            <Pagination
              currentPage={currentPage}
              totalItems={totalFilteredItems}
              itemsPerPage={itemsPerPage}
              onPageChange={handlePageChange}
              onItemsPerPageChange={handleItemsPerPageChange}
            />
          )}

          {/* Summary */}
          <Box textAlign="center">
            <Text fontSize="sm" color="fg.muted">
              Showing {paginatedRepositories.length} of {totalFilteredItems}{" "}
              filtered • {repositoryData?.count ?? 0} total repositories
            </Text>
          </Box>
        </Stack>
      </Stack>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={handleDeleteModalClose}
        onConfirm={handleDeleteRepository}
        title="Delete Repository"
        description="Are you sure you want to delete this repository? This will permanently remove all associated data."
        itemName={repositoryToDelete?.name ?? ""}
        isLoading={isDeleting}
      />
    </Container>
  )
}

export default RepositoriesPage

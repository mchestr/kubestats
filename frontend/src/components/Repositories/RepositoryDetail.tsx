import {
  Badge,
  Box,
  Breadcrumb,
  Button,
  Card,
  Container,
  Flex,
  Grid,
  HStack,
  Heading,
  Skeleton,
  Stack,
  Text,
} from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink, useParams } from "@tanstack/react-router"
import {
  FiArrowLeft,
  FiCalendar,
  FiCheck,
  FiGitBranch,
  FiShield,
  FiTag,
} from "react-icons/fi"

import type { RepositoryMetricsPublic, RepositoryPublic } from "../../client"
import { RepositoriesService } from "../../client"
import useAuth from "../../hooks/useAuth"
import useCustomToast from "../../hooks/useCustomToast"
import { SyncButton } from "../ui/sync-button"
import MetricsCards from "./MetricsCards"
import MetricsChart from "./MetricsChart"
import RepositoryInfo from "./RepositoryInfo"
import { getSyncStatusBadge } from "./repository-utils"

function RepositoryDetail() {
  console.log("Rendering RepositoryDetail component")
  const { repositoryId } = useParams({
    from: "/_layout/repositories/$repositoryId",
  })
  console.log("Repository ID:", repositoryId)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { user } = useAuth()

  const {
    data: repository,
    isLoading: isLoadingRepository,
    isError: isRepositoryError,
  } = useQuery({
    queryKey: ["repository", repositoryId],
    queryFn: () =>
      RepositoriesService.repositoriesReadRepository({
        path: { repository_id: repositoryId },
      }),
  })

  const {
    data: metricsData,
    isLoading: isLoadingMetrics,
    isError: isMetricsError,
  } = useQuery({
    queryKey: ["repository-metrics", repositoryId],
    queryFn: () =>
      RepositoriesService.repositoriesReadRepositoryMetrics({
        path: { repository_id: repositoryId },
      }),
    enabled: !!repositoryId,
  })

  const repositoryData = repository?.data as RepositoryPublic | undefined

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const handleTriggerSync = async () => {
    if (!repositoryId) return

    try {
      await RepositoriesService.repositoriesTriggerRepositorySyncSingle({
        path: { repository_id: repositoryId },
      })
      showSuccessToast("Sync triggered for repository")
      // Refresh the repository data
      await queryClient.invalidateQueries({
        queryKey: ["repository", repositoryId],
      })
    } catch (error) {
      showErrorToast("Failed to trigger sync")
    }
  }

  const handleBlockRepository = async () => {
    if (!repositoryId) return

    try {
      await RepositoriesService.repositoriesBlockRepository({
        path: { repository_id: repositoryId },
      })
      showSuccessToast("Repository blocked successfully")
      // Refresh the repository data
      await queryClient.invalidateQueries({
        queryKey: ["repository", repositoryId],
      })
    } catch (error) {
      showErrorToast("Failed to block repository")
    }
  }

  const handleApproveRepository = async () => {
    if (!repositoryId) return

    try {
      await RepositoriesService.repositoriesApproveRepository({
        path: { repository_id: repositoryId },
      })
      showSuccessToast("Repository approved successfully")
      // Refresh the repository data
      await queryClient.invalidateQueries({
        queryKey: ["repository", repositoryId],
      })
    } catch (error) {
      showErrorToast("Failed to approve repository")
    }
  }

  if (isLoadingRepository) {
    return (
      <Container maxW="full">
        <Stack gap={6}>
          <Skeleton height="60px" />
          <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
            <Skeleton height="100px" />
            <Skeleton height="100px" />
            <Skeleton height="100px" />
            <Skeleton height="100px" />
          </Grid>
          <Skeleton height="400px" />
        </Stack>
      </Container>
    )
  }

  if (isRepositoryError || !repositoryData) {
    return (
      <Container maxW="full">
        <Stack gap={6}>
          <Breadcrumb.Root>
            <Breadcrumb.List>
              <Breadcrumb.Item>
                <Breadcrumb.Link asChild>
                  <RouterLink to="/repositories">Repositories</RouterLink>
                </Breadcrumb.Link>
              </Breadcrumb.Item>
              <Breadcrumb.Separator />
              <Breadcrumb.Item>
                <Text>Error</Text>
              </Breadcrumb.Item>
            </Breadcrumb.List>
          </Breadcrumb.Root>

          <Card.Root>
            <Card.Body textAlign="center" py={12}>
              <Text color="red.500" fontSize="lg" fontWeight="medium">
                Repository not found
              </Text>
              <Text color="fg.muted" mt={2}>
                The repository you're looking for doesn't exist or you don't
                have access to it.
              </Text>
              <Button mt={4} asChild>
                <RouterLink to="/repositories">
                  <FiArrowLeft />
                  Back to Repositories
                </RouterLink>
              </Button>
            </Card.Body>
          </Card.Root>
        </Stack>
      </Container>
    )
  }

  return (
    <Container maxW="full">
      <Stack gap={6}>
        {/* Breadcrumb Navigation */}
        <Breadcrumb.Root>
          <Breadcrumb.List>
            <Breadcrumb.Item>
              <Breadcrumb.Link asChild>
                <RouterLink to="/repositories">Repositories</RouterLink>
              </Breadcrumb.Link>
            </Breadcrumb.Item>
            <Breadcrumb.Separator />
            <Breadcrumb.Item>
              <Text>{repositoryData.name}</Text>
            </Breadcrumb.Item>
          </Breadcrumb.List>
        </Breadcrumb.Root>

        {/* Repository Header */}
        <Card.Root>
          <Card.Body>
            <Flex justifyContent="space-between" alignItems="flex-start">
              <Stack gap={3} flex={1}>
                <Flex alignItems="center" gap={3} flexWrap="wrap">
                  <Heading size="xl">
                    <HStack gap={2}>
                      <FiGitBranch />
                      <Text>{repositoryData.name}</Text>
                    </HStack>
                  </Heading>
                  {repositoryData.language && (
                    <Badge variant="outline" colorPalette="blue">
                      {repositoryData.language}
                    </Badge>
                  )}
                  {getSyncStatusBadge(repositoryData)}
                </Flex>

                <Text color="fg.muted" fontSize="lg">
                  {repositoryData.full_name}
                </Text>

                {repositoryData.description && (
                  <Text color="fg.subtle" maxW="2xl">
                    {repositoryData.description}
                  </Text>
                )}

                {repositoryData.topics && repositoryData.topics.length > 0 && (
                  <Flex gap={2} flexWrap="wrap" alignItems="center">
                    <FiTag size={14} />
                    {repositoryData.topics.map((topic) => (
                      <Badge key={topic} variant="subtle" size="sm">
                        {topic}
                      </Badge>
                    ))}
                  </Flex>
                )}
              </Stack>

              <HStack gap={2}>
                {user?.is_superuser && (
                  <>
                    {repositoryData.sync_status === "blocked" && (
                      <Button
                        onClick={handleApproveRepository}
                        colorPalette="green"
                        size="sm"
                      >
                        <FiCheck />
                        Approve
                      </Button>
                    )}
                    {repositoryData.sync_status === "pending_approval" && (
                      <>
                        <Button
                          onClick={handleApproveRepository}
                          colorPalette="green"
                          size="sm"
                        >
                          <FiCheck />
                          Approve
                        </Button>
                        <Button
                          onClick={handleBlockRepository}
                          colorPalette="red"
                          size="sm"
                        >
                          <FiShield />
                          Block
                        </Button>
                      </>
                    )}
                    {(repositoryData.sync_status === "success" ||
                      repositoryData.sync_status === "error" ||
                      repositoryData.sync_status === "pending") && (
                      <Button
                        onClick={handleBlockRepository}
                        colorPalette="red"
                        size="sm"
                      >
                        <FiShield />
                        Block
                      </Button>
                    )}
                  </>
                )}
                <SyncButton
                  onSync={() => handleTriggerSync()}
                  colorPalette="blue"
                >
                  Sync
                </SyncButton>
              </HStack>
            </Flex>
          </Card.Body>
        </Card.Root>

        {/* Metrics Cards */}
        <MetricsCards repository={repositoryData} />

        {/* Charts Section */}
        <Card.Root>
          <Card.Header>
            <Heading size="lg">Metrics Over Time</Heading>
            <Text color="fg.muted">
              Historical view of repository metrics and activity
            </Text>
          </Card.Header>
          <Card.Body>
            {isLoadingMetrics ? (
              <Skeleton height="400px" />
            ) : isMetricsError || !metricsData?.data ? (
              <Box textAlign="center" py={12}>
                <Text color="fg.muted">Unable to load metrics data</Text>
              </Box>
            ) : (
              <MetricsChart metrics={ (metricsData.data as {data: any[]})?.data } />
            )}
          </Card.Body>
        </Card.Root>

        {/* Repository Information */}
        <RepositoryInfo repository={repositoryData} />

        {/* Sync Information */}
        {(repositoryData.last_sync_at || repositoryData.sync_error) && (
          <Card.Root>
            <Card.Header>
              <Heading size="lg">Sync Information</Heading>
            </Card.Header>
            <Card.Body>
              <Stack gap={4}>
                {repositoryData.last_sync_at && (
                  <Flex alignItems="center" gap={2}>
                    <FiCalendar size={16} />
                    <Text fontWeight="medium">Last Sync:</Text>
                    <Text color="fg.muted">
                      {formatDate(repositoryData.last_sync_at)}
                    </Text>
                  </Flex>
                )}

                {repositoryData.sync_error && (
                  <Box>
                    <Text fontWeight="medium" color="red.500" mb={2}>
                      Sync Error:
                    </Text>
                    <Text
                      color="fg.muted"
                      fontFamily="mono"
                      fontSize="sm"
                      bg="bg.subtle"
                      p={3}
                      rounded="md"
                    >
                      {repositoryData.sync_error}
                    </Text>
                  </Box>
                )}

                {repositoryData.working_directory_path && (
                  <Flex alignItems="center" gap={2}>
                    <Text fontWeight="medium">Working Directory:</Text>
                    <Text color="fg.muted" fontFamily="mono" fontSize="sm">
                      {repositoryData.working_directory_path}
                    </Text>
                  </Flex>
                )}
              </Stack>
            </Card.Body>
          </Card.Root>
        )}
      </Stack>
    </Container>
  )
}

export default RepositoryDetail

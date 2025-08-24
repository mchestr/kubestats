import {
  Box,
  Card,
  Grid,
  HStack,
  Heading,
  Link,
  Stack,
  Stat,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { Link as TanstackLink } from "@tanstack/react-router"

import { Admin, Repositories } from "@/client"

interface DatabaseStats {
  table_counts: {
    repositories: number
    repository_metrics: number
    kubernetes_resources: number
    kubernetes_resource_events: number
  }
  recent_stats: {
    new_repositories_last_7_days: number
    resource_changes_last_7_days: number
  }
  sync_run_stats: {
    total_sync_runs: number
    recent_sync_runs: Array<{
      repository_name: string
      repository_full_name: string
      event_count: number
      started_at: string | null
      completed_at: string | null
      duration_milliseconds: number | null
    }>
    event_type_breakdown: Record<string, number>
  }
  total_records: number
}

interface RecentActiveRepository {
  repository_id: string
  name: string
  full_name: string
  owner: string
  description: string | null
  total_events: number
  last_activity: string | null
  event_breakdown: Record<string, number>
}

interface RecentActiveRepositories {
  recent_active_repositories: RecentActiveRepository[]
  period_days: number
  cutoff_date: string
}

function getDatabaseStatsQueryOptions() {
  return {
    queryFn: async () => {
      const response = await Admin.adminGetDatabaseStats()
      return response.data as unknown as DatabaseStats
    },
    queryKey: ["admin", "database-stats"],
    refetchInterval: 30000, // Refresh every 30 seconds
  }
}

function getRecentActiveRepositoriesQueryOptions() {
  return {
    queryFn: async () => {
      const response =
        await Repositories.repositoriesGetRecentActiveRepositories()
      return response.data as unknown as RecentActiveRepositories
    },
    queryKey: ["repositories", "recent-active-repositories"],
    refetchInterval: 30000, // Refresh every 30 seconds
  }
}

function TableCountsGrid({ data }: { data: DatabaseStats["table_counts"] }) {
  const tableData = [
    { label: "Repositories", count: data.repositories, color: "green" },
    {
      label: "Repository Metrics",
      count: data.repository_metrics,
      color: "purple",
    },
    {
      label: "Kubernetes Resources",
      count: data.kubernetes_resources,
      color: "orange",
    },
    {
      label: "Resource Events",
      count: data.kubernetes_resource_events,
      color: "red",
    },
  ]

  return (
    <Grid
      templateColumns={{
        base: "1fr",
        md: "repeat(2, 1fr)",
        lg: "repeat(4, 1fr)",
      }}
      gap={4}
    >
      {tableData.map((table) => (
        <Card.Root key={table.label} p={4}>
          <Card.Body>
            <Stat.Root>
              <Stat.Label fontSize="sm" color="gray.600">
                {table.label}
              </Stat.Label>
              <Stat.ValueText
                fontSize="2xl"
                fontWeight="bold"
                color={`${table.color}.500`}
              >
                {table.count.toLocaleString()}
              </Stat.ValueText>
            </Stat.Root>
          </Card.Body>
        </Card.Root>
      ))}
    </Grid>
  )
}

function RecentStatsGrid({ data }: { data: DatabaseStats["recent_stats"] }) {
  const statsData = [
    {
      label: "New Repositories",
      sublabel: "Last 7 days",
      count: data.new_repositories_last_7_days,
      color: "blue",
      icon: "📊",
    },
    {
      label: "Resource Changes",
      sublabel: "Last 7 days",
      count: data.resource_changes_last_7_days,
      color: "green",
      icon: "🔄",
    },
  ]

  return (
    <Grid
      templateColumns={{
        base: "1fr",
        md: "repeat(2, 1fr)",
      }}
      gap={6}
    >
      {statsData.map((stat) => (
        <Card.Root key={stat.label} p={6}>
          <Card.Body>
            <HStack justify="space-between" align="start">
              <VStack align="start" gap={1}>
                <Text fontSize="sm" fontWeight="medium">
                  {stat.sublabel}
                </Text>
                <Text fontSize="lg" fontWeight="bold">
                  {stat.label}
                </Text>
                <Text fontSize="3xl" fontWeight="bold">
                  {stat.count.toLocaleString()}
                </Text>
              </VStack>
              <Text fontSize="2xl">{stat.icon}</Text>
            </HStack>
          </Card.Body>
        </Card.Root>
      ))}
    </Grid>
  )
}

function SyncRunsTable({
  data,
}: {
  data: DatabaseStats["sync_run_stats"]["recent_sync_runs"]
}) {
  const formatDuration = (milliseconds: number | null) => {
    if (!milliseconds) return "N/A"
    if (milliseconds < 1000) return `${Math.round(milliseconds)}ms`
    const seconds = milliseconds / 1000
    if (seconds < 60) return `${Math.round(seconds * 10) / 10}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    return `${Math.round(seconds / 3600)}h`
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A"
    return new Date(dateString).toLocaleString()
  }

  return (
    <Table.Root size="sm">
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>Repository</Table.ColumnHeader>
          <Table.ColumnHeader>Events</Table.ColumnHeader>
          <Table.ColumnHeader>Started</Table.ColumnHeader>
          <Table.ColumnHeader>Completed</Table.ColumnHeader>
          <Table.ColumnHeader>Duration</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {data.map((run) => (
          <Table.Row key={run.repository_full_name}>
            <Table.Cell>
              <Text
                fontFamily="mono"
                fontSize="xs"
                title={run.repository_full_name}
              >
                {run.repository_full_name}
              </Text>
            </Table.Cell>
            <Table.Cell>{run.event_count.toLocaleString()}</Table.Cell>
            <Table.Cell>
              <Text fontSize="xs">{formatDate(run.started_at)}</Text>
            </Table.Cell>
            <Table.Cell>
              <Text fontSize="xs">{formatDate(run.completed_at)}</Text>
            </Table.Cell>
            <Table.Cell>{formatDuration(run.duration_milliseconds)}</Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  )
}

function EventTypeBreakdown({ data }: { data: Record<string, number> }) {
  const eventTypes = Object.entries(data).map(([type, count]) => ({
    type,
    count,
    percentage:
      Object.values(data).reduce((sum, c) => sum + c, 0) > 0
        ? Math.round(
            (count / Object.values(data).reduce((sum, c) => sum + c, 0)) * 100,
          )
        : 0,
  }))

  const getEventTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "created":
        return "green"
      case "modified":
        return "orange"
      case "deleted":
        return "red"
      default:
        return "gray"
    }
  }

  return (
    <Grid
      templateColumns={{
        base: "1fr",
        md: "repeat(2, 1fr)",
        lg: "repeat(3, 1fr)",
      }}
      gap={4}
    >
      {eventTypes.map((event) => (
        <Card.Root key={event.type} p={3}>
          <Card.Body>
            <VStack align="center" gap={2}>
              <Box
                w={6}
                h={6}
                bg={`${getEventTypeColor(event.type)}.500`}
                borderRadius="full"
              />
              <Text
                fontWeight="bold"
                textTransform="capitalize"
                fontSize="sm"
                color="gray.700"
              >
                {event.type}
              </Text>
              <Text
                fontWeight="bold"
                fontSize="xl"
                color={`${getEventTypeColor(event.type)}.600`}
              >
                {event.count.toLocaleString()}
              </Text>
              <Text fontSize="sm" color="gray.500">
                {event.percentage}% of total
              </Text>
            </VStack>
          </Card.Body>
        </Card.Root>
      ))}
    </Grid>
  )
}

function RecentActiveRepositoriesTable({
  data,
}: {
  data: RecentActiveRepository[]
}) {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A"
    return new Date(dateString).toLocaleString()
  }

  const getEventTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "created":
        return "green"
      case "modified":
        return "orange"
      case "deleted":
        return "red"
      default:
        return "gray"
    }
  }

  // Mobile Card Layout (for screens smaller than 768px)
  const MobileLayout = () => (
    <Stack gap={4} display={{ base: "flex", md: "none" }}>
      {data.map((repo) => (
        <Card.Root key={repo.repository_id} variant="outline">
          <Card.Body p={4}>
            <VStack align="stretch" gap={3}>
              {/* Repository Info */}
              <VStack align="start" gap={1}>
                <Link
                  asChild
                  fontWeight="bold"
                  color="blue.500"
                  _hover={{ color: "blue.600" }}
                  fontSize="md"
                >
                  <TanstackLink
                    to="/repositories/$repositoryId"
                    params={{ repositoryId: repo.repository_id }}
                  >
                    {repo.name}
                  </TanstackLink>
                </Link>
                <Text fontSize="sm" color="gray.600">
                  {repo.owner}/{repo.name}
                </Text>
                {repo.description && (
                  <Text fontSize="sm" color="gray.500" lineClamp={2}>
                    {repo.description}
                  </Text>
                )}
              </VStack>

              {/* Stats Row */}
              <HStack justify="space-between" align="center">
                <VStack align="start" gap={0}>
                  <Text fontSize="xs" color="gray.500" fontWeight="medium">
                    Total Events
                  </Text>
                  <Text fontWeight="bold" fontSize="lg" color="blue.600">
                    {repo.total_events.toLocaleString()}
                  </Text>
                </VStack>
                <VStack align="end" gap={0}>
                  <Text fontSize="xs" color="gray.500" fontWeight="medium">
                    Last Activity
                  </Text>
                  <Text fontSize="xs" color="gray.600">
                    {formatDate(repo.last_activity)}
                  </Text>
                </VStack>
              </HStack>

              {/* Event Breakdown */}
              <VStack align="stretch" gap={2}>
                <Text fontSize="xs" color="gray.500" fontWeight="medium">
                  Event Breakdown
                </Text>
                <Stack gap={2}>
                  {Object.entries(repo.event_breakdown).map(([type, count]) => (
                    <HStack key={type} justify="space-between">
                      <HStack gap={2}>
                        <Box
                          w={3}
                          h={3}
                          bg={`${getEventTypeColor(type)}.500`}
                          borderRadius="full"
                        />
                        <Text fontSize="sm" fontWeight="medium">
                          {type}
                        </Text>
                      </HStack>
                      <Text fontSize="sm" fontWeight="bold">
                        {count}
                      </Text>
                    </HStack>
                  ))}
                </Stack>
              </VStack>
            </VStack>
          </Card.Body>
        </Card.Root>
      ))}
    </Stack>
  )

  // Desktop Table Layout (for screens 768px and larger)
  const DesktopLayout = () => (
    <Box overflowX="auto" display={{ base: "none", md: "block" }}>
      <Table.Root size="sm" minW="600px">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader minW="200px">Repository</Table.ColumnHeader>
            <Table.ColumnHeader minW="100px" textAlign="center">
              Total Events
            </Table.ColumnHeader>
            <Table.ColumnHeader minW="200px">
              Event Breakdown
            </Table.ColumnHeader>
            <Table.ColumnHeader minW="140px">Last Activity</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {data.map((repo) => (
            <Table.Row key={repo.repository_id}>
              <Table.Cell>
                <VStack align="start" gap={1}>
                  <Link
                    asChild
                    fontWeight="bold"
                    color="blue.500"
                    _hover={{ color: "blue.600" }}
                  >
                    <TanstackLink
                      to="/repositories/$repositoryId"
                      params={{ repositoryId: repo.repository_id }}
                    >
                      {repo.name}
                    </TanstackLink>
                  </Link>
                  <Text fontSize="xs" color="gray.600">
                    {repo.owner}/{repo.name}
                  </Text>
                  {repo.description && (
                    <Text fontSize="xs" color="gray.500" lineClamp={1}>
                      {repo.description}
                    </Text>
                  )}
                </VStack>
              </Table.Cell>
              <Table.Cell textAlign="center">
                <Text fontWeight="bold" fontSize="lg" color="blue.600">
                  {repo.total_events.toLocaleString()}
                </Text>
              </Table.Cell>
              <Table.Cell>
                <Stack gap={1} maxW="180px">
                  {Object.entries(repo.event_breakdown).map(([type, count]) => (
                    <HStack key={type} gap={2} justify="space-between">
                      <HStack gap={1}>
                        <Box
                          w={2}
                          h={2}
                          bg={`${getEventTypeColor(type)}.500`}
                          borderRadius="full"
                        />
                        <Text fontSize="xs" fontWeight="medium">
                          {type}
                        </Text>
                      </HStack>
                      <Text fontSize="xs" fontWeight="bold">
                        {count}
                      </Text>
                    </HStack>
                  ))}
                </Stack>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="xs" color="gray.600">
                  {formatDate(repo.last_activity)}
                </Text>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  )

  return (
    <>
      <MobileLayout />
      <DesktopLayout />
    </>
  )
}

export default function DatabaseStats() {
  const {
    data: databaseStatsData,
    isLoading: isLoadingDatabaseStats,
    error: errorDatabaseStats,
  } = useQuery(getDatabaseStatsQueryOptions())

  const {
    data: recentActiveRepositoriesData,
    isLoading: isLoadingRecentActiveRepositories,
    error: errorRecentActiveRepositories,
  } = useQuery(getRecentActiveRepositoriesQueryOptions())

  if (isLoadingDatabaseStats || isLoadingRecentActiveRepositories) {
    return (
      <VStack gap={6} align="start">
        <Heading size="lg">Dashboard</Heading>
        <Text>Loading database statistics...</Text>
      </VStack>
    )
  }

  if (errorDatabaseStats || errorRecentActiveRepositories) {
    return (
      <VStack gap={6} align="start">
        <Heading size="lg">Dashboard</Heading>
        <Text color="red.500">Failed to load database statistics</Text>
      </VStack>
    )
  }

  if (!databaseStatsData || !recentActiveRepositoriesData) {
    return null
  }

  return (
    <VStack gap={8} align="start" w="full">
      <VStack align="start" gap={2}>
        <Heading size="lg">Dashboard</Heading>
        <Text color="gray.600">
          Total records across all tables:{" "}
          {databaseStatsData.total_records.toLocaleString()}
        </Text>
      </VStack>

      <Box w="full">
        <Heading size="md" mb={6}>
          Recent Activity Overview
        </Heading>
        <RecentStatsGrid data={databaseStatsData.recent_stats} />
      </Box>

      <Box w="full">
        <Heading size="md" mb={6}>
          Table Record Counts
        </Heading>
        <TableCountsGrid data={databaseStatsData.table_counts} />
      </Box>

      <Box w="full">
        <Heading size="md" mb={6}>
          Event Type Distribution
        </Heading>
        <EventTypeBreakdown
          data={databaseStatsData.sync_run_stats.event_type_breakdown}
        />
      </Box>

      <Box w="full">
        <Heading size="md" mb={6}>
          Recent Sync Runs
        </Heading>
        <Text color="gray.600" mb={4}>
          Latest synchronization runs (showing{" "}
          {databaseStatsData.sync_run_stats.recent_sync_runs.length} of{" "}
          {databaseStatsData.sync_run_stats.total_sync_runs} total)
        </Text>
        <Card.Root>
          <Card.Body p={0}>
            <SyncRunsTable
              data={databaseStatsData.sync_run_stats.recent_sync_runs}
            />
          </Card.Body>
        </Card.Root>
      </Box>

      <Box w="full">
        <Heading size="md" mb={4}>
          Most Recently Changed Repositories
        </Heading>
        <Text color="gray.600" mb={6}>
          Top 10 repositories with the most Kubernetes resource changes in the
          last {recentActiveRepositoriesData.period_days} days
        </Text>
        <Card.Root>
          <Card.Body p={0}>
            <RecentActiveRepositoriesTable
              data={recentActiveRepositoriesData.recent_active_repositories}
            />
          </Card.Body>
        </Card.Root>
      </Box>
    </VStack>
  )
}

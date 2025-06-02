import {
  Box,
  Card,
  Grid,
  HStack,
  Heading,
  Link,
  Stat,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { Link as TanstackLink } from "@tanstack/react-router"

import { AdminService } from "@/client"

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
      sync_run_id: string
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
      const response = await AdminService.adminGetDatabaseStats()
      return response.data as unknown as DatabaseStats
    },
    queryKey: ["admin", "database-stats"],
    refetchInterval: 30000, // Refresh every 30 seconds
  }
}

function getRecentActiveRepositoriesQueryOptions() {
  return {
    queryFn: async () => {
      const response = await AdminService.adminGetRecentActiveRepositories()
      return response.data as unknown as RecentActiveRepositories
    },
    queryKey: ["admin", "recent-active-repositories"],
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
      label: "New Repositories (7 days)",
      count: data.new_repositories_last_7_days,
      color: "blue",
    },
    {
      label: "Resource Changes (7 days)",
      count: data.resource_changes_last_7_days,
      color: "green",
    },
  ]

  return (
    <Grid
      templateColumns={{
        base: "1fr",
        md: "repeat(2, 1fr)",
      }}
      gap={4}
    >
      {statsData.map((stat) => (
        <Card.Root key={stat.label} p={4}>
          <Card.Body>
            <Stat.Root>
              <Stat.Label fontSize="sm" color="gray.600">
                {stat.label}
              </Stat.Label>
              <Stat.ValueText
                fontSize="2xl"
                fontWeight="bold"
                color={`${stat.color}.500`}
              >
                {stat.count.toLocaleString()}
              </Stat.ValueText>
            </Stat.Root>
          </Card.Body>
        </Card.Root>
      ))}
    </Grid>
  )
}

function SyncRunsTable({
  data,
}: { data: DatabaseStats["sync_run_stats"]["recent_sync_runs"] }) {
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
          <Table.ColumnHeader>Sync Run ID</Table.ColumnHeader>
          <Table.ColumnHeader>Events</Table.ColumnHeader>
          <Table.ColumnHeader>Started</Table.ColumnHeader>
          <Table.ColumnHeader>Completed</Table.ColumnHeader>
          <Table.ColumnHeader>Duration</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {data.map((run) => (
          <Table.Row key={run.sync_run_id}>
            <Table.Cell>
              <Text fontFamily="mono" fontSize="xs">
                {run.sync_run_id.substring(0, 8)}...
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
    <VStack align="start" gap={3}>
      {eventTypes.map((event) => (
        <HStack key={event.type} justify="space-between" w="full">
          <HStack>
            <Box
              w={3}
              h={3}
              bg={`${getEventTypeColor(event.type)}.500`}
              borderRadius="full"
            />
            <Text fontWeight="medium" textTransform="capitalize">
              {event.type}
            </Text>
          </HStack>
          <HStack>
            <Text fontWeight="bold">{event.count.toLocaleString()}</Text>
            <Text fontSize="sm" color="gray.600">
              ({event.percentage}%)
            </Text>
          </HStack>
        </HStack>
      ))}
    </VStack>
  )
}

function RecentActiveRepositoriesTable({
  data,
}: { data: RecentActiveRepository[] }) {
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

  return (
    <Table.Root size="sm">
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>Repository</Table.ColumnHeader>
          <Table.ColumnHeader>Total Events</Table.ColumnHeader>
          <Table.ColumnHeader>Event Breakdown</Table.ColumnHeader>
          <Table.ColumnHeader>Last Activity</Table.ColumnHeader>
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
                  <Text fontSize="xs" color="gray.500" truncate>
                    {repo.description}
                  </Text>
                )}
              </VStack>
            </Table.Cell>
            <Table.Cell>
              <Text fontWeight="bold" fontSize="lg">
                {repo.total_events.toLocaleString()}
              </Text>
            </Table.Cell>
            <Table.Cell>
              <HStack gap={2} wrap="wrap">
                {Object.entries(repo.event_breakdown).map(([type, count]) => (
                  <HStack key={type} gap={1}>
                    <Box
                      w={2}
                      h={2}
                      bg={`${getEventTypeColor(type)}.500`}
                      borderRadius="full"
                    />
                    <Text fontSize="xs" fontWeight="medium">
                      {type}: {count}
                    </Text>
                  </HStack>
                ))}
              </HStack>
            </Table.Cell>
            <Table.Cell>
              <Text fontSize="xs">{formatDate(repo.last_activity)}</Text>
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
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
        <Heading size="lg">Database Statistics</Heading>
        <Text>Loading database statistics...</Text>
      </VStack>
    )
  }

  if (errorDatabaseStats || errorRecentActiveRepositories) {
    return (
      <VStack gap={6} align="start">
        <Heading size="lg">Database Statistics</Heading>
        <Text color="red.500">Failed to load database statistics</Text>
      </VStack>
    )
  }

  if (!databaseStatsData || !recentActiveRepositoriesData) {
    return null
  }

  return (
    <VStack gap={6} align="start" w="full">
      <VStack align="start" gap={2}>
        <Heading size="lg">Database Statistics</Heading>
        <Text color="gray.600">
          Total records across all tables:{" "}
          {databaseStatsData.total_records.toLocaleString()}
        </Text>
      </VStack>

      <Box w="full">
        <Heading size="md" mb={4}>
          Recent Activity
        </Heading>
        <RecentStatsGrid data={databaseStatsData.recent_stats} />
      </Box>

      <Box w="full">
        <Heading size="md" mb={4}>
          Table Record Counts
        </Heading>
        <TableCountsGrid data={databaseStatsData.table_counts} />
      </Box>

      <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap={6} w="full">
        <Box>
          <Heading size="md" mb={4}>
            Recent Sync Runs ({databaseStatsData.sync_run_stats.total_sync_runs}{" "}
            total)
          </Heading>
          <Card.Root>
            <Card.Body p={0}>
              <SyncRunsTable
                data={databaseStatsData.sync_run_stats.recent_sync_runs}
              />
            </Card.Body>
          </Card.Root>
        </Box>

        <Box>
          <Heading size="md" mb={4}>
            Event Type Breakdown
          </Heading>
          <Card.Root>
            <Card.Body>
              <EventTypeBreakdown
                data={databaseStatsData.sync_run_stats.event_type_breakdown}
              />
            </Card.Body>
          </Card.Root>
        </Box>
      </Grid>

      <Box w="full">
        <Heading size="md" mb={4}>
          Most Recently Changed Repositories (Last 3 Days)
        </Heading>
        <Text color="gray.600" mb={4}>
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

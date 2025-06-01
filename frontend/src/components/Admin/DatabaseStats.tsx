import {
  Box,
  Card,
  Grid,
  HStack,
  Heading,
  Stat,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"

import { AdminService } from "@/client"

interface DatabaseStats {
  table_counts: {
    users: number
    repositories: number
    repository_metrics: number
    kubernetes_resources: number
    kubernetes_resource_events: number
  }
  sync_run_stats: {
    total_sync_runs: number
    recent_sync_runs: Array<{
      sync_run_id: string
      event_count: number
      started_at: string | null
      completed_at: string | null
      duration_seconds: number | null
    }>
    event_type_breakdown: Record<string, number>
  }
  total_records: number
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

function TableCountsGrid({ data }: { data: DatabaseStats["table_counts"] }) {
  const tableData = [
    { label: "Users", count: data.users, color: "blue" },
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
        md: "repeat(3, 1fr)",
        lg: "repeat(5, 1fr)",
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

function SyncRunsTable({
  data,
}: { data: DatabaseStats["sync_run_stats"]["recent_sync_runs"] }) {
  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "N/A"
    if (seconds < 60) return `${Math.round(seconds)}s`
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
            <Table.Cell>{formatDuration(run.duration_seconds)}</Table.Cell>
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

export default function DatabaseStats() {
  const { data, isLoading, error } = useQuery(getDatabaseStatsQueryOptions())

  if (isLoading) {
    return (
      <VStack gap={6} align="start">
        <Heading size="lg">Database Statistics</Heading>
        <Text>Loading database statistics...</Text>
      </VStack>
    )
  }

  if (error) {
    return (
      <VStack gap={6} align="start">
        <Heading size="lg">Database Statistics</Heading>
        <Text color="red.500">Failed to load database statistics</Text>
      </VStack>
    )
  }

  if (!data) {
    return null
  }

  return (
    <VStack gap={6} align="start" w="full">
      <VStack align="start" gap={2}>
        <Heading size="lg">Database Statistics</Heading>
        <Text color="gray.600">
          Total records across all tables: {data.total_records.toLocaleString()}
        </Text>
      </VStack>

      <Box w="full">
        <Heading size="md" mb={4}>
          Table Record Counts
        </Heading>
        <TableCountsGrid data={data.table_counts} />
      </Box>

      <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap={6} w="full">
        <Box>
          <Heading size="md" mb={4}>
            Recent Sync Runs ({data.sync_run_stats.total_sync_runs} total)
          </Heading>
          <Card.Root>
            <Card.Body p={0}>
              <SyncRunsTable data={data.sync_run_stats.recent_sync_runs} />
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
                data={data.sync_run_stats.event_type_breakdown}
              />
            </Card.Body>
          </Card.Root>
        </Box>
      </Grid>
    </VStack>
  )
}

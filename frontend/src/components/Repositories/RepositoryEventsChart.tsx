import {
  Box,
  Button,
  ButtonGroup,
  Card,
  Heading,
  Skeleton,
  Stack,
  Text,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import type { EventDailyCountsPublic } from "../../client"
import { RepositoriesService } from "../../client"

interface RepositoryEventsChartProps {
  repositoryId: string
}

type TimeFilter = "7d" | "30d" | "90d"

function RepositoryEventsChart({ repositoryId }: RepositoryEventsChartProps) {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>("30d")

  const getDaysFromFilter = (filter: TimeFilter): number => {
    switch (filter) {
      case "7d":
        return 7
      case "30d":
        return 30
      case "90d":
        return 90
      default:
        return 30
    }
  }

  const {
    data: dailyCountsData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["repository-events-daily-counts", repositoryId, timeFilter],
    queryFn: () =>
      RepositoriesService.repositoriesReadRepositoryEventsDailyCounts({
        path: { repository_id: repositoryId },
        query: {
          days: getDaysFromFilter(timeFilter),
        },
      }),
    enabled: !!repositoryId,
  })

  const dailyCounts =
    (dailyCountsData?.data as EventDailyCountsPublic | undefined)?.data || []

  // Transform data for the chart
  const getChartData = () => {
    if (!dailyCounts.length) return []

    // Group by date and aggregate by event type
    const groupedByDate: Record<string, Record<string, number>> = {}

    for (const count of dailyCounts) {
      if (!groupedByDate[count.date]) {
        groupedByDate[count.date] = { CREATED: 0, MODIFIED: 0, DELETED: 0 }
      }
      groupedByDate[count.date][count.event_type] = count.count
    }

    // Convert to chart format and sort by date
    return Object.entries(groupedByDate)
      .map(([date, eventCounts]) => ({
        date,
        formattedDate: new Date(date).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        }),
        CREATED: eventCounts.CREATED || 0,
        MODIFIED: eventCounts.MODIFIED || 0,
        DELETED: eventCounts.DELETED || 0,
        total:
          (eventCounts.CREATED || 0) +
          (eventCounts.MODIFIED || 0) +
          (eventCounts.DELETED || 0),
      }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
  }

  const chartData = getChartData()

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <Box
          bg="bg.panel"
          border="1px solid"
          borderColor="border.muted"
          borderRadius="md"
          p={3}
          shadow="lg"
        >
          <Text fontWeight="medium" mb={2}>
            {new Date(data.date).toLocaleDateString("en-US", {
              weekday: "short",
              month: "short",
              day: "numeric",
              year: "numeric",
            })}
          </Text>
          <Stack gap={1}>
            {payload.map((entry: any) => (
              <Box
                key={entry.dataKey}
                display="flex"
                alignItems="center"
                gap={2}
              >
                <Box w={3} h={3} borderRadius="sm" bg={entry.color} />
                <Text fontSize="sm">
                  {entry.dataKey}:{" "}
                  <Text as="span" fontWeight="medium">
                    {entry.value}
                  </Text>
                </Text>
              </Box>
            ))}
            <Box
              display="flex"
              alignItems="center"
              gap={2}
              mt={1}
              pt={1}
              borderTop="1px solid"
              borderColor="border.muted"
            >
              <Text fontSize="sm" fontWeight="medium">
                Total: {data.total}
              </Text>
            </Box>
          </Stack>
        </Box>
      )
    }
    return null
  }

  if (isLoading) {
    return (
      <Card.Root>
        <Card.Header>
          <Heading size="lg">Daily Event Activity</Heading>
          <Text color="fg.muted">Resource events over time</Text>
        </Card.Header>
        <Card.Body>
          <Skeleton height="400px" />
        </Card.Body>
      </Card.Root>
    )
  }

  if (isError) {
    return (
      <Card.Root>
        <Card.Header>
          <Heading size="lg">Daily Event Activity</Heading>
          <Text color="fg.muted">Resource events over time</Text>
        </Card.Header>
        <Card.Body>
          <Box textAlign="center" py={12}>
            <Text color="fg.muted">Unable to load events chart data</Text>
          </Box>
        </Card.Body>
      </Card.Root>
    )
  }

  return (
    <Card.Root>
      <Card.Header>
        <Stack
          direction={{ base: "column", md: "row" }}
          justify="space-between"
          align={{ md: "center" }}
        >
          <Box>
            <Heading size="lg">Daily Event Activity</Heading>
            <Text color="fg.muted">Resource events over time</Text>
          </Box>
          <ButtonGroup size="sm" variant="outline">
            <Button
              variant={timeFilter === "7d" ? "solid" : "outline"}
              onClick={() => setTimeFilter("7d")}
            >
              7 Days
            </Button>
            <Button
              variant={timeFilter === "30d" ? "solid" : "outline"}
              onClick={() => setTimeFilter("30d")}
            >
              30 Days
            </Button>
            <Button
              variant={timeFilter === "90d" ? "solid" : "outline"}
              onClick={() => setTimeFilter("90d")}
            >
              90 Days
            </Button>
          </ButtonGroup>
        </Stack>
      </Card.Header>
      <Card.Body>
        {chartData.length === 0 ? (
          <Box textAlign="center" py={12}>
            <Text color="fg.muted">
              No events found for the selected time period
            </Text>
          </Box>
        ) : (
          <Box h="400px">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="var(--chakra-colors-border-muted)"
                />
                <XAxis
                  dataKey="formattedDate"
                  tick={{ fontSize: 12 }}
                  tickLine={{ stroke: "var(--chakra-colors-border-muted)" }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickLine={{ stroke: "var(--chakra-colors-border-muted)" }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="CREATED"
                  stroke="var(--chakra-colors-green-500)"
                  strokeWidth={2}
                  dot={{
                    fill: "var(--chakra-colors-green-500)",
                    strokeWidth: 2,
                    r: 4,
                  }}
                  name="Created"
                />
                <Line
                  type="monotone"
                  dataKey="MODIFIED"
                  stroke="var(--chakra-colors-blue-500)"
                  strokeWidth={2}
                  dot={{
                    fill: "var(--chakra-colors-blue-500)",
                    strokeWidth: 2,
                    r: 4,
                  }}
                  name="Modified"
                />
                <Line
                  type="monotone"
                  dataKey="DELETED"
                  stroke="var(--chakra-colors-red-500)"
                  strokeWidth={2}
                  dot={{
                    fill: "var(--chakra-colors-red-500)",
                    strokeWidth: 2,
                    r: 4,
                  }}
                  name="Deleted"
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}
      </Card.Body>
    </Card.Root>
  )
}

export default RepositoryEventsChart

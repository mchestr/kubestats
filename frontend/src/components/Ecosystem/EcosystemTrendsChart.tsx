import {
  Box,
  Button,
  ButtonGroup,
  HStack,
  Skeleton,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react"
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

import type { EcosystemTrendsPublic } from "@/client"

interface EcosystemTrendsChartProps {
  trends: EcosystemTrendsPublic | undefined
  isLoading: boolean
  period: string
}

type ChartMode = "repositories" | "resources" | "activity" | "combined"

function EcosystemTrendsChart({
  trends,
  isLoading,
  period,
}: EcosystemTrendsChartProps) {
  const [chartMode, setChartMode] = useState<ChartMode>("combined")

  if (isLoading || !trends) {
    return <Skeleton height="400px" borderRadius="md" />
  }

  // Transform trend data for charting
  const getChartData = () => {
    if (!trends) return []

    // Create a map of dates to combine all trend data
    const dateMap = new Map<string, any>()

    // Add repository trends
    for (const trend of trends.repository_trends) {
      const existing = dateMap.get(trend.date) || { date: trend.date }
      existing.repositories = trend.value
      dateMap.set(trend.date, existing)
    }

    // Add resource trends
    for (const trend of trends.resource_trends) {
      const existing = dateMap.get(trend.date) || { date: trend.date }
      existing.resources = trend.value
      dateMap.set(trend.date, existing)
    }

    // Add activity trends
    for (const trend of trends.activity_trends) {
      const existing = dateMap.get(trend.date) || { date: trend.date }
      existing.activity = trend.value
      dateMap.set(trend.date, existing)
    }

    // Convert to array and sort by date
    const chartData = Array.from(dateMap.values())
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map((item) => ({
        ...item,
        formattedDate: new Date(item.date).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        }),
      }))

    return chartData
  }

  const chartData = getChartData()

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          bg="bg.panel"
          border="1px solid"
          borderColor="border.muted"
          borderRadius="md"
          p={4}
          shadow="lg"
        >
          <Text fontWeight="semibold" mb={2}>
            {new Date(payload[0].payload.date).toLocaleDateString("en-US", {
              weekday: "long",
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
          </Text>
          <Stack gap={1}>
            {payload.map((entry: any) => (
              <HStack key={entry.dataKey} justify="space-between" minW="200px">
                <HStack gap={2}>
                  <Box w={3} h={3} borderRadius="sm" bg={entry.color} />
                  <Text fontSize="sm" color="fg.default">
                    {entry.name}
                  </Text>
                </HStack>
                <Text fontSize="sm" fontWeight="semibold">
                  {entry.value?.toLocaleString() || 0}
                </Text>
              </HStack>
            ))}
          </Stack>
        </Box>
      )
    }
    return null
  }

  const getVisibleLines = () => {
    switch (chartMode) {
      case "repositories":
        return ["repositories"]
      case "resources":
        return ["resources"]
      case "activity":
        return ["activity"]
      default:
        return ["repositories", "resources", "activity"]
    }
  }

  const lineConfig = {
    repositories: {
      color: "#3b82f6",
      name: "Total Repositories",
    },
    resources: {
      color: "#10b981",
      name: "Active Resources",
    },
    activity: {
      color: "#f59e0b",
      name: "Daily Activity",
    },
  }

  if (chartData.length === 0) {
    return (
      <Box textAlign="center" py={12}>
        <VStack gap={3}>
          <Text color="fg.muted" fontSize="lg">
            No trend data available
          </Text>
          <Text color="fg.muted" fontSize="sm">
            Trend data will appear once ecosystem statistics are collected over
            time
          </Text>
        </VStack>
      </Box>
    )
  }

  return (
    <Stack gap={4}>
      {/* Chart Mode Selector */}
      <ButtonGroup size="sm" variant="outline">
        <Button
          variant={chartMode === "combined" ? "solid" : "outline"}
          onClick={() => setChartMode("combined")}
        >
          Combined View
        </Button>
        <Button
          variant={chartMode === "repositories" ? "solid" : "outline"}
          onClick={() => setChartMode("repositories")}
        >
          Repositories
        </Button>
        <Button
          variant={chartMode === "resources" ? "solid" : "outline"}
          onClick={() => setChartMode("resources")}
        >
          Resources
        </Button>
        <Button
          variant={chartMode === "activity" ? "solid" : "outline"}
          onClick={() => setChartMode("activity")}
        >
          Activity
        </Button>
      </ButtonGroup>

      {/* Chart */}
      <Box height="400px" width="100%">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 20,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis
              dataKey="formattedDate"
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => {
                if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
                if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
                return value.toString()
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {getVisibleLines().map((line) => {
              const config = lineConfig[line as keyof typeof lineConfig]
              return (
                <Line
                  key={line}
                  type="monotone"
                  dataKey={line}
                  stroke={config.color}
                  strokeWidth={2}
                  dot={{ fill: config.color, strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6 }}
                  name={config.name}
                />
              )
            })}
          </LineChart>
        </ResponsiveContainer>
      </Box>

      {/* Chart Summary */}
      <Box bg="bg.muted" p={4} borderRadius="md">
        <HStack justify="space-between" wrap="wrap" gap={4}>
          <VStack align="start" gap={1}>
            <Text fontSize="sm" fontWeight="semibold" color="fg.default">
              Trend Period
            </Text>
            <Text fontSize="sm" color="fg.muted">
              {period.toUpperCase()} • {chartData.length} data points
            </Text>
          </VStack>
          {chartData.length > 1 && (
            <>
              <VStack align="center" gap={1}>
                <Text fontSize="sm" fontWeight="semibold" color="blue.600">
                  Repositories
                </Text>
                <Text fontSize="sm" color="fg.muted">
                  {chartData[
                    chartData.length - 1
                  ]?.repositories?.toLocaleString() || 0}
                </Text>
              </VStack>
              <VStack align="center" gap={1}>
                <Text fontSize="sm" fontWeight="semibold" color="green.600">
                  Resources
                </Text>
                <Text fontSize="sm" color="fg.muted">
                  {chartData[
                    chartData.length - 1
                  ]?.resources?.toLocaleString() || 0}
                </Text>
              </VStack>
              <VStack align="center" gap={1}>
                <Text fontSize="sm" fontWeight="semibold" color="orange.600">
                  Activity
                </Text>
                <Text fontSize="sm" color="fg.muted">
                  {chartData[
                    chartData.length - 1
                  ]?.activity?.toLocaleString() || 0}
                </Text>
              </VStack>
            </>
          )}
        </HStack>
      </Box>
    </Stack>
  )
}

export { EcosystemTrendsChart }

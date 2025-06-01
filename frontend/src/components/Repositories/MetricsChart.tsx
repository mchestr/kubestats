import { Box, Button, ButtonGroup, Stack, Text } from "@chakra-ui/react"
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

import type { RepositoryMetricsPublic } from "../../client"

interface MetricsChartProps {
  metrics: RepositoryMetricsPublic[]
}

type TimeFilter = "7d" | "30d" | "90d" | "1y" | "all"

function MetricsChart({ metrics }: MetricsChartProps) {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>("90d")
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([
    "stars_count",
    "forks_count",
    "kubernetes_resources_count",
  ])
  console.log(metrics);

  const getFilteredData = () => {
    if (!metrics.length) return []

    const now = new Date()
    let cutoffDate: Date

    switch (timeFilter) {
      case "7d":
        cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      case "30d":
        cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        break
      case "90d":
        cutoffDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
        break
      case "1y":
        cutoffDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
        break
      case "all":
        cutoffDate = new Date(0)
        break
      default:
        cutoffDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
    }

    return metrics
      .filter((metric) => new Date(metric.recorded_at) >= cutoffDate)
      .sort(
        (a, b) =>
          new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime(),
      )
      .map((metric) => ({
        ...metric,
        date: new Date(metric.recorded_at).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year:
            timeFilter === "all" || timeFilter === "1y" ? "numeric" : undefined,
        }),
      }))
  }

  const toggleMetric = (metric: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(metric)
        ? prev.filter((m) => m !== metric)
        : [...prev, metric],
    )
  }

  const chartData = getFilteredData()

  const metricConfig = {
    stars_count: { color: "#f59e0b", label: "Stars" },
    forks_count: { color: "#3b82f6", label: "Forks" },
    kubernetes_resources_count: { color: "#10b981", label: "Resources" },
    open_issues_count: { color: "#ef4444", label: "Open Issues" },
    size: { color: "#8b5cf6", label: "Size (KB)" },
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          bg="bg.panel"
          border="1px solid"
          borderColor="border.default"
          borderRadius="md"
          p={3}
          shadow="md"
        >
          <Text fontWeight="medium" mb={2}>
            {label}
          </Text>
          {payload.map((entry: any, index: number) => (
            <Text key={index} color={entry.color} fontSize="sm">
              {entry.name}: {entry.value.toLocaleString()}
            </Text>
          ))}
        </Box>
      )
    }
    return null
  }

  if (!metrics.length) {
    return (
      <Box textAlign="center" py={12}>
        <Text color="fg.muted">No metrics data available</Text>
      </Box>
    )
  }

  return (
    <Stack gap={4}>
      {/* Time Filter Buttons */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        flexWrap="wrap"
      >
        <ButtonGroup size="sm">
          {(["7d", "30d", "90d", "1y", "all"] as TimeFilter[]).map((filter) => (
            <Button
              key={filter}
              variant={timeFilter === filter ? "solid" : "outline"}
              onClick={() => setTimeFilter(filter)}
            >
              {filter === "all" ? "All Time" : filter.toUpperCase()}
            </Button>
          ))}
        </ButtonGroup>

        {/* Metric Toggle Buttons */}
        <ButtonGroup size="sm">
          {Object.entries(metricConfig).map(([key, config]) => (
            <Button
              key={key}
              variant={selectedMetrics.includes(key) ? "solid" : "outline"}
              colorPalette={selectedMetrics.includes(key) ? "blue" : "gray"}
              onClick={() => toggleMetric(key)}
              fontSize="xs"
            >
              {config.label}
            </Button>
          ))}
        </ButtonGroup>
      </Stack>

      {/* Chart */}
      <Box height="400px" width="100%">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis
              dataKey="date"
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
            {selectedMetrics.map((metric) => {
              const config = metricConfig[metric as keyof typeof metricConfig]
              if (!config) return null

              return (
                <Line
                  key={metric}
                  type="monotone"
                  dataKey={metric}
                  stroke={config.color}
                  strokeWidth={2}
                  dot={{ fill: config.color, strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6 }}
                  name={config.label}
                />
              )
            })}
          </LineChart>
        </ResponsiveContainer>
      </Box>

      {chartData.length === 0 && (
        <Box textAlign="center" py={8}>
          <Text color="fg.muted">
            No data available for the selected time period
          </Text>
        </Box>
      )}
    </Stack>
  )
}

export default MetricsChart

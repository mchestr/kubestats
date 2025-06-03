import {
  Box,
  Card,
  CardBody,
  CardHeader,
  HStack,
  Heading,
  Progress,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react"
import {
  FiCode,
  FiGitBranch,
  FiLayers,
  FiStar,
  FiTag,
  FiUsers,
} from "react-icons/fi"
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts"

import type { EcosystemStatsPublic } from "@/client"

interface ResourceBreakdownChartsProps {
  stats: EcosystemStatsPublic | undefined
  isLoading: boolean
}

function ResourceBreakdownCharts({
  stats,
  isLoading,
}: ResourceBreakdownChartsProps) {
  if (isLoading || !stats) {
    return (
      <Stack gap={6}>
        <Skeleton height="300px" borderRadius="md" />
        <Skeleton height="300px" borderRadius="md" />
        <Skeleton height="200px" borderRadius="md" />
      </Stack>
    )
  }

  // Prepare data for charts
  const resourceTypeData = Object.entries(stats.resource_type_breakdown || {})
    .map(([type, count]) => ({
      name: type,
      value: Number(count),
      percentage: Math.round(
        (Number(count) /
          Object.values(stats.resource_type_breakdown || {}).reduce(
            (sum: number, val: any) => sum + Number(val),
            0,
          )) *
          100,
      ),
    }))
    .sort((a, b) => b.value - a.value)

  const languageData = Object.entries(stats.language_breakdown || {})
    .map(([language, count]) => ({
      name: language,
      value: Number(count),
      percentage: Math.round(
        (Number(count) /
          Object.values(stats.language_breakdown || {}).reduce(
            (sum: number, val: any) => sum + Number(val),
            0,
          )) *
          100,
      ),
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8) // Show top 8 languages

  const topicsData = Object.entries(stats.popular_topics || {})
    .map(([topic, count]) => ({
      name: topic,
      value: Number(count),
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6) // Show top 6 topics

  const helmChartsData = Object.entries(stats.popular_helm_charts || {})
    .map(([chart, count]) => ({
      name: chart,
      value: Number(count),
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5) // Show top 5 helm charts

  // Color schemes for charts
  const resourceTypeColors = [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#06b6d4",
    "#84cc16",
    "#f97316",
    "#ec4899",
    "#6366f1",
  ]

  const languageColors = [
    "#3178c6",
    "#f1e05a",
    "#e34c26",
    "#563d7c",
    "#b07219",
    "#f1e05a",
    "#701516",
    "#89e051",
    "#ff6b6b",
    "#4caf50",
  ]

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
          <Text fontWeight="semibold" mb={1}>
            {data.name}
          </Text>
          <Text color="fg.muted" fontSize="sm">
            Count: {data.value.toLocaleString()}
          </Text>
          {data.percentage && (
            <Text color="fg.muted" fontSize="sm">
              {data.percentage}% of total
            </Text>
          )}
        </Box>
      )
    }
    return null
  }

  return (
    <Stack gap={6}>
      {/* Resource Type Breakdown */}
      <Card.Root>
        <CardHeader>
          <HStack>
            <FiLayers />
            <VStack align="start" gap={1}>
              <Heading size="md">Resource Type Distribution</Heading>
              <Text color="fg.muted" fontSize="sm">
                Breakdown by Kubernetes resource types
              </Text>
            </VStack>
          </HStack>
        </CardHeader>
        <CardBody>
          {resourceTypeData.length > 0 ? (
            <Box height="250px">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={resourceTypeData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percentage }) => `${name} (${percentage}%)`}
                    labelLine={false}
                  >
                    {resourceTypeData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          resourceTypeColors[index % resourceTypeColors.length]
                        }
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          ) : (
            <Box textAlign="center" py={8}>
              <Text color="fg.muted">No resource type data available</Text>
            </Box>
          )}
        </CardBody>
      </Card.Root>

      {/* Programming Languages */}
      <Card.Root>
        <Card.Header>
          <HStack>
            <FiCode />
            <VStack align="start" gap={1}>
              <Heading size="md">Programming Languages</Heading>
              <Text color="fg.muted" fontSize="sm">
                Top languages across repositories
              </Text>
            </VStack>
          </HStack>
        </Card.Header>
        <Card.Body>
          {languageData.length > 0 ? (
            <Stack gap={3}>
              {languageData.map((language, index) => (
                <Box key={language.name}>
                  <HStack justify="space-between" mb={2}>
                    <HStack gap={2}>
                      <Box
                        w={3}
                        h={3}
                        borderRadius="sm"
                        bg={languageColors[index % languageColors.length]}
                      />
                      <Text fontSize="sm" fontWeight="medium">
                        {language.name}
                      </Text>
                    </HStack>
                    <HStack gap={2}>
                      <Text fontSize="sm" color="fg.muted">
                        {language.value}
                      </Text>
                      <Text fontSize="sm" color="fg.muted">
                        ({language.percentage}%)
                      </Text>
                    </HStack>
                  </HStack>
                  <Progress.Root
                    value={language.percentage}
                    colorPalette="blue"
                    size="sm"
                  >
                    <Progress.Track>
                      <Progress.Range />
                    </Progress.Track>
                  </Progress.Root>
                </Box>
              ))}
            </Stack>
          ) : (
            <Box textAlign="center" py={8}>
              <Text color="fg.muted">No language data available</Text>
            </Box>
          )}
        </Card.Body>
      </Card.Root>

      {/* GitHub Statistics */}
      <Card.Root>
        <Card.Header>
          <HStack>
            <FiStar />
            <VStack align="start" gap={1}>
              <Heading size="md">GitHub Activity</Heading>
              <Text color="fg.muted" fontSize="sm">
                Community engagement metrics
              </Text>
            </VStack>
          </HStack>
        </Card.Header>
        <Card.Body>
          <SimpleGrid columns={2} gap={4}>
            <VStack align="center" p={3} bg="yellow.50" borderRadius="md">
              <FiStar size={20} color="#f59e0b" />
              <Text fontSize="2xl" fontWeight="bold" color="yellow.600">
                {stats.total_stars.toLocaleString()}
              </Text>
              <Text fontSize="sm" color="fg.muted" textAlign="center">
                Total Stars
              </Text>
              {stats.star_growth !== 0 && (
                <Text
                  fontSize="xs"
                  color={stats.star_growth > 0 ? "green.600" : "red.600"}
                >
                  {stats.star_growth > 0 ? "+" : ""}
                  {stats.star_growth} today
                </Text>
              )}
            </VStack>

            <VStack align="center" p={3} bg="blue.50" borderRadius="md">
              <FiGitBranch size={20} color="#3b82f6" />
              <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                {stats.total_forks.toLocaleString()}
              </Text>
              <Text fontSize="sm" color="fg.muted" textAlign="center">
                Total Forks
              </Text>
            </VStack>

            <VStack align="center" p={3} bg="green.50" borderRadius="md">
              <FiUsers size={20} color="#10b981" />
              <Text fontSize="2xl" fontWeight="bold" color="green.600">
                {stats.total_watchers.toLocaleString()}
              </Text>
              <Text fontSize="sm" color="fg.muted" textAlign="center">
                Watchers
              </Text>
            </VStack>

            <VStack align="center" p={3} bg="red.50" borderRadius="md">
              <FiUsers size={20} color="#ef4444" />
              <Text fontSize="2xl" fontWeight="bold" color="red.600">
                {stats.total_open_issues.toLocaleString()}
              </Text>
              <Text fontSize="sm" color="fg.muted" textAlign="center">
                Open Issues
              </Text>
            </VStack>
          </SimpleGrid>
        </Card.Body>
      </Card.Root>

      {/* Popular Topics */}
      {topicsData.length > 0 && (
        <Card.Root>
          <Card.Header>
            <HStack>
              <FiTag />
              <VStack align="start" gap={1}>
                <Heading size="md">Popular Topics</Heading>
                <Text color="fg.muted" fontSize="sm">
                  Most common repository topics
                </Text>
              </VStack>
            </HStack>
          </Card.Header>
          <Card.Body>
            <SimpleGrid columns={2} gap={3}>
              {topicsData.map((topic) => (
                <HStack
                  key={topic.name}
                  justify="space-between"
                  p={2}
                  bg="bg.muted"
                  borderRadius="md"
                >
                  <Text fontSize="sm" fontWeight="medium">
                    {topic.name}
                  </Text>
                  <Text fontSize="sm" color="fg.muted">
                    {topic.value}
                  </Text>
                </HStack>
              ))}
            </SimpleGrid>
          </Card.Body>
        </Card.Root>
      )}

      {/* Popular Helm Charts */}
      {helmChartsData.length > 0 && (
        <Card.Root>
          <Card.Header>
            <HStack>
              <FiLayers />
              <VStack align="start" gap={1}>
                <Heading size="md">Popular Helm Charts</Heading>
                <Text color="fg.muted" fontSize="sm">
                  Most deployed Helm charts
                </Text>
              </VStack>
            </HStack>
          </Card.Header>
          <Card.Body>
            <Stack gap={2}>
              {helmChartsData.map((chart, index) => (
                <HStack
                  key={chart.name}
                  justify="space-between"
                  p={2}
                  bg="bg.muted"
                  borderRadius="md"
                >
                  <HStack>
                    <Text fontSize="sm" fontWeight="bold" color="blue.600">
                      #{index + 1}
                    </Text>
                    <Text fontSize="sm" fontWeight="medium">
                      {chart.name}
                    </Text>
                  </HStack>
                  <Text fontSize="sm" color="fg.muted">
                    {chart.value} deployments
                  </Text>
                </HStack>
              ))}
            </Stack>
          </Card.Body>
        </Card.Root>
      )}
    </Stack>
  )
}

export { ResourceBreakdownCharts }

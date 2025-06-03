import {
  Box,
  Card,
  HStack,
  Heading,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react"
import {
  FiActivity,
  FiDatabase,
  FiGitBranch,
  FiLayers,
  FiStar,
  FiTrendingUp,
  FiUsers,
} from "react-icons/fi"
import type { EcosystemStatsPublic } from "../../client"

interface EcosystemOverviewProps {
  stats: EcosystemStatsPublic | undefined
  isLoading: boolean
}

interface MetricCardProps {
  icon: React.ElementType
  title: string
  value: string | number
  subtitle?: string
  growth?: number
  colorScheme: string
}

const MetricCard = ({
  icon: Icon,
  title,
  value,
  subtitle,
  growth,
  colorScheme,
}: MetricCardProps) => {
  const formatGrowth = (growth: number) => {
    const sign = growth > 0 ? "+" : ""
    return `${sign}${growth}`
  }

  const getGrowthColor = (growth: number) => {
    if (growth > 0) return "green.500"
    if (growth < 0) return "red.500"
    return "gray.500"
  }

  return (
    <Card.Root>
      <Card.Body>
        <VStack gap={3} align="start">
          <HStack justify="space-between" w="full">
            <HStack>
              <Box color={`${colorScheme}.500`}>
                <Icon size={20} />
              </Box>
              <Text fontSize="sm" fontWeight="medium" color="gray.600">
                {title}
              </Text>
            </HStack>
            {growth !== undefined && (
              <HStack gap={1}>
                <FiTrendingUp size={12} color={getGrowthColor(growth)} />
                <Text
                  fontSize="xs"
                  fontWeight="medium"
                  color={getGrowthColor(growth)}
                >
                  {formatGrowth(growth)}
                </Text>
              </HStack>
            )}
          </HStack>

          <VStack align="start" gap={1} w="full">
            <Text fontSize="2xl" fontWeight="bold" lineHeight="1">
              {typeof value === "number" ? value.toLocaleString() : value}
            </Text>
            {subtitle && (
              <Text fontSize="xs" color="gray.500">
                {subtitle}
              </Text>
            )}
          </VStack>
        </VStack>
      </Card.Body>
    </Card.Root>
  )
}

export function EcosystemOverview({
  stats,
  isLoading,
}: EcosystemOverviewProps) {
  if (isLoading || !stats) {
    return (
      <Box>
        <Heading size="md" mb={4}>
          <HStack>
            <FiDatabase />
            <Text>Ecosystem Overview</Text>
          </HStack>
        </Heading>
        <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} gap={4}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Card.Root key={i}>
              <Card.Body>
                <VStack gap={3}>
                  <Box w="20px" h="20px" bg="gray.200" borderRadius="md" />
                  <Box w="full" h="8" bg="gray.200" borderRadius="md" />
                  <Box w="3/4" h="4" bg="gray.100" borderRadius="md" />
                </VStack>
              </Card.Body>
            </Card.Root>
          ))}
        </SimpleGrid>
      </Box>
    )
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString()
  }

  return (
    <Box>
      <Heading size="md" mb={4}>
        <HStack justify="space-between">
          <HStack>
            <FiDatabase />
            <Text>Ecosystem Overview</Text>
          </HStack>
          <Text fontSize="sm" color="gray.500">
            {formatDate(stats.date)}
          </Text>
        </HStack>
      </Heading>

      <SimpleGrid columns={{ base: 2, md: 3, lg: 6 }} gap={4}>
        {/* Repository Metrics */}
        <MetricCard
          icon={FiGitBranch}
          title="Total Repositories"
          value={stats.total_repositories}
          subtitle={`${stats.repositories_with_resources} with resources`}
          growth={stats.repository_growth}
          colorScheme="blue"
        />

        <MetricCard
          icon={FiUsers}
          title="Active Repositories"
          value={stats.active_repositories}
          subtitle={`${Math.round((stats.active_repositories / stats.total_repositories) * 100)}% of total`}
          colorScheme="blue"
        />

        {/* Resource Metrics */}
        <MetricCard
          icon={FiLayers}
          title="Total Resources"
          value={stats.total_resources}
          subtitle={`${stats.active_resources} active`}
          growth={stats.resource_growth}
          colorScheme="green"
        />

        <MetricCard
          icon={FiActivity}
          title="Resource Events"
          value={stats.total_resource_events}
          subtitle="All time events"
          colorScheme="green"
        />

        {/* GitHub Metrics */}
        <MetricCard
          icon={FiStar}
          title="Total Stars"
          value={stats.total_stars}
          subtitle={`${stats.total_forks} forks`}
          growth={stats.star_growth}
          colorScheme="yellow"
        />

        <MetricCard
          icon={FiUsers}
          title="Open Issues"
          value={stats.total_open_issues}
          subtitle={`${stats.total_watchers} watchers`}
          colorScheme="orange"
        />
      </SimpleGrid>
    </Box>
  )
}

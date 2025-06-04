import {
  Box,
  Button,
  ButtonGroup,
  Card,
  Grid,
  HStack,
  Heading,
  SimpleGrid,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { FiActivity, FiDatabase, FiTrendingUp } from "react-icons/fi"

import { EcosystemService } from "@/client"
import { DailyActivity } from "./DailyActivity"
import { EcosystemOverview } from "./EcosystemOverview"
import { EcosystemTrendsChart } from "./EcosystemTrendsChart"
import { HelmReleaseActivitySummary } from "./HelmReleaseActivitySummary"
import { ResourceBreakdownCharts } from "./ResourceBreakdownCharts"

type TimePeriod = "7d" | "30d" | "90d"

function EcosystemDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>("30d")

  // Get latest ecosystem stats
  const {
    data: latestStatsData,
    isLoading: isLoadingStats,
    isError: isStatsError,
  } = useQuery({
    queryKey: ["ecosystem-latest-stats"],
    queryFn: () => EcosystemService.ecosystemGetLatestEcosystemStats(),
  })

  // Get ecosystem trends
  const {
    data: trendsData,
    isLoading: isLoadingTrends,
    isError: isTrendsError,
  } = useQuery({
    queryKey: ["ecosystem-trends", selectedPeriod],
    queryFn: () =>
      EcosystemService.ecosystemGetEcosystemTrends({
        query: { days: getDaysFromPeriod(selectedPeriod) },
      }),
  })

  const getDaysFromPeriod = (period: TimePeriod): number => {
    switch (period) {
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

  const latestStats = latestStatsData?.data
  const trends = trendsData?.data

  if (isStatsError || isTrendsError) {
    return (
      <Box w="full">
        <Card.Root>
          <Card.Body p={8}>
            <VStack gap={4} textAlign="center">
              <FiDatabase size={48} color="gray.400" />
              <Heading size="lg" color="fg.muted">
                Unable to Load Ecosystem Data
              </Heading>
              <Text color="fg.muted">
                There was an error loading the ecosystem statistics. Please try
                refreshing the page.
              </Text>
            </VStack>
          </Card.Body>
        </Card.Root>
      </Box>
    )
  }

  return (
    <Stack gap={8} w="full">
      {/* Header */}
      <Box>
        <HStack justify="space-between" align="center" mb={2}>
          <HStack gap={3}>
            <FiTrendingUp size={28} color="blue.500" />
            <VStack align="start" gap={1}>
              <Heading size="xl">Ecosystem Dashboard</Heading>
              <Text color="fg.muted" fontSize="lg">
                Comprehensive overview of Kubernetes ecosystem statistics and
                trends
              </Text>
            </VStack>
          </HStack>

          {/* Time Period Selector */}
          <ButtonGroup size="sm" variant="outline">
            <Button
              variant={selectedPeriod === "7d" ? "solid" : "outline"}
              onClick={() => setSelectedPeriod("7d")}
            >
              7 Days
            </Button>
            <Button
              variant={selectedPeriod === "30d" ? "solid" : "outline"}
              onClick={() => setSelectedPeriod("30d")}
            >
              30 Days
            </Button>
            <Button
              variant={selectedPeriod === "90d" ? "solid" : "outline"}
              onClick={() => setSelectedPeriod("90d")}
            >
              90 Days
            </Button>
          </ButtonGroup>
        </HStack>
      </Box>

      {/* Overview Cards */}
      <EcosystemOverview stats={latestStats} isLoading={isLoadingStats} />

      {/* Daily Activity */}
      <DailyActivity stats={latestStats} isLoading={isLoadingStats} />

      {/* Helm Release Activity Summary */}
      <HelmReleaseActivitySummary />

      {/* Main Dashboard Content */}
      <Grid templateColumns={{ base: "1fr", xl: "2fr 1fr" }} gap={8}>
        {/* Left Column - Trends and Main Charts */}
        <Stack gap={6}>
          {/* Ecosystem Trends Chart */}
          <Card.Root>
            <Card.Header>
              <HStack justify="space-between" align="center">
                <VStack align="start" gap={1}>
                  <Heading size="lg">
                    <HStack>
                      <FiTrendingUp />
                      <Text>Ecosystem Trends</Text>
                    </HStack>
                  </Heading>
                  <Text color="fg.muted">
                    Repository, resource, and activity trends over time
                  </Text>
                </VStack>
                <Text fontSize="sm" color="fg.muted">
                  Last {getDaysFromPeriod(selectedPeriod)} days
                </Text>
              </HStack>
            </Card.Header>
            <Card.Body>
              <EcosystemTrendsChart
                trends={trends}
                isLoading={isLoadingTrends}
                period={selectedPeriod}
              />
            </Card.Body>
          </Card.Root>

          {/* Resource Type Activity */}
          <Card.Root>
            <Card.Header>
              <HStack>
                <FiActivity />
                <VStack align="start" gap={1}>
                  <Heading size="lg">Resource Activity Breakdown</Heading>
                  <Text color="fg.muted">
                    Daily resource changes by activity type
                  </Text>
                </VStack>
              </HStack>
            </Card.Header>
            <Card.Body>
              {latestStats && (
                <SimpleGrid columns={{ base: 1, md: 3 }} gap={6}>
                  <VStack>
                    <Box
                      w={16}
                      h={16}
                      borderRadius="full"
                      bg="green.500"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                    >
                      <Text fontSize="2xl" fontWeight="bold" color="white">
                        {latestStats.daily_created_resources}
                      </Text>
                    </Box>
                    <VStack gap={1}>
                      <Text fontWeight="semibold" color="green.600">
                        Created
                      </Text>
                      <Text fontSize="sm" color="fg.muted">
                        New resources today
                      </Text>
                    </VStack>
                  </VStack>

                  <VStack>
                    <Box
                      w={16}
                      h={16}
                      borderRadius="full"
                      bg="blue.500"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                    >
                      <Text fontSize="2xl" fontWeight="bold" color="white">
                        {latestStats.daily_modified_resources}
                      </Text>
                    </Box>
                    <VStack gap={1}>
                      <Text fontWeight="semibold" color="blue.600">
                        Modified
                      </Text>
                      <Text fontSize="sm" color="fg.muted">
                        Updated resources today
                      </Text>
                    </VStack>
                  </VStack>

                  <VStack>
                    <Box
                      w={16}
                      h={16}
                      borderRadius="full"
                      bg="red.500"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                    >
                      <Text fontSize="2xl" fontWeight="bold" color="white">
                        {latestStats.daily_deleted_resources}
                      </Text>
                    </Box>
                    <VStack gap={1}>
                      <Text fontWeight="semibold" color="red.600">
                        Deleted
                      </Text>
                      <Text fontSize="sm" color="fg.muted">
                        Removed resources today
                      </Text>
                    </VStack>
                  </VStack>
                </SimpleGrid>
              )}
            </Card.Body>
          </Card.Root>
        </Stack>

        {/* Right Column - Breakdowns and Secondary Stats */}
        <ResourceBreakdownCharts
          stats={latestStats}
          isLoading={isLoadingStats}
        />
      </Grid>
    </Stack>
  )
}

export default EcosystemDashboard

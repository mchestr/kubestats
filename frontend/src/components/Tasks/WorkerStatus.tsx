import {
  Badge,
  Box,
  Button,
  Card,
  Flex,
  HStack,
  Heading,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { FiAlertCircle, FiEye, FiRefreshCw, FiServer } from "react-icons/fi"
import type { WorkerStatus as WorkerStatusType } from "./types"

interface WorkerStatusProps {
  workerStatus: WorkerStatusType | undefined
  workersLoading: boolean
  onRefresh: () => void
  onViewWorkerStats: (workerName: string) => void
}

export function WorkerStatus({
  workerStatus,
  workersLoading,
  onRefresh,
  onViewWorkerStats,
}: WorkerStatusProps) {
  const hasWorkers =
    workerStatus?.stats && Object.keys(workerStatus.stats).length > 0

  return (
    <Card.Root>
      <Card.Header>
        <HStack justify="space-between">
          <Heading size="md">
            <HStack>
              <FiServer />
              <Text>Workers</Text>
            </HStack>
          </Heading>
          <Button
            size="sm"
            variant="outline"
            onClick={onRefresh}
            loading={workersLoading}
          >
            <FiRefreshCw />
          </Button>
        </HStack>
      </Card.Header>
      <Card.Body>
        {workersLoading ? (
          <Flex justify="center" py={8}>
            <Spinner />
          </Flex>
        ) : hasWorkers ? (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
            {Object.entries(workerStatus.stats!)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([workerName, stats]: [string, any]) => {
                const activeTasks = workerStatus?.active?.[workerName] || []
                const taskCount = Array.isArray(activeTasks)
                  ? activeTasks.length
                  : 0

                return (
                  <Card.Root key={workerName} variant="outline">
                    <Card.Body>
                      <VStack gap={3} align="stretch">
                        <HStack justify="space-between">
                          <VStack gap={1} align="start">
                            <Text fontWeight="bold" fontSize="sm">
                              {workerName.replace(/^celery@/, "")}
                            </Text>
                            <Badge colorPalette="green" size="sm">
                              ONLINE
                            </Badge>
                          </VStack>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onViewWorkerStats(workerName)}
                          >
                            <FiEye />
                          </Button>
                        </HStack>

                        <VStack gap={2} align="stretch" fontSize="sm">
                          <HStack justify="space-between">
                            <Text color="gray.600">Active Tasks:</Text>
                            <Text fontWeight="medium">{taskCount}</Text>
                          </HStack>
                          <HStack justify="space-between">
                            <Text color="gray.600">Pool:</Text>
                            <Text fontWeight="medium">
                              {stats.pool?.max_concurrency || "N/A"}
                            </Text>
                          </HStack>
                          <HStack justify="space-between">
                            <Text color="gray.600">Processed:</Text>
                            <Text fontWeight="medium">
                              {stats.total
                                ? String(
                                    Object.values(stats.total).reduce(
                                      (a: any, b: any) => a + b,
                                      0,
                                    ),
                                  )
                                : "0"}
                            </Text>
                          </HStack>
                        </VStack>
                      </VStack>
                    </Card.Body>
                  </Card.Root>
                )
              })}
          </SimpleGrid>
        ) : (
          <Box p={6} bg="orange.50" borderRadius="md" textAlign="center">
            <FiAlertCircle
              size={24}
              color="orange"
              style={{ margin: "0 auto 8px" }}
            />
            <Text color="orange.700" fontWeight="medium">
              No workers found
            </Text>
            <Text color="orange.600" fontSize="sm">
              Make sure Celery workers are running
            </Text>
          </Box>
        )}
      </Card.Body>
    </Card.Root>
  )
}

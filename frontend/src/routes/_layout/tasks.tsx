import {
  Badge,
  Box,
  Button,
  Container,
  Flex,
  HStack,
  Heading,
  SimpleGrid,
  Spinner,
  Table,
  Text,
  VStack,
  Card,
} from "@chakra-ui/react"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import {
  FiActivity,
  FiClock,
  FiRefreshCw,
  FiUsers,
  FiServer,
  FiDatabase,
  FiList,
  FiAlertCircle,
  FiCheckCircle,
  FiZap,
  FiEye,
} from "react-icons/fi"

import { TasksService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/tasks")({
  component: Tasks,
})

interface SystemHealth {
  redis_status: string
  active_workers: number
  running_tasks: number
  queue_depth: number
  failed_tasks_24h: number
}

function Tasks() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [selectedWorkerData, setSelectedWorkerData] = useState<any>(null)
  const [workerStatsModalOpen, setWorkerStatsModalOpen] = useState(false)
  const [taskDetailsModalOpen, setTaskDetailsModalOpen] = useState(false)

  // Health check mutation
  const healthCheckMutation = useMutation({
    mutationFn: () => TasksService.tasksTriggerHealthCheck(),
    onSuccess: (data: any) => {
      showSuccessToast(`Health check ${data.task_id} started`)
      setSelectedTaskId(data.task_id)
      queryClient.invalidateQueries({ queryKey: ["tasks"] })
      queryClient.invalidateQueries({ queryKey: ["workers"] })
    },
    onError: (err: any) => {
      const errDetail = (err.body as any)?.detail
      showErrorToast(`${errDetail}`)
    },
  })

  // Trigger periodic task mutation
  const triggerPeriodicTaskMutation = useMutation({
    mutationFn: (taskName: string) => 
      TasksService.tasksTriggerPeriodicTask({ path: { task_name: taskName } }),
    onSuccess: (data: any) => {
      showSuccessToast(`Task ${data.task_id} triggered successfully`)
      setSelectedTaskId(data.task_id)
      queryClient.invalidateQueries({ queryKey: ["tasks"] })
      queryClient.invalidateQueries({ queryKey: ["workers"] })
    },
    onError: (err: any) => {
      const errDetail = (err.body as any)?.detail
      showErrorToast(`${errDetail}`)
    },
  })

  // Get task status for selected task
  const { data: taskStatus, isLoading: statusLoading } = useQuery({
    queryKey: ["taskStatus", selectedTaskId],
    queryFn: async () => {
      if (!selectedTaskId) return null
      const response = await TasksService.tasksGetTaskStatus({
        path: { task_id: selectedTaskId },
      })
      return response.data as any
    },
    enabled: !!selectedTaskId,
    refetchInterval: 2000, // Refetch every 2 seconds
  })

  // Get worker status (which now includes periodic tasks)
  const { data: workerStatus, isLoading: workersLoading } = useQuery({
    queryKey: ["workers"],
    queryFn: async () => {
      const response = await TasksService.tasksGetWorkerStatus()
      return response.data as any
    },
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  const handleHealthCheck = () => {
    healthCheckMutation.mutate()
  }

  const handleTriggerPeriodicTask = (taskName: string) => {
    triggerPeriodicTaskMutation.mutate(taskName)
  }

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case "SUCCESS":
        return "green"
      case "FAILURE":
        return "red"
      case "PENDING":
        return "yellow"
      case "RETRY":
        return "orange"
      case "REVOKED":
        return "gray"
      default:
        return "blue"
    }
  }

  const renderTaskResult = (result: unknown): string => {
    try {
      return JSON.stringify(result, null, 2)
    } catch {
      return String(result)
    }
  }

  const handleViewWorkerStats = (workerName: string) => {
    const workerStats = workerStatus?.stats?.[workerName]
    if (workerStats) {
      setSelectedWorkerData({
        worker_name: workerName,
        worker_id: workerName.replace(/^celery@/, ""),
        status: "ONLINE",
        ...workerStats
      })
      setWorkerStatsModalOpen(true)
    }
  }

  const handleViewTaskDetails = (taskId: string) => {
    setSelectedTaskId(taskId)
    setTaskDetailsModalOpen(true)
  }

  // Calculate system health metrics
  const systemHealth: SystemHealth = {
    redis_status: "healthy", // Would come from backend
    active_workers: workerStatus?.active ? Object.keys(workerStatus.active).length : 0,
    running_tasks: workerStatus?.active 
      ? Object.values(workerStatus.active).reduce((total: number, tasks: any) => 
          total + (Array.isArray(tasks) ? tasks.length : 0), 0)
      : 0,
    queue_depth: 0, // Would need to be calculated from backend
    failed_tasks_24h: 0, // Would need to be calculated from backend
  }

  return (
    <Container maxW="full" py={4}>
      <VStack gap={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" textAlign={{ base: "center", md: "left" }}>
            Celery Task Management
          </Heading>
          <Text color="gray.500">Monitor workers, tasks, and system health</Text>
        </Box>

        {/* System Health Overview */}
        <Box>
          <Heading size="md" mb={4}>
            <HStack>
              <FiActivity />
              <Text>System Health</Text>
            </HStack>
          </Heading>
          <SimpleGrid columns={{ base: 2, md: 5 }} gap={4}>
            {/* Redis Status */}
            <Card.Root>
              <Card.Body>
                <VStack gap={2}>
                  <HStack>
                    <FiDatabase color="green" />
                    <Text fontSize="sm" fontWeight="medium">Redis</Text>
                  </HStack>
                  <Badge colorPalette="green" size="sm">
                    {systemHealth.redis_status}
                  </Badge>
                </VStack>
              </Card.Body>
            </Card.Root>

            {/* Active Workers */}
            <Card.Root>
              <Card.Body>
                <VStack gap={2}>
                  <HStack>
                    <FiUsers color="blue" />
                    <Text fontSize="sm" fontWeight="medium">Workers</Text>
                  </HStack>
                  <Text fontSize="xl" fontWeight="bold">
                    {systemHealth.active_workers}
                  </Text>
                </VStack>
              </Card.Body>
            </Card.Root>

            {/* Running Tasks */}
            <Card.Root>
              <Card.Body>
                <VStack gap={2}>
                  <HStack>
                    <FiZap color="orange" />
                    <Text fontSize="sm" fontWeight="medium">Running</Text>
                  </HStack>
                  <Text fontSize="xl" fontWeight="bold">
                    {systemHealth.running_tasks}
                  </Text>
                </VStack>
              </Card.Body>
            </Card.Root>

            {/* Queue Depth */}
            <Card.Root>
              <Card.Body>
                <VStack gap={2}>
                  <HStack>
                    <FiList color="purple" />
                    <Text fontSize="sm" fontWeight="medium">Queued</Text>
                  </HStack>
                  <Text fontSize="xl" fontWeight="bold">
                    {systemHealth.queue_depth}
                  </Text>
                </VStack>
              </Card.Body>
            </Card.Root>

            {/* Failed Tasks */}
            <Card.Root>
              <Card.Body>
                <VStack gap={2}>
                  <HStack>
                    <FiAlertCircle color="red" />
                    <Text fontSize="sm" fontWeight="medium">Failed (24h)</Text>
                  </HStack>
                  <Text fontSize="xl" fontWeight="bold">
                    {systemHealth.failed_tasks_24h}
                  </Text>
                </VStack>
              </Card.Body>
            </Card.Root>
          </SimpleGrid>
        </Box>

        {/* Task Operations */}
        <Card.Root>
          <Card.Header>
            <Heading size="md">
              <HStack>
                <FiZap />
                <Text>Quick Actions</Text>
              </HStack>
            </Heading>
          </Card.Header>
          <Card.Body>
            <VStack gap={3}>
              <Button
                colorPalette="green"
                onClick={handleHealthCheck}
                loading={healthCheckMutation.isPending}
                width="full"
              >
                <FiActivity />
                Run Health Check
              </Button>
              <Button
                colorPalette="blue"
                onClick={() => queryClient.invalidateQueries({ queryKey: ["workers"] })}
                loading={workersLoading}
                width="full"
              >
                <FiRefreshCw />
                Refresh All Data
              </Button>
            </VStack>
          </Card.Body>
        </Card.Root>

        {/* Active Tasks Monitor */}
        <Card.Root>
          <Card.Header>
            <HStack justify="space-between">
              <Heading size="md">
                <HStack>
                  <FiZap />
                  <Text>Active Tasks</Text>
                </HStack>
              </Heading>
              <Button
                size="sm"
                variant="outline"
                onClick={() => queryClient.invalidateQueries({ queryKey: ["workers"] })}
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
            ) : workerStatus?.active && Object.keys(workerStatus.active).length > 0 ? (
              <Table.Root variant="outline">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>Task ID</Table.ColumnHeader>
                    <Table.ColumnHeader>Task Name</Table.ColumnHeader>
                    <Table.ColumnHeader>Worker</Table.ColumnHeader>
                    <Table.ColumnHeader>Started</Table.ColumnHeader>
                    <Table.ColumnHeader>Actions</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {Object.entries(workerStatus.active).map(([workerName, tasks]) =>
                    Array.isArray(tasks) ? tasks.map((task: any, index: number) => (
                      <Table.Row key={`${workerName}-${index}`}>
                        <Table.Cell>
                          <Text fontFamily="mono" fontSize="sm">
                            {task.id?.substring(0, 8) || 'N/A'}...
                          </Text>
                        </Table.Cell>
                        <Table.Cell>
                          <Text fontWeight="medium">{task.name || 'Unknown'}</Text>
                        </Table.Cell>
                        <Table.Cell>
                          <Badge size="sm" colorPalette="blue">
                            {workerName.replace(/^celery@/, '')}
                          </Badge>
                        </Table.Cell>
                        <Table.Cell>
                          <Text fontSize="sm" color="gray.600">
                            {task.time_start ? new Date(task.time_start * 1000).toLocaleTimeString() : 'N/A'}
                          </Text>
                        </Table.Cell>
                        <Table.Cell>
                          <HStack gap={2}>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleViewTaskDetails(task.id)}
                            >
                              <FiEye />
                            </Button>
                          </HStack>
                        </Table.Cell>
                      </Table.Row>
                    )) : []
                  )}
                </Table.Body>
              </Table.Root>
            ) : (
              <Box
                p={6}
                bg="blue.50"
                borderRadius="md"
                textAlign="center"
              >
                <FiCheckCircle size={24} color="blue" style={{ margin: "0 auto 8px" }} />
                <Text color="blue.700" fontWeight="medium">
                  No active tasks
                </Text>
                <Text color="blue.600" fontSize="sm">
                  All workers are idle and ready for new tasks
                </Text>
              </Box>
            )}
          </Card.Body>
        </Card.Root>

        {/* Worker Status */}
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
                onClick={() => queryClient.invalidateQueries({ queryKey: ["workers"] })}
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
            ) : workerStatus?.stats && Object.keys(workerStatus.stats).length > 0 ? (
              <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
                {Object.entries(workerStatus.stats).map(([workerName, stats]: [string, any]) => {
                  const activeTasks = workerStatus?.active?.[workerName] || []
                  const taskCount = Array.isArray(activeTasks) ? activeTasks.length : 0
                  
                  return (
                    <Card.Root key={workerName} variant="outline">
                      <Card.Body>
                        <VStack gap={3} align="stretch">
                          <HStack justify="space-between">
                            <VStack gap={1} align="start">
                              <Text fontWeight="bold" fontSize="sm">
                                {workerName.replace(/^celery@/, '')}
                              </Text>
                              <Badge colorPalette="green" size="sm">
                                ONLINE
                              </Badge>
                            </VStack>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleViewWorkerStats(workerName)}
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
                              <Text fontWeight="medium">{stats.pool?.max_concurrency || 'N/A'}</Text>
                            </HStack>
                            <HStack justify="space-between">
                              <Text color="gray.600">Processed:</Text>
                              <Text fontWeight="medium">
                                {stats.total ? String(Object.values(stats.total).reduce((a: any, b: any) => a + b, 0)) : '0'}
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
              <Box
                p={6}
                bg="orange.50"
                borderRadius="md"
                textAlign="center"
              >
                <FiAlertCircle size={24} color="orange" style={{ margin: "0 auto 8px" }} />
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

        {/* Periodic Tasks */}
        <Card.Root>
          <Card.Header>
            <HStack justify="space-between">
              <Heading size="md">
                <HStack>
                  <FiClock />
                  <Text>Periodic Tasks</Text>
                </HStack>
              </Heading>
              <Button
                size="sm"
                variant="outline"
                onClick={() => queryClient.invalidateQueries({ queryKey: ["workers"] })}
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
            ) : workerStatus?.periodic_tasks && workerStatus.periodic_tasks.length > 0 ? (
              <Table.Root variant="outline">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>Task Name</Table.ColumnHeader>
                    <Table.ColumnHeader>Schedule</Table.ColumnHeader>
                    <Table.ColumnHeader>Status</Table.ColumnHeader>
                    <Table.ColumnHeader>Run Count</Table.ColumnHeader>
                    <Table.ColumnHeader>Actions</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {workerStatus.periodic_tasks.map((task: any) => (
                    <Table.Row key={task.name}>
                      <Table.Cell>
                        <VStack gap={1} align="start">
                          <Text fontWeight="medium">{task.name}</Text>
                          <Text fontSize="sm" color="gray.600">{task.task}</Text>
                        </VStack>
                      </Table.Cell>
                      <Table.Cell>
                        <Text fontSize="sm" fontFamily="mono" color="gray.600">
                          {task.schedule}
                        </Text>
                      </Table.Cell>
                      <Table.Cell>
                        <Badge
                          colorPalette={task.enabled ? "green" : "red"}
                          size="sm"
                        >
                          {task.enabled ? "Enabled" : "Disabled"}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell>
                        {task.total_run_count ? (
                          <Badge colorPalette="blue" size="sm">
                            {task.total_run_count}
                          </Badge>
                        ) : (
                          <Text color="gray.500" fontSize="sm">
                            0
                          </Text>
                        )}
                      </Table.Cell>
                      <Table.Cell>
                        <Button 
                          size="sm" 
                          variant="outline"
                          colorPalette="green"
                          onClick={() => handleTriggerPeriodicTask(task.name)}
                          loading={triggerPeriodicTaskMutation.isPending}
                        >
                          <FiZap />
                          Trigger Now
                        </Button>
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            ) : (
              <Box
                p={6}
                bg="blue.50"
                borderRadius="md"
                textAlign="center"
              >
                <FiClock size={24} color="blue" style={{ margin: "0 auto 8px" }} />
                <Text color="blue.700" fontWeight="medium">
                  No periodic tasks configured
                </Text>
                <Text color="blue.600" fontSize="sm">
                  Scheduled tasks will appear here
                </Text>
              </Box>
            )}
          </Card.Body>
        </Card.Root>

        {/* Task Details Modal */}
        <DialogRoot
          open={taskDetailsModalOpen}
          onOpenChange={(e) => setTaskDetailsModalOpen(e.open)}
        >
          <DialogContent maxW="4xl">
            <DialogHeader>
              <DialogTitle>
                Task Details: {selectedTaskId?.substring(0, 8)}...
              </DialogTitle>
            </DialogHeader>
            <DialogCloseTrigger />
            
            <DialogBody>
              {statusLoading ? (
                <Flex justify="center" py={8}>
                  <Spinner />
                </Flex>
              ) : taskStatus ? (
                <VStack gap={4} align="stretch">
                  <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                    <VStack gap={3} align="stretch">
                      <Box>
                        <Text fontWeight="bold" mb={2}>Basic Information</Text>
                        <VStack gap={2} align="stretch">
                          <HStack>
                            <Text fontWeight="medium" minW="100px">Status:</Text>
                            <Badge colorPalette={getStatusColor(taskStatus.status)}>
                              {taskStatus.status}
                            </Badge>
                          </HStack>
                          <HStack>
                            <Text fontWeight="medium" minW="100px">Task ID:</Text>
                            <Text fontFamily="mono" fontSize="sm">{selectedTaskId}</Text>
                          </HStack>
                          {taskStatus.name && (
                            <HStack>
                              <Text fontWeight="medium" minW="100px">Name:</Text>
                              <Text>{taskStatus.name}</Text>
                            </HStack>
                          )}
                          {taskStatus.worker && (
                            <HStack>
                              <Text fontWeight="medium" minW="100px">Worker:</Text>
                              <Text>{taskStatus.worker}</Text>
                            </HStack>
                          )}
                        </VStack>
                      </Box>
                    </VStack>

                    <VStack gap={3} align="stretch">
                      {taskStatus.date_done && (
                        <Box>
                          <Text fontWeight="bold" mb={2}>Timing</Text>
                          <VStack gap={2} align="stretch">
                            <HStack>
                              <Text fontWeight="medium" minW="100px">Completed:</Text>
                              <Text fontSize="sm">{new Date(taskStatus.date_done).toLocaleString()}</Text>
                            </HStack>
                            {taskStatus.retries !== null && (
                              <HStack>
                                <Text fontWeight="medium" minW="100px">Retries:</Text>
                                <Text>{taskStatus.retries}</Text>
                              </HStack>
                            )}
                          </VStack>
                        </Box>
                      )}
                    </VStack>
                  </SimpleGrid>

                  {taskStatus.result != null && (
                    <Box>
                      <Text fontWeight="bold" mb={2}>Result</Text>
                      <Box
                        p={3}
                        bg="gray.50"
                        borderRadius="md"
                        fontFamily="mono"
                        fontSize="sm"
                        overflowX="auto"
                        maxH="300px"
                        overflowY="auto"
                      >
                        <pre>{renderTaskResult(taskStatus.result)}</pre>
                      </Box>
                    </Box>
                  )}

                  {taskStatus.traceback && (
                    <Box>
                      <Text fontWeight="bold" mb={2} color="red.500">Error Details</Text>
                      <Box
                        p={3}
                        bg="red.50"
                        borderRadius="md"
                        fontFamily="mono"
                        fontSize="sm"
                        overflowX="auto"
                        maxH="300px"
                        overflowY="auto"
                      >
                        <pre>{taskStatus.traceback}</pre>
                      </Box>
                    </Box>
                  )}
                </VStack>
              ) : (
                <Box
                  p={6}
                  bg="red.50"
                  borderRadius="md"
                  textAlign="center"
                >
                  <Text color="red.700">Failed to load task details</Text>
                </Box>
              )}
            </DialogBody>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setTaskDetailsModalOpen(false)}
              >
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </DialogRoot>

        {/* Worker Stats Modal */}
        <DialogRoot
          open={workerStatsModalOpen}
          onOpenChange={(e) => setWorkerStatsModalOpen(e.open)}
        >
          <DialogContent maxW="4xl">
            <DialogHeader>
              <DialogTitle>
                Worker Details: {selectedWorkerData?.worker_id || "N/A"}
              </DialogTitle>
            </DialogHeader>
            <DialogCloseTrigger />
            
            <DialogBody>
              {selectedWorkerData ? (
                <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                  <VStack gap={4} align="stretch">
                    <Box>
                      <Text fontWeight="bold" mb={2}>Basic Information</Text>
                      <VStack gap={2} align="stretch">
                        <HStack>
                          <Text fontWeight="medium" minW="120px">Worker Name:</Text>
                          <Text>{selectedWorkerData.worker_name}</Text>
                        </HStack>
                        <HStack>
                          <Text fontWeight="medium" minW="120px">Status:</Text>
                          <Badge colorPalette="green">{selectedWorkerData.status}</Badge>
                        </HStack>
                        <HStack>
                          <Text fontWeight="medium" minW="120px">PID:</Text>
                          <Text>{selectedWorkerData.pid || "N/A"}</Text>
                        </HStack>
                        <HStack>
                          <Text fontWeight="medium" minW="120px">Uptime:</Text>
                          <Text>
                            {selectedWorkerData.uptime
                              ? `${Math.floor(selectedWorkerData.uptime / 60)} minutes`
                              : "N/A"}
                          </Text>
                        </HStack>
                      </VStack>
                    </Box>

                    <Box>
                      <Text fontWeight="bold" mb={2}>Configuration</Text>
                      <VStack gap={2} align="stretch">
                        <HStack>
                          <Text fontWeight="medium" minW="120px">Clock:</Text>
                          <Text>{selectedWorkerData.clock || "N/A"}</Text>
                        </HStack>
                        <HStack>
                          <Text fontWeight="medium" minW="120px">Prefetch Count:</Text>
                          <Text>{selectedWorkerData.prefetch_count || "N/A"}</Text>
                        </HStack>
                      </VStack>
                    </Box>
                  </VStack>

                  <VStack gap={4} align="stretch">
                    {selectedWorkerData.pool && (
                      <Box>
                        <Text fontWeight="bold" mb={2}>Pool Information</Text>
                        <Box
                          p={3}
                          bg="gray.50"
                          borderRadius="md"
                          fontFamily="mono"
                          fontSize="sm"
                          overflowX="auto"
                          maxH="200px"
                          overflowY="auto"
                        >
                          <pre>{JSON.stringify(selectedWorkerData.pool, null, 2)}</pre>
                        </Box>
                      </Box>
                    )}

                    {selectedWorkerData.total_tasks && (
                      <Box>
                        <Text fontWeight="bold" mb={2}>Task Statistics</Text>
                        <Box
                          p={3}
                          bg="blue.50"
                          borderRadius="md"
                          fontFamily="mono"
                          fontSize="sm"
                          overflowX="auto"
                          maxH="200px"
                          overflowY="auto"
                        >
                          <pre>{JSON.stringify(selectedWorkerData.total_tasks, null, 2)}</pre>
                        </Box>
                      </Box>
                    )}
                  </VStack>
                </SimpleGrid>
              ) : (
                <Box
                  p={4}
                  bg="red.50"
                  borderRadius="md"
                  borderLeftWidth="4px"
                  borderLeftColor="red.500"
                >
                  <Text color="red.700">No worker data available</Text>
                </Box>
              )}
            </DialogBody>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setWorkerStatsModalOpen(false)}
              >
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </DialogRoot>
      </VStack>
    </Container>
  )
}

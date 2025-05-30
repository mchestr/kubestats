import {
  Badge,
  Box,
  Button,
  Container,
  Flex,
  HStack,
  Heading,
  Input,
  SimpleGrid,
  Spinner,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import {
  FiActivity,
  FiClock,
  FiPlay,
  FiRefreshCw,
  FiUsers,
} from "react-icons/fi"

import { type TaskTriggerRequest, TasksService } from "@/client"
import { Field } from "@/components/ui/field"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/tasks")({
  component: Tasks,
})

function Tasks() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [taskType, setTaskType] = useState("log")
  const [message, setMessage] = useState("Test message from frontend")
  const [logLevel, setLogLevel] = useState("INFO")
  const [duration, setDuration] = useState(3)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [selectedWorkerId, setSelectedWorkerId] = useState<string | null>(null)
  const [workerStatsVisible, setWorkerStatsVisible] = useState(false)

  // Trigger task mutation
  const triggerTaskMutation = useMutation({
    mutationFn: (data: TaskTriggerRequest) =>
      TasksService.tasksTriggerLogTask({ body: data }),
    onSuccess: (data: any) => {
      showSuccessToast(`Task ${data.task_id} triggered successfully`)
      setSelectedTaskId(data.task_id)
      queryClient.invalidateQueries({ queryKey: ["tasks"] })
    },
    onError: (err: any) => {
      const errDetail = (err.body as any)?.detail
      showErrorToast(`${errDetail}`)
    },
  })

  // Health check mutation
  const healthCheckMutation = useMutation({
    mutationFn: () => TasksService.tasksTriggerHealthCheck(),
    onSuccess: (data: any) => {
      showSuccessToast(`Health check ${data.task_id} started`)
      setSelectedTaskId(data.task_id)
      queryClient.invalidateQueries({ queryKey: ["tasks"] })
    },
    onError: (err: any) => {
      const errDetail = (err.body as any)?.detail
      showErrorToast(`${errDetail}`)
    },
  })

  // Get worker stats for selected worker
  const { data: workerStats, isLoading: workerStatsLoading } = useQuery({
    queryKey: ["workerStats", selectedWorkerId],
    queryFn: async () => {
      if (!selectedWorkerId) return null
      const response = await TasksService.tasksGetWorkerStats({
        path: { worker_id: selectedWorkerId },
      })
      return response.data as any
    },
    enabled: !!selectedWorkerId,
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

  // Get worker status
  const { data: workerStatus, isLoading: workersLoading } = useQuery({
    queryKey: ["workers"],
    queryFn: async () => {
      const response = await TasksService.tasksGetWorkerStatus()
      return response.data as any
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  })

  // Get periodic tasks
  const { data: periodicTasks, isLoading: periodicTasksLoading } = useQuery({
    queryKey: ["periodicTasks"],
    queryFn: async () => {
      const response = await TasksService.tasksGetPeriodicTasks()
      return response.data as any
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const handleTriggerTask = () => {
    triggerTaskMutation.mutate({
      message: message,
      log_level: logLevel,
      duration: duration,
    })
  }

  const handleHealthCheck = () => {
    healthCheckMutation.mutate()
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

  const extractWorkerId = (workerName: string): string => {
    // Remove 'celery@' prefix to get clean worker ID
    return workerName.replace(/^celery@/, "")
  }

  const handleViewWorkerStats = (workerName: string) => {
    const workerId = extractWorkerId(workerName)
    setSelectedWorkerId(workerId)
    setWorkerStatsVisible(true)
  }

  return (
    <Container maxW="full" py={4}>
      <VStack gap={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" textAlign={{ base: "center", md: "left" }}>
            Task Management
          </Heading>
          <Text color="gray.500">Trigger and monitor Celery tasks</Text>
        </Box>

        {/* Task Controls */}
        <SimpleGrid columns={{ base: 1, lg: 2 }} gap={6}>
          {/* Trigger Task Card */}
          <Box bg="white" p={6} borderRadius="lg" shadow="sm" borderWidth="1px">
            <Heading size="md" mb={4}>
              <HStack>
                <FiPlay />
                <Text>Trigger Task</Text>
              </HStack>
            </Heading>
            <VStack gap={4} align="stretch">
              <Field label="Task Type">
                <select
                  value={taskType}
                  onChange={(e) => setTaskType(e.target.value)}
                  style={{
                    padding: "8px",
                    borderRadius: "6px",
                    border: "1px solid #e2e8f0",
                    width: "100%",
                  }}
                >
                  <option value="log">Log Entry Task</option>
                </select>
              </Field>

              <Field label="Message">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Enter task message"
                />
              </Field>

              <Field label="Log Level">
                <select
                  value={logLevel}
                  onChange={(e) => setLogLevel(e.target.value)}
                  style={{
                    padding: "8px",
                    borderRadius: "6px",
                    border: "1px solid #e2e8f0",
                    width: "100%",
                  }}
                >
                  <option value="DEBUG">DEBUG</option>
                  <option value="INFO">INFO</option>
                  <option value="WARNING">WARNING</option>
                  <option value="ERROR">ERROR</option>
                </select>
              </Field>

              <Field label="Duration (seconds)">
                <Input
                  type="number"
                  value={duration}
                  onChange={(e) =>
                    setDuration(Number.parseInt(e.target.value) || 1)
                  }
                  min={1}
                  max={60}
                />
              </Field>

              <Button
                colorPalette="blue"
                onClick={handleTriggerTask}
                loading={triggerTaskMutation.isPending}
              >
                <FiPlay />
                Trigger Task
              </Button>
            </VStack>
          </Box>

          {/* System Tasks Card */}
          <Box bg="white" p={6} borderRadius="lg" shadow="sm" borderWidth="1px">
            <Heading size="md" mb={4}>
              <HStack>
                <FiActivity />
                <Text>System Tasks</Text>
              </HStack>
            </Heading>
            <VStack gap={4} align="stretch">
              <Button
                colorPalette="green"
                onClick={handleHealthCheck}
                loading={healthCheckMutation.isPending}
              >
                <FiActivity />
                Run Health Check
              </Button>

              <Box
                p={3}
                bg="blue.50"
                borderRadius="md"
                borderLeftWidth="4px"
                borderLeftColor="blue.500"
              >
                <Text fontWeight="bold" color="blue.700" mb={1}>
                  Health Check
                </Text>
                <Text fontSize="sm" color="blue.600">
                  Monitors Redis connection and system resources
                </Text>
              </Box>
            </VStack>
          </Box>
        </SimpleGrid>

        {/* Worker Status */}
        <Box bg="white" p={6} borderRadius="lg" shadow="sm" borderWidth="1px">
          <HStack justify="space-between" mb={4}>
            <Heading size="md">
              <HStack>
                <FiUsers />
                <Text>Worker Status</Text>
              </HStack>
            </Heading>
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                queryClient.invalidateQueries({ queryKey: ["workers"] })
              }
              loading={workersLoading}
            >
              <FiRefreshCw />
              Refresh
            </Button>
          </HStack>

          {workersLoading ? (
            <Flex justify="center">
              <Spinner />
            </Flex>
          ) : workerStatus?.active &&
            Object.keys(workerStatus.active).length > 0 ? (
            <Table.Root variant="outline">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>Worker</Table.ColumnHeader>
                  <Table.ColumnHeader>Status</Table.ColumnHeader>
                  <Table.ColumnHeader>Active Tasks</Table.ColumnHeader>
                  <Table.ColumnHeader>Processed</Table.ColumnHeader>
                  <Table.ColumnHeader>Actions</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {Object.entries(workerStatus.data?.active || {}).map(
                  ([workerName, tasks]) => (
                    <Table.Row key={workerName}>
                      <Table.Cell>{workerName}</Table.Cell>
                      <Table.Cell>
                        <Badge colorPalette="green">online</Badge>
                      </Table.Cell>
                      <Table.Cell>
                        {Array.isArray(tasks) ? tasks.length : 0}
                      </Table.Cell>
                      <Table.Cell>-</Table.Cell>
                      <Table.Cell>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleViewWorkerStats(workerName)}
                        >
                          View Stats
                        </Button>
                      </Table.Cell>
                    </Table.Row>
                  ),
                )}
              </Table.Body>
            </Table.Root>
          ) : (
            <Box
              p={3}
              bg="orange.50"
              borderRadius="md"
              borderLeftWidth="4px"
              borderLeftColor="orange.500"
            >
              <Text color="orange.700">
                No workers found. Make sure Celery workers are running.
              </Text>
            </Box>
          )}
        </Box>

        {/* Periodic Tasks */}
        <Box bg="white" p={6} borderRadius="lg" shadow="sm" borderWidth="1px">
          <HStack justify="space-between" mb={4}>
            <Heading size="md">
              <HStack>
                <FiClock />
                <Text>Periodic Tasks</Text>
              </HStack>
            </Heading>
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                queryClient.invalidateQueries({ queryKey: ["periodicTasks"] })
              }
              loading={periodicTasksLoading}
            >
              <FiRefreshCw />
              Refresh
            </Button>
          </HStack>

          {periodicTasksLoading ? (
            <Flex justify="center">
              <Spinner />
            </Flex>
          ) : periodicTasks && periodicTasks.length > 0 ? (
            <Table.Root variant="outline">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>Task Name</Table.ColumnHeader>
                  <Table.ColumnHeader>Schedule</Table.ColumnHeader>
                  <Table.ColumnHeader>Status</Table.ColumnHeader>
                  <Table.ColumnHeader>Last Run</Table.ColumnHeader>
                  <Table.ColumnHeader>Run Count</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {periodicTasks.map((task: any) => (
                  <Table.Row key={task.name}>
                    <Table.Cell>
                      <VStack align="start" gap={1}>
                        <Text fontWeight="medium">{task.name}</Text>
                        <Text fontSize="sm" color="gray.500">
                          {task.task}
                        </Text>
                      </VStack>
                    </Table.Cell>
                    <Table.Cell>
                      <Text fontSize="sm">{task.schedule}</Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Badge colorPalette={task.enabled ? "green" : "gray"}>
                        {task.enabled ? "enabled" : "disabled"}
                      </Badge>
                    </Table.Cell>
                    <Table.Cell>
                      <Text fontSize="sm" color="gray.500">
                        {task.last_run_at || "Never"}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text fontSize="sm">{task.total_run_count || 0}</Text>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          ) : (
            <Box
              p={3}
              bg="blue.50"
              borderRadius="md"
              borderLeftWidth="4px"
              borderLeftColor="blue.500"
            >
              <Text color="blue.700">No periodic tasks configured.</Text>
            </Box>
          )}
        </Box>

        {/* Task Status */}
        {selectedTaskId && (
          <Box bg="white" p={6} borderRadius="lg" shadow="sm" borderWidth="1px">
            <Heading size="md" mb={4}>
              Task Status: {selectedTaskId}
            </Heading>

            {statusLoading ? (
              <Flex justify="center">
                <Spinner />
              </Flex>
            ) : taskStatus ? (
              <VStack gap={4} align="stretch">
                <HStack>
                  <Text fontWeight="bold">Status:</Text>
                  <Badge colorPalette={getStatusColor(taskStatus.status)}>
                    {taskStatus.status}
                  </Badge>
                </HStack>

                {taskStatus.name && (
                  <HStack>
                    <Text fontWeight="bold">Task Name:</Text>
                    <Text>{taskStatus.name}</Text>
                  </HStack>
                )}

                {taskStatus.worker && (
                  <HStack>
                    <Text fontWeight="bold">Worker:</Text>
                    <Text>{taskStatus.worker}</Text>
                  </HStack>
                )}

                {taskStatus.result != null && (
                  <Box>
                    <Text fontWeight="bold" mb={2}>
                      Result:
                    </Text>
                    <Box
                      p={3}
                      bg="gray.50"
                      borderRadius="md"
                      fontFamily="mono"
                      fontSize="sm"
                      overflowX="auto"
                    >
                      <pre>{renderTaskResult(taskStatus.result)}</pre>
                    </Box>
                  </Box>
                )}

                {taskStatus.traceback && (
                  <Box>
                    <Text fontWeight="bold" mb={2} color="red.500">
                      Error:
                    </Text>
                    <Box
                      p={3}
                      bg="red.50"
                      borderRadius="md"
                      fontFamily="mono"
                      fontSize="sm"
                      overflowX="auto"
                    >
                      <pre>{taskStatus.traceback}</pre>
                    </Box>
                  </Box>
                )}
              </VStack>
            ) : (
              <Box
                p={3}
                bg="red.50"
                borderRadius="md"
                borderLeftWidth="4px"
                borderLeftColor="red.500"
              >
                <Text color="red.700">Failed to load task status</Text>
              </Box>
            )}
          </Box>
        )}

        {/* Worker Stats Details */}
        {workerStatsVisible && selectedWorkerId && (
          <Box bg="white" p={6} borderRadius="lg" shadow="sm" borderWidth="1px">
            <HStack justify="space-between" mb={4}>
              <Heading size="md">Worker Stats: {selectedWorkerId}</Heading>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setWorkerStatsVisible(false)
                  setSelectedWorkerId(null)
                }}
              >
                Close Stats
              </Button>
            </HStack>

            {workerStatsLoading ? (
              <Flex justify="center">
                <Spinner />
              </Flex>
            ) : workerStats ? (
              <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                <VStack gap={3} align="stretch">
                  <HStack>
                    <Text fontWeight="bold">Worker Name:</Text>
                    <Text>{workerStats.worker_name}</Text>
                  </HStack>
                  <HStack>
                    <Text fontWeight="bold">Status:</Text>
                    <Badge colorPalette="green">{workerStats.status}</Badge>
                  </HStack>
                  <HStack>
                    <Text fontWeight="bold">PID:</Text>
                    <Text>{workerStats.pid || "N/A"}</Text>
                  </HStack>
                  <HStack>
                    <Text fontWeight="bold">Uptime:</Text>
                    <Text>
                      {workerStats.uptime
                        ? `${Math.floor(workerStats.uptime / 60)} minutes`
                        : "N/A"}
                    </Text>
                  </HStack>
                </VStack>

                <VStack gap={3} align="stretch">
                  <HStack>
                    <Text fontWeight="bold">Clock:</Text>
                    <Text>{workerStats.clock || "N/A"}</Text>
                  </HStack>
                  <HStack>
                    <Text fontWeight="bold">Prefetch Count:</Text>
                    <Text>{workerStats.prefetch_count || "N/A"}</Text>
                  </HStack>

                  {workerStats.pool && (
                    <Box>
                      <Text fontWeight="bold" mb={2}>
                        Pool Info:
                      </Text>
                      <Box
                        p={3}
                        bg="gray.50"
                        borderRadius="md"
                        fontFamily="mono"
                        fontSize="sm"
                        overflowX="auto"
                      >
                        <pre>{JSON.stringify(workerStats.pool, null, 2)}</pre>
                      </Box>
                    </Box>
                  )}

                  {workerStats.total_tasks && (
                    <Box>
                      <Text fontWeight="bold" mb={2}>
                        Task Stats:
                      </Text>
                      <Box
                        p={3}
                        bg="blue.50"
                        borderRadius="md"
                        fontFamily="mono"
                        fontSize="sm"
                        overflowX="auto"
                      >
                        <pre>
                          {JSON.stringify(workerStats.total_tasks, null, 2)}
                        </pre>
                      </Box>
                    </Box>
                  )}
                </VStack>
              </SimpleGrid>
            ) : (
              <Box
                p={3}
                bg="red.50"
                borderRadius="md"
                borderLeftWidth="4px"
                borderLeftColor="red.500"
              >
                <Text color="red.700">
                  Failed to load worker stats for {selectedWorkerId}
                </Text>
              </Box>
            )}
          </Box>
        )}
      </VStack>
    </Container>
  )
}

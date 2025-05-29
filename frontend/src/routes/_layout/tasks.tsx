import {
  Box,
  Container,
  Flex,
  Heading,
  SimpleGrid,
  Text,
  VStack,
  HStack,
  Badge,
  Button,
  Input,
  Table,
  EmptyState,
  Spinner,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { FiPlay, FiActivity, FiUsers, FiRefreshCw } from "react-icons/fi"

import { ApiError, TasksService, TaskStatusResponse, TaskTriggerRequest } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { Field } from "@/components/ui/field"



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



  // Trigger task mutation
  const triggerTaskMutation = useMutation({
    mutationFn: (data: TaskTriggerRequest) =>
      TasksService.triggerLogTask({ requestBody: data }),
    onSuccess: (data: any) => {
      showSuccessToast(`Task ${data.task_id} triggered successfully`)
      setSelectedTaskId(data.task_id)
      queryClient.invalidateQueries({ queryKey: ["tasks"] })
    },
    onError: (err: ApiError) => {
      const errDetail = (err.body as any)?.detail
      showErrorToast(`${errDetail}`)
    },
  })

  // Health check mutation
  const healthCheckMutation = useMutation({
    mutationFn: () => TasksService.triggerHealthCheck(),
    onSuccess: (data: any) => {
      showSuccessToast(`Health check ${data.task_id} started`)
      setSelectedTaskId(data.task_id)
      queryClient.invalidateQueries({ queryKey: ["tasks"] })
    },
    onError: (err: ApiError) => {
      const errDetail = (err.body as any)?.detail
      showErrorToast(`${errDetail}`)
    },
  })

  // Get task list
  const {
    data: taskList,
    isLoading: tasksLoading,
    refetch: refetchTasks,
  } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => TasksService.listTasks(),
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  // Get task status for selected task
  const { data: taskStatus, isLoading: statusLoading } = useQuery({
    queryKey: ["taskStatus", selectedTaskId],
    queryFn: () => selectedTaskId ? TasksService.getTaskStatus({ taskId: selectedTaskId }) : null,
    enabled: !!selectedTaskId,
    refetchInterval: 2000, // Refetch every 2 seconds
  })

  // Get worker status
  const { data: workerStatus, isLoading: workersLoading } = useQuery({
    queryKey: ["workers"],
    queryFn: () => TasksService.getWorkerStatus(),
    refetchInterval: 10000, // Refetch every 10 seconds
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



  return (
    <Container maxW="full" py={4}>
      <VStack gap={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" textAlign={{ base: "center", md: "left" }}>
            Task Management
          </Heading>
          <Text color="gray.500">
            Trigger and monitor Celery tasks
          </Text>
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
                    padding: '8px', 
                    borderRadius: '6px', 
                    border: '1px solid #e2e8f0',
                    width: '100%'
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
                    padding: '8px', 
                    borderRadius: '6px', 
                    border: '1px solid #e2e8f0',
                    width: '100%'
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
                  onChange={(e) => setDuration(parseInt(e.target.value) || 1)}
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
              
              <Box p={3} bg="blue.50" borderRadius="md" borderLeftWidth="4px" borderLeftColor="blue.500">
                <Text fontWeight="bold" color="blue.700" mb={1}>Health Check</Text>
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
              onClick={() => queryClient.invalidateQueries({ queryKey: ["workers"] })}
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
          ) : workerStatus?.active && Object.keys(workerStatus.active).length > 0 ? (
            <Table.Root variant="outline">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>Worker</Table.ColumnHeader>
                  <Table.ColumnHeader>Status</Table.ColumnHeader>
                  <Table.ColumnHeader>Active Tasks</Table.ColumnHeader>
                  <Table.ColumnHeader>Processed</Table.ColumnHeader>
                  <Table.ColumnHeader>Load Average</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {Object.entries(workerStatus.active || {}).map(([workerName, tasks]) => (
                  <Table.Row key={workerName}>
                    <Table.Cell>{workerName}</Table.Cell>
                    <Table.Cell>
                      <Badge colorPalette="green">
                        online
                      </Badge>
                    </Table.Cell>
                    <Table.Cell>{Array.isArray(tasks) ? tasks.length : 0}</Table.Cell>
                    <Table.Cell>-</Table.Cell>
                    <Table.Cell>-</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          ) : (
            <Box p={3} bg="orange.50" borderRadius="md" borderLeftWidth="4px" borderLeftColor="orange.500">
              <Text color="orange.700">
                No workers found. Make sure Celery workers are running.
              </Text>
            </Box>
          )}
        </Box>

        {/* Task Status */}
        {selectedTaskId && (
          <Box bg="white" p={6} borderRadius="lg" shadow="sm" borderWidth="1px">
            <Heading size="md" mb={4}>Task Status: {selectedTaskId}</Heading>
            
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
                
                {taskStatus.result && (
                  <Box>
                    <Text fontWeight="bold" mb={2}>Result:</Text>
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
                    <Text fontWeight="bold" mb={2} color="red.500">Error:</Text>
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
              <Box p={3} bg="red.50" borderRadius="md" borderLeftWidth="4px" borderLeftColor="red.500">
                <Text color="red.700">
                  Failed to load task status
                </Text>
              </Box>
            )}
          </Box>
        )}

        {/* Task History */}
        <Box bg="white" p={6} borderRadius="lg" shadow="sm" borderWidth="1px">
          <HStack justify="space-between" mb={4}>
            <Heading size="md">Recent Tasks</Heading>
            <Button
              size="sm"
              variant="outline"
              onClick={() => refetchTasks()}
              loading={tasksLoading}
            >
              <FiRefreshCw />
              Refresh
            </Button>
          </HStack>
          
          {tasksLoading ? (
            <Flex justify="center">
              <Spinner />
            </Flex>
          ) : taskList && taskList.length > 0 ? (
            <Table.Root variant="outline">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>Task ID</Table.ColumnHeader>
                  <Table.ColumnHeader>Status</Table.ColumnHeader>
                  <Table.ColumnHeader>Date Done</Table.ColumnHeader>
                  <Table.ColumnHeader>Actions</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {taskList.slice(0, 10).map((task) => (
                  <Table.Row key={task.task_id}>
                    <Table.Cell fontFamily="mono" fontSize="sm">
                      {task.task_id.substring(0, 8)}...
                    </Table.Cell>
                    <Table.Cell>
                      <Badge colorPalette={getStatusColor(task.status)}>
                        {task.status}
                      </Badge>
                    </Table.Cell>
                    <Table.Cell>
                      {task.date_done ? new Date(task.date_done).toLocaleString() : "N/A"}
                    </Table.Cell>
                    <Table.Cell>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedTaskId(task.task_id)}
                      >
                        View
                      </Button>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          ) : (
            <EmptyState.Root>
              <EmptyState.Content>
                <EmptyState.Indicator>
                  <FiActivity />
                </EmptyState.Indicator>
                <VStack textAlign="center">
                  <EmptyState.Title>No tasks found</EmptyState.Title>
                  <EmptyState.Description>
                    Trigger a task to see it here
                  </EmptyState.Description>
                </VStack>
              </EmptyState.Content>
            </EmptyState.Root>
          )}
        </Box>
      </VStack>
    </Container>
  )
}

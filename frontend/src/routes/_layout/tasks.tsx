import { TasksService } from "@/client"
import {
  ActiveTasksMonitor,
  PeriodicTasks,
  QuickActions,
  type SystemHealth,
  SystemHealthOverview,
  TaskDetailsModal,
  type WorkerData,
  WorkerStatsModal,
  WorkerStatus,
} from "@/components/Tasks"
import useCustomToast from "@/hooks/useCustomToast"
import { Box, Container, Flex, Heading, Text, VStack } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

export const Route = createFileRoute("/_layout/tasks")({
  component: Tasks,
})

function Tasks() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [selectedWorkerData, setSelectedWorkerData] =
    useState<WorkerData | null>(null)
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
    onSuccess: ({ data }: any) => {
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
    refetchInterval: (data: any) => {
      // Stop polling if task is in a terminal state
      if (
        data?.state &&
        ["SUCCESS", "FAILURE", "REVOKED"].includes(
          data.state.data?.status.toUpperCase(),
        )
      ) {
        return false
      }
      return 2000 // Continue polling every 2 seconds for running tasks
    },
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

  // Handler functions
  const handleHealthCheck = () => {
    healthCheckMutation.mutate()
  }

  const handleTriggerPeriodicTask = (taskName: string) => {
    triggerPeriodicTaskMutation.mutate(taskName)
  }

  const handleRefreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ["workers"] })
  }

  const handleRefreshWorkers = () => {
    queryClient.invalidateQueries({ queryKey: ["workers"] })
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
        ...workerStats,
      })
      setWorkerStatsModalOpen(true)
    }
  }

  const handleViewTaskDetails = (taskId: string) => {
    setSelectedTaskId(taskId)
    setTaskDetailsModalOpen(true)
  }

  const handleCloseTaskDetailsModal = () => {
    setTaskDetailsModalOpen(false)
  }

  const handleCloseWorkerStatsModal = () => {
    setWorkerStatsModalOpen(false)
  }

  // Calculate system health metrics
  const systemHealth: SystemHealth = {
    redis_status: "healthy", // Would come from backend
    active_workers: workerStatus?.active
      ? Object.keys(workerStatus.active).length
      : 0,
    running_tasks: workerStatus?.active
      ? Object.values(workerStatus.active).reduce(
          (total: number, tasks: any) =>
            total + (Array.isArray(tasks) ? tasks.length : 0),
          0,
        )
      : 0,
    queue_depth: 0, // Would need to be calculated from backend
    failed_tasks_24h: 0, // Would need to be calculated from backend
  }

  return (
    <Container maxW="full" py={4}>
      <VStack gap={6} align="stretch">
        {/* Header */}
        <Flex
          justify="space-between"
          align={{ base: "flex-start", md: "center" }}
          direction={{ base: "column", md: "row" }}
          gap={{ base: 4, md: 0 }}
        >
          <Box>
            <Heading size="lg" textAlign={{ base: "center", md: "left" }}>
              Celery Task Management
            </Heading>
            <Text color="gray.500">
              Monitor workers, tasks, and system health
            </Text>
          </Box>
          <Box alignSelf={{ base: "center", md: "auto" }}>
            <QuickActions
              onHealthCheck={handleHealthCheck}
              onRefreshAll={handleRefreshAll}
              healthCheckLoading={healthCheckMutation.isPending}
              workersLoading={workersLoading}
            />
          </Box>
        </Flex>

        {/* System Health Overview */}
        <SystemHealthOverview systemHealth={systemHealth} />

        {/* Active Tasks Monitor */}
        <ActiveTasksMonitor
          workerStatus={workerStatus}
          workersLoading={workersLoading}
          onRefresh={handleRefreshWorkers}
          onViewTaskDetails={handleViewTaskDetails}
        />

        {/* Worker Status */}
        <WorkerStatus
          workerStatus={workerStatus}
          workersLoading={workersLoading}
          onRefresh={handleRefreshWorkers}
          onViewWorkerStats={handleViewWorkerStats}
        />

        {/* Periodic Tasks */}
        <PeriodicTasks
          workerStatus={workerStatus}
          workersLoading={workersLoading}
          triggerPeriodicTaskLoading={triggerPeriodicTaskMutation.isPending}
          onRefresh={handleRefreshWorkers}
          onTriggerPeriodicTask={handleTriggerPeriodicTask}
        />

        {/* Task Details Modal */}
        <TaskDetailsModal
          isOpen={taskDetailsModalOpen}
          onClose={handleCloseTaskDetailsModal}
          selectedTaskId={selectedTaskId}
          taskStatus={taskStatus}
          statusLoading={statusLoading}
          getStatusColor={getStatusColor}
          renderTaskResult={renderTaskResult}
        />

        {/* Worker Stats Modal */}
        <WorkerStatsModal
          isOpen={workerStatsModalOpen}
          onClose={handleCloseWorkerStatsModal}
          selectedWorkerData={selectedWorkerData}
        />
      </VStack>
    </Container>
  )
}

export default Tasks

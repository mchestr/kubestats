import { TasksService } from "@/client"
import {
  ActiveTasksMonitor,
  PeriodicTasks,
  type SystemHealth,
  SystemHealthOverview,
  TaskDetailsModal,
  TaskMetaTable,
  type WorkerData,
  WorkerStatsModal,
  WorkerStatus,
} from "@/components/Tasks"
import type { TaskMeta } from "@/components/Tasks"
import useCustomToast from "@/hooks/useCustomToast"
import {
  Box,
  Container,
  Flex,
  Heading,
  Text,
  VStack,
  createListCollection,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"

export function TasksPage() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [_selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [selectedWorkerData, setSelectedWorkerData] =
    useState<WorkerData | null>(null)
  const [workerStatsModalOpen, setWorkerStatsModalOpen] = useState(false)
  const [_taskDetailsModalOpen, setTaskDetailsModalOpen] = useState(false)
  const [taskMetaModalOpen, setTaskMetaModalOpen] = useState(false)
  const [selectedTaskMeta, setSelectedTaskMeta] = useState<TaskMeta | null>(
    null,
  )
  const [status, setStatus] = useState<string>("")
  const [search, setSearch] = useState("")

  const statusCollection = createListCollection({
    items: [
      { value: "", label: "All Statuses" },
      { value: "PENDING", label: "Pending" },
      { value: "FAILURE", label: "Failed" },
      { value: "SUCCESS", label: "Success" },
    ],
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

  // Get worker status (which now includes periodic tasks)
  const { data: workerStatus, isLoading: workersLoading } = useQuery({
    queryKey: ["workers"],
    queryFn: async () => {
      const response = await TasksService.tasksGetWorkerStatus()
      return response.data as any
    },
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  const handleTriggerPeriodicTask = (taskName: string) => {
    triggerPeriodicTaskMutation.mutate(taskName)
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

  const handleCloseWorkerStatsModal = () => {
    setWorkerStatsModalOpen(false)
  }

  // Memoize the 'since' date for failed tasks so the queryKey is stable
  const failedSince = useMemo(
    () => new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    [],
  )

  // Fetch failed tasks in the last 24h
  const { data: failedTasks } = useQuery({
    queryKey: ["failedTasks24h", failedSince],
    queryFn: async () => {
      const response = await TasksService.tasksListTasks({
        query: { status: "FAILURE", since: failedSince, limit: 1000 },
      })
      return response.data
    },
  })

  // Fetch pending tasks (queue depth)
  const { data: pendingTasks } = useQuery({
    queryKey: ["pendingTasksQueueDepth"],
    queryFn: async () => {
      const response = await TasksService.tasksListTasks({
        query: { status: "PENDING", limit: 1000 },
      })
      return response.data
    },
    refetchInterval: 10000,
  })

  // Calculate system health metrics
  const systemHealth: SystemHealth = {
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
    queue_depth: pendingTasks?.length || 0,
    failed_tasks_24h: failedTasks?.length || 0,
  }

  const handleViewTaskMeta = (task: TaskMeta) => {
    setSelectedTaskMeta(task)
    setTaskMetaModalOpen(true)
  }
  const handleCloseTaskMetaModal = () => setTaskMetaModalOpen(false)

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

        {/* Worker Stats Modal */}
        <WorkerStatsModal
          isOpen={workerStatsModalOpen}
          onClose={handleCloseWorkerStatsModal}
          selectedWorkerData={selectedWorkerData}
        />

        <Box>
          <Heading size="md" mb={2}>
            Recent Celery Tasks
          </Heading>
          <TaskMetaTable
            onViewTask={handleViewTaskMeta}
            status={status}
            setStatus={setStatus}
            search={search}
            setSearch={setSearch}
            statusCollection={statusCollection}
          />
        </Box>

        <TaskDetailsModal
          isOpen={taskMetaModalOpen}
          onClose={handleCloseTaskMetaModal}
          selectedTaskId={selectedTaskMeta?.task_id || null}
          taskStatus={null}
          statusLoading={false}
          getStatusColor={getStatusColor}
          renderTaskResult={renderTaskResult}
          taskMeta={selectedTaskMeta || undefined}
        />
      </VStack>
    </Container>
  )
}

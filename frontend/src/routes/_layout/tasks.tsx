import { TasksService } from "@/client"
import {
  ActiveTasksMonitor,
  PeriodicTasks,
  type SystemHealth,
  SystemHealthOverview,
  TaskDetailsModal,
  type WorkerData,
  WorkerStatsModal,
  WorkerStatus,
} from "@/components/Tasks"
import type { TaskMeta } from "@/components/Tasks"
import useCustomToast from "@/hooks/useCustomToast"
import {
  Box,
  Button,
  Container,
  Flex,
  HStack,
  Heading,
  Input,
  Select,
  Spinner,
  Table,
  Text,
  VStack,
  createListCollection,
} from "@chakra-ui/react"
import {
  type UseQueryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useMemo, useState } from "react"

export const Route = createFileRoute("/_layout/tasks")({
  component: Tasks,
})

function Tasks() {
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
    queue_depth: 0, // Would need to be calculated from backend
    failed_tasks_24h: 0, // Would need to be calculated from backend
  }

  // Memoize the 'since' date for failed tasks so the queryKey is stable
  const failedSince = useMemo(
    () => new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    [],
  )

  function useTaskMeta(
    {
      status,
      limit,
      since,
    }: { status?: string; limit?: number; since?: string },
    options?: Partial<UseQueryOptions<TaskMeta[], Error>>,
  ) {
    return useQuery({
      queryKey: ["taskMeta", status, limit, since],
      queryFn: async () => {
        const response = await TasksService.tasksListTasks({
          query: { status, limit, since },
        })
        return response.data as TaskMeta[]
      },
      ...(options || {}),
    })
  }

  function TaskMetaTable({
    onViewTask,
    status,
    setStatus,
    search,
    setSearch,
  }: {
    onViewTask: (task: TaskMeta) => void
    status: string
    setStatus: (s: string) => void
    search: string
    setSearch: (s: string) => void
  }) {
    const { data, isLoading, refetch } = useTaskMeta({
      status: status || undefined,
      limit: 50,
    })

    const filtered: TaskMeta[] = Array.isArray(data)
      ? data.filter((t: TaskMeta) =>
          search
            ? t.task_id.toLowerCase().includes(search.toLowerCase())
            : true,
        )
      : []

    return (
      <Box>
        <HStack mb={2} gap={2}>
          <Select.Root
            collection={statusCollection}
            value={status ? [status] : []}
            onValueChange={({ value }) => setStatus(value[0] || "")}
            maxW="180px"
            size="sm"
          >
            <Select.HiddenSelect />
            <Select.Control>
              <Select.Trigger>
                <Select.ValueText placeholder="All Statuses" />
              </Select.Trigger>
              <Select.IndicatorGroup>
                <Select.Indicator />
              </Select.IndicatorGroup>
            </Select.Control>
            <Select.Positioner>
              <Select.Content>
                {statusCollection.items.map((opt) => (
                  <Select.Item key={opt.value} item={opt.value}>
                    {opt.label}
                  </Select.Item>
                ))}
              </Select.Content>
            </Select.Positioner>
          </Select.Root>
          <Input
            placeholder="Search by Task ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            maxW="250px"
          />
          <Button size="sm" onClick={() => refetch()}>
            Refresh
          </Button>
        </HStack>
        <Box overflowX="auto">
          <Table.Root variant="outline">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>Task ID</Table.ColumnHeader>
                <Table.ColumnHeader>Status</Table.ColumnHeader>
                <Table.ColumnHeader>Name</Table.ColumnHeader>
                <Table.ColumnHeader>Date</Table.ColumnHeader>
                <Table.ColumnHeader>Actions</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {isLoading ? (
                <Table.Row>
                  <Table.Cell colSpan={5} textAlign="center">
                    <Spinner size="sm" />
                  </Table.Cell>
                </Table.Row>
              ) : filtered && filtered.length > 0 ? (
                filtered.map((task: TaskMeta) => (
                  <Table.Row key={task.task_id}>
                    <Table.Cell fontFamily="mono" fontSize="xs">
                      {task.task_id.substring(0, 8)}...
                    </Table.Cell>
                    <Table.Cell>{task.status}</Table.Cell>
                    <Table.Cell>{task.name || "-"}</Table.Cell>
                    <Table.Cell>
                      {new Date(task.date_done).toLocaleString()}
                    </Table.Cell>
                    <Table.Cell>
                      <Button size="xs" onClick={() => onViewTask(task)}>
                        Details
                      </Button>
                    </Table.Cell>
                  </Table.Row>
                ))
              ) : (
                <Table.Row>
                  <Table.Cell colSpan={5} textAlign="center">
                    No tasks found
                  </Table.Cell>
                </Table.Row>
              )}
            </Table.Body>
          </Table.Root>
        </Box>
      </Box>
    )
  }

  const { data: failedTasks } = useTaskMeta({
    status: "FAILURE",
    since: failedSince,
    limit: 100,
  })
  const { data: pendingTasks } = useTaskMeta(
    { status: "PENDING", limit: 100 },
    { refetchInterval: 10000 },
  )

  // Update systemHealth with real values
  systemHealth.queue_depth = pendingTasks?.length || 0
  systemHealth.failed_tasks_24h = failedTasks?.length || 0

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

export default Tasks

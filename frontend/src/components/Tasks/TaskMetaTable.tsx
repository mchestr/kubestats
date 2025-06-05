import { TasksService } from "@/client"
import {
  Box,
  Button,
  HStack,
  Input,
  Select,
  Spinner,
  Table,
} from "@chakra-ui/react"
import { type UseQueryOptions, useQuery } from "@tanstack/react-query"
import type { TaskMeta } from "./types"

export function useTaskMeta(
  { status, limit, since }: { status?: string; limit?: number; since?: string },
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

export function TaskMetaTable({
  onViewTask,
  status,
  setStatus,
  search,
  setSearch,
  statusCollection,
}: {
  onViewTask: (task: TaskMeta) => void
  status: string
  setStatus: (s: string) => void
  search: string
  setSearch: (s: string) => void
  statusCollection: any
}) {
  const { data, isLoading, refetch } = useTaskMeta({
    status: status || undefined,
    limit: 50,
  })

  const filtered: TaskMeta[] = Array.isArray(data)
    ? data.filter((t: TaskMeta) =>
        search
          ? t.task_id.toLowerCase().includes(search.toLowerCase()) ||
            t.name?.toLowerCase().includes(search.toLowerCase())
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
              {statusCollection.items.map((opt: any) => (
                <Select.Item key={opt.value} item={opt.value}>
                  {opt.label}
                </Select.Item>
              ))}
            </Select.Content>
          </Select.Positioner>
        </Select.Root>
        <Input
          placeholder="Search by Task ID or Name"
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

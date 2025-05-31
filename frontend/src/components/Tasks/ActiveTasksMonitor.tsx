import {
  Badge,
  Box,
  Button,
  Card,
  Flex,
  HStack,
  Heading,
  Spinner,
  Table,
  Text,
} from "@chakra-ui/react"
import { FiCheckCircle, FiEye, FiRefreshCw, FiZap } from "react-icons/fi"
import type { WorkerStatus } from "./types"

interface ActiveTasksMonitorProps {
  workerStatus: WorkerStatus | undefined
  workersLoading: boolean
  onRefresh: () => void
  onViewTaskDetails: (taskId: string) => void
}

export function ActiveTasksMonitor({
  workerStatus,
  workersLoading,
  onRefresh,
  onViewTaskDetails,
}: ActiveTasksMonitorProps) {
  const hasActiveTasks =
    workerStatus?.active &&
    Object.values(workerStatus.active).some(
      (tasks) => Array.isArray(tasks) && tasks.length > 0,
    )

  return (
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
        ) : hasActiveTasks ? (
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
              {Object.entries(workerStatus.active!)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([workerName, tasks]) =>
                  Array.isArray(tasks)
                    ? tasks.map((task: any, index: number) => (
                        <Table.Row key={`${workerName}-${index}`}>
                          <Table.Cell>
                            <Text fontFamily="mono" fontSize="sm">
                              {task.id?.substring(0, 8) || "N/A"}...
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text fontWeight="medium">
                              {task.name || "Unknown"}
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Badge size="sm" colorPalette="blue">
                              {workerName.replace(/^celery@/, "")}
                            </Badge>
                          </Table.Cell>
                          <Table.Cell>
                            <Text fontSize="sm" color="fg.muted">
                              {task.time_start
                                ? new Date(
                                    task.time_start * 1000,
                                  ).toLocaleTimeString()
                                : "N/A"}
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <HStack gap={2}>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => onViewTaskDetails(task.id)}
                              >
                                <FiEye />
                              </Button>
                            </HStack>
                          </Table.Cell>
                        </Table.Row>
                      ))
                    : [],
                )}
            </Table.Body>
          </Table.Root>
        ) : (
          <Box p={6} borderRadius="md" textAlign="center">
            <Box
              style={{
                display: "flex",
                justifyContent: "center",
                marginBottom: "8px",
              }}
            >
              <FiCheckCircle size={24} />
            </Box>
            <Text fontWeight="medium">No active tasks</Text>
            <Text fontSize="sm">
              All workers are idle and ready for new tasks
            </Text>
          </Box>
        )}
      </Card.Body>
    </Card.Root>
  )
}

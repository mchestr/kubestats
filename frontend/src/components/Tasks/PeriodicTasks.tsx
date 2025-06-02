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
  VStack,
} from "@chakra-ui/react"
import { FiClock, FiRefreshCw, FiZap } from "react-icons/fi"
import type { PeriodicTaskData, WorkerStatus } from "./types"

interface PeriodicTasksProps {
  workerStatus: WorkerStatus | undefined
  workersLoading: boolean
  triggerPeriodicTaskLoading: boolean
  onRefresh: () => void
  onTriggerPeriodicTask: (taskName: string) => void
}

export function PeriodicTasks({
  workerStatus,
  workersLoading,
  triggerPeriodicTaskLoading,
  onRefresh,
  onTriggerPeriodicTask,
}: PeriodicTasksProps) {
  const hasPeriodicTasks =
    workerStatus?.periodic_tasks && workerStatus.periodic_tasks.length > 0

  return (
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
        ) : hasPeriodicTasks ? (
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
              {workerStatus.periodic_tasks!.map((task: PeriodicTaskData) => (
                <Table.Row key={task.name}>
                  <Table.Cell>
                    <VStack gap={1} align="start">
                      <Text fontWeight="medium">{task.name}</Text>
                      <Text fontSize="sm" color="gray.600">
                        {task.task}
                      </Text>
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
                      onClick={() => onTriggerPeriodicTask(task.name)}
                      loading={triggerPeriodicTaskLoading}
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
          <Box p={6} bg="blue.50" borderRadius="md" textAlign="center">
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
  )
}

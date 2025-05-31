import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Box,
  Button,
  Flex,
  HStack,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { Badge } from "@chakra-ui/react"
import type { TaskDetailsModalProps } from "./types"

export function TaskDetailsModal({
  isOpen,
  onClose,
  selectedTaskId,
  taskStatus,
  statusLoading,
  getStatusColor,
  renderTaskResult,
}: TaskDetailsModalProps) {
  return (
    <DialogRoot open={isOpen} onOpenChange={(_e) => onClose()}>
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
                    <Text fontWeight="bold" mb={2}>
                      Basic Information
                    </Text>
                    <VStack gap={2} align="stretch">
                      <HStack>
                        <Text fontWeight="medium" minW="100px">
                          Status:
                        </Text>
                        <Badge colorPalette={getStatusColor(taskStatus.status)}>
                          {taskStatus.status}
                        </Badge>
                      </HStack>
                      <HStack>
                        <Text fontWeight="medium" minW="100px">
                          Task ID:
                        </Text>
                        <Text fontFamily="mono" fontSize="sm">
                          {selectedTaskId}
                        </Text>
                      </HStack>
                      {taskStatus.name && (
                        <HStack>
                          <Text fontWeight="medium" minW="100px">
                            Name:
                          </Text>
                          <Text>{taskStatus.name}</Text>
                        </HStack>
                      )}
                      {taskStatus.worker && (
                        <HStack>
                          <Text fontWeight="medium" minW="100px">
                            Worker:
                          </Text>
                          <Text>{taskStatus.worker}</Text>
                        </HStack>
                      )}
                    </VStack>
                  </Box>
                </VStack>

                <VStack gap={3} align="stretch">
                  {taskStatus.date_done && (
                    <Box>
                      <Text fontWeight="bold" mb={2}>
                        Timing
                      </Text>
                      <VStack gap={2} align="stretch">
                        <HStack>
                          <Text fontWeight="medium" minW="100px">
                            Completed:
                          </Text>
                          <Text fontSize="sm">
                            {new Date(taskStatus.date_done).toLocaleString()}
                          </Text>
                        </HStack>
                      </VStack>
                    </Box>
                  )}
                </VStack>
              </SimpleGrid>

              {taskStatus.result != null && (
                <Box>
                  <Text fontWeight="bold" mb={2}>
                    Result
                  </Text>
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
                  <Text fontWeight="bold" mb={2} color="red.500">
                    Error Details
                  </Text>
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
            <Box p={6} bg="red.50" borderRadius="md" textAlign="center">
              <Text color="red.700">Failed to load task details</Text>
            </Box>
          )}
        </DialogBody>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}

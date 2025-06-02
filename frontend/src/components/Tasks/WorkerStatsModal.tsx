import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import { Box, Button, SimpleGrid, Text, VStack } from "@chakra-ui/react"
import type { WorkerStatsModalProps } from "./types"

export function WorkerStatsModal({
  isOpen,
  onClose,
  selectedWorkerData,
}: WorkerStatsModalProps) {
  return (
    <DialogRoot open={isOpen} onOpenChange={(_e) => onClose()}>
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
                  <Text fontWeight="bold" mb={2}>
                    Basic Information
                  </Text>
                  <VStack gap={2} align="stretch">
                    <Text>Worker ID: {selectedWorkerData.worker_id}</Text>
                    <Text>Status: {selectedWorkerData.status}</Text>
                    {selectedWorkerData.pool?.max_concurrency && (
                      <Text>
                        Pool Size: {selectedWorkerData.pool.max_concurrency}
                      </Text>
                    )}
                  </VStack>
                </Box>
              </VStack>

              <VStack gap={4} align="stretch">
                {selectedWorkerData.total && (
                  <Box>
                    <Text fontWeight="bold" mb={2}>
                      Task Statistics
                    </Text>
                    <VStack gap={2} align="stretch">
                      {Object.entries(selectedWorkerData.total).map(
                        ([key, value]) => (
                          <Text key={key}>
                            {key}: {String(value)}
                          </Text>
                        ),
                      )}
                    </VStack>
                  </Box>
                )}
              </VStack>
            </SimpleGrid>
          ) : (
            <Box p={6} bg="red.50" borderRadius="md" textAlign="center">
              <Text color="red.700">No worker data available</Text>
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

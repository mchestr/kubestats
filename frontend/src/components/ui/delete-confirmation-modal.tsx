import { Button, Flex, Heading, Text, VStack } from "@chakra-ui/react"
import { FiAlertTriangle, FiTrash2 } from "react-icons/fi"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
} from "./dialog"

interface DeleteConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description: string
  itemName: string
  isLoading?: boolean
}

export function DeleteConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  itemName,
  isLoading = false,
}: DeleteConfirmationModalProps) {
  return (
    <DialogRoot open={isOpen} onOpenChange={({ open }) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <Flex align="center" gap={3}>
            <FiAlertTriangle color="red.500" size="24" />
            <Heading size="lg">{title}</Heading>
          </Flex>
        </DialogHeader>

        <DialogBody>
          <VStack gap={4} align="stretch">
            <Text>{description}</Text>

            <Text fontWeight="bold" color="red.500">
              Repository: {itemName}
            </Text>

            <Text fontSize="sm" color="gray.600">
              This action cannot be undone. All associated data including:
            </Text>

            <VStack align="start" fontSize="sm" color="gray.600" pl={4}>
              <Text>• Repository metadata</Text>
              <Text>• Kubernetes resources</Text>
              <Text>• Resource events</Text>
              <Text>• Metrics history</Text>
            </VStack>

            <Text fontSize="sm" color="gray.600">
              will be permanently deleted.
            </Text>
          </VStack>
        </DialogBody>

        <DialogFooter>
          <DialogCloseTrigger asChild>
            <Button variant="ghost" mr={3} disabled={isLoading}>
              Cancel
            </Button>
          </DialogCloseTrigger>
          <Button
            colorPalette="red"
            onClick={onConfirm}
            disabled={isLoading}
            loading={isLoading}
          >
            <FiTrash2 />
            Delete Repository
          </Button>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}

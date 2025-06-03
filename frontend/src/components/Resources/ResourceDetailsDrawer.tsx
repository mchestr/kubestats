/* eslint-disable lint/a11y/useSemanticElements */
import { useColorModeValue } from "@/components/ui/color-mode"
import {
  Box,
  Flex,
  Heading,
  IconButton,
  Text,
  useClipboard,
} from "@chakra-ui/react"
import type React from "react"
import { FiCopy, FiX } from "react-icons/fi"

interface ResourceDetailsDrawerProps {
  open: boolean
  onClose: () => void
  resource: any
}

export const ResourceDetailsDrawer: React.FC<ResourceDetailsDrawerProps> = ({
  open,
  onClose,
  resource,
}) => {
  const nameClipboard = useClipboard(resource?.name || "")
  const nsClipboard = useClipboard(resource?.namespace || "")
  const kindClipboard = useClipboard(resource?.kind || "")
  const drawerBg = useColorModeValue("white", "gray.800") // Fully opaque

  if (!open || !resource) return null

  return (
    <>
      {/* Backdrop (rendered first, below the drawer) */}
      <Box
        position="fixed"
        inset={0}
        bg="blackAlpha.700"
        zIndex={1400}
        onClick={onClose}
        aria-label="Close details drawer backdrop"
        tabIndex={-1}
        role="presentation"
      />
      {/* Drawer (rendered after, above the backdrop) */}
      {/* eslint-disable-next-line lint/a11y/useSemanticElements */}
      <Box
        position="fixed"
        right={0}
        top={0}
        width={{ base: "100%", md: 420 }}
        height="100%"
        bg={drawerBg}
        boxShadow="-2px 0 16px rgba(0,0,0,0.08)"
        zIndex={1401}
        overflowY="auto"
        p={0}
        display="flex"
        flexDirection="column"
        aria-modal="true"
      >
        <Flex
          align="center"
          justify="space-between"
          p={4}
          borderBottomWidth={1}
          borderColor="border.emphasized"
        >
          <Heading size="md">Resource Details</Heading>
          <IconButton
            aria-label="Close"
            onClick={onClose}
            size="sm"
            variant="ghost"
          >
            <FiX />
          </IconButton>
        </Flex>
        <Box p={4} flex={1} overflowY="auto">
          <Flex align="center" mb={2} gap={2}>
            <Text fontWeight="bold">Name:</Text>
            <Text>{resource.name}</Text>
            <IconButton
              aria-label="Copy name"
              size="xs"
              onClick={nameClipboard.copy}
              variant="ghost"
            >
              <FiCopy />
            </IconButton>
          </Flex>
          <Flex align="center" mb={2} gap={2}>
            <Text fontWeight="bold">Namespace:</Text>
            <Text>{resource.namespace || <em>cluster-scoped</em>}</Text>
            <IconButton
              aria-label="Copy namespace"
              size="xs"
              onClick={nsClipboard.copy}
              variant="ghost"
            >
              <FiCopy />
            </IconButton>
          </Flex>
          <Flex align="center" mb={2} gap={2}>
            <Text fontWeight="bold">Kind:</Text>
            <Text>{resource.kind}</Text>
            <IconButton
              aria-label="Copy kind"
              size="xs"
              onClick={kindClipboard.copy}
              variant="ghost"
            >
              <FiCopy />
            </IconButton>
          </Flex>
          <Flex align="center" mb={2} gap={2}>
            <Text fontWeight="bold">API Version:</Text>
            <Text>{resource.api_version}</Text>
          </Flex>
          <Flex align="center" mb={2} gap={2}>
            <Text fontWeight="bold">Status:</Text>
            <Text>{resource.status}</Text>
          </Flex>
          <Flex align="center" mb={2} gap={2}>
            <Text fontWeight="bold">Repository ID:</Text>
            <Text>{resource.repository_id}</Text>
          </Flex>
          <Box my={4} borderTopWidth={1} borderColor="border.emphasized" />
          <Heading size="sm" mb={2}>
            YAML
          </Heading>
          <Box
            as="pre"
            fontSize="sm"
            bg="bg.subtle"
            p={3}
            borderRadius={6}
            overflowX="auto"
            maxHeight="400px"
          >
            {yamlString(resource)}
          </Box>
        </Box>
      </Box>
    </>
  )
}

function yamlString(resource: any) {
  // Simple YAML-like rendering for now
  if (!resource) return ""
  const omit = ["id", "repository_id", "created_at", "updated_at"]
  const filtered = Object.fromEntries(
    Object.entries(resource).filter(([k]) => !omit.includes(k)),
  )
  try {
    return JSON.stringify(filtered, null, 2)
      .replace(/"/g, "")
      .replace(/\n/g, "\n")
      .replace(/,/g, "")
      .replace(/^{|}$/g, "")
  } catch {
    return ""
  }
}

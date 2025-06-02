import { Badge, HStack, Text } from "@chakra-ui/react"
import {
  FiAlertTriangle,
  FiCheckCircle,
  FiClock,
  FiRefreshCw,
  FiShield,
  FiXCircle,
} from "react-icons/fi"

import type { RepositoryPublic } from "../../client"

export const getSyncStatusBadge = (repo: RepositoryPublic) => {
  const syncStatus = repo.sync_status || "pending"

  switch (syncStatus) {
    case "success":
      return (
        <Badge colorPalette="green">
          <HStack gap={1}>
            <FiCheckCircle size={12} />
            <Text>Synced</Text>
          </HStack>
        </Badge>
      )
    case "pending":
      return (
        <Badge colorPalette="yellow">
          <HStack gap={1}>
            <FiClock size={12} />
            <Text>Pending</Text>
          </HStack>
        </Badge>
      )
    case "syncing":
      return (
        <Badge colorPalette="blue">
          <HStack gap={1}>
            <FiRefreshCw size={12} />
            <Text>Syncing</Text>
          </HStack>
        </Badge>
      )
    case "error":
      return (
        <Badge colorPalette="red">
          <HStack gap={1}>
            <FiXCircle size={12} />
            <Text>Error</Text>
          </HStack>
        </Badge>
      )
    case "blocked":
      return (
        <Badge colorPalette="red">
          <HStack gap={1}>
            <FiShield size={12} />
            <Text>Blocked</Text>
          </HStack>
        </Badge>
      )
    case "pending_approval":
      return (
        <Badge colorPalette="orange">
          <HStack gap={1}>
            <FiAlertTriangle size={12} />
            <Text>Pending Approval</Text>
          </HStack>
        </Badge>
      )
    default:
      return (
        <Badge colorPalette="gray">
          <HStack gap={1}>
            <FiClock size={12} />
            <Text>Unknown</Text>
          </HStack>
        </Badge>
      )
  }
}

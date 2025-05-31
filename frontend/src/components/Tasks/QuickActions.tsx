import { Button, HStack, Spinner } from "@chakra-ui/react"
import { FiActivity, FiMoreVertical, FiRefreshCw } from "react-icons/fi"
import { MenuContent, MenuItem, MenuRoot, MenuTrigger } from "../ui/menu"

interface QuickActionsProps {
  onHealthCheck: () => void
  onRefreshAll: () => void
  healthCheckLoading: boolean
  workersLoading: boolean
}

export function QuickActions({
  onHealthCheck,
  onRefreshAll,
  healthCheckLoading,
  workersLoading,
}: QuickActionsProps) {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <Button variant="outline" size="sm" p={2} aria-label="Quick Actions">
          <FiMoreVertical />
        </Button>
      </MenuTrigger>
      <MenuContent>
        <MenuItem
          value="health-check"
          gap={2}
          py={2}
          onClick={onHealthCheck}
          style={{ cursor: "pointer" }}
          disabled={healthCheckLoading}
        >
          <HStack gap={2} flex="1">
            {healthCheckLoading ? <Spinner size="sm" /> : <FiActivity />}
            Run Health Check
          </HStack>
        </MenuItem>
        <MenuItem
          value="refresh-all"
          gap={2}
          py={2}
          onClick={onRefreshAll}
          style={{ cursor: "pointer" }}
          disabled={workersLoading}
        >
          <HStack gap={2} flex="1">
            {workersLoading ? <Spinner size="sm" /> : <FiRefreshCw />}
            Refresh All Data
          </HStack>
        </MenuItem>
      </MenuContent>
    </MenuRoot>
  )
}

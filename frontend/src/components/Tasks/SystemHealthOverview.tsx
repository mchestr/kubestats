import {
  Box,
  Card,
  HStack,
  Heading,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react"
import {
  FiActivity,
  FiAlertCircle,
  FiList,
  FiUsers,
  FiZap,
} from "react-icons/fi"
import type { SystemHealth } from "./types"

interface SystemHealthOverviewProps {
  systemHealth: SystemHealth
}

export function SystemHealthOverview({
  systemHealth,
}: SystemHealthOverviewProps) {
  return (
    <Box>
      <Heading size="md" mb={4}>
        <HStack>
          <FiActivity />
          <Text>System Health</Text>
        </HStack>
      </Heading>
      <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
        {/* Active Workers */}
        <Card.Root>
          <Card.Body>
            <VStack gap={2}>
              <HStack>
                <FiUsers color="blue" />
                <Text fontSize="sm" fontWeight="medium">
                  Workers
                </Text>
              </HStack>
              <Text fontSize="xl" fontWeight="bold">
                {systemHealth.active_workers}
              </Text>
            </VStack>
          </Card.Body>
        </Card.Root>

        {/* Running Tasks */}
        <Card.Root>
          <Card.Body>
            <VStack gap={2}>
              <HStack>
                <FiZap color="orange" />
                <Text fontSize="sm" fontWeight="medium">
                  Running
                </Text>
              </HStack>
              <Text fontSize="xl" fontWeight="bold">
                {systemHealth.running_tasks}
              </Text>
            </VStack>
          </Card.Body>
        </Card.Root>

        {/* Queue Depth */}
        <Card.Root>
          <Card.Body>
            <VStack gap={2}>
              <HStack>
                <FiList color="purple" />
                <Text fontSize="sm" fontWeight="medium">
                  Queued
                </Text>
              </HStack>
              <Text fontSize="xl" fontWeight="bold">
                {systemHealth.queue_depth}
              </Text>
            </VStack>
          </Card.Body>
        </Card.Root>

        {/* Failed Tasks */}
        <Card.Root>
          <Card.Body>
            <VStack gap={2}>
              <HStack>
                <FiAlertCircle color="red" />
                <Text fontSize="sm" fontWeight="medium">
                  Failed (24h)
                </Text>
              </HStack>
              <Text fontSize="xl" fontWeight="bold">
                {systemHealth.failed_tasks_24h}
              </Text>
            </VStack>
          </Card.Body>
        </Card.Root>
      </SimpleGrid>
    </Box>
  )
}

import {
  Box,
  Card,
  HStack,
  Heading,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react"
import { FiActivity, FiMinus, FiPlus, FiRefreshCw } from "react-icons/fi"
import type { EcosystemStatsPublic } from "../../client"

interface DailyActivityProps {
  stats: EcosystemStatsPublic | undefined
  isLoading: boolean
}

interface ActivityCardProps {
  icon: React.ElementType
  title: string
  value: number
  colorScheme: string
}

const ActivityCard = ({
  icon: Icon,
  title,
  value,
  colorScheme,
}: ActivityCardProps) => {
  return (
    <Card.Root>
      <Card.Body>
        <VStack gap={3}>
          <HStack justify="space-between" w="full">
            <HStack>
              <Box color={`${colorScheme}.500`}>
                <Icon size={18} />
              </Box>
              <Text fontSize="sm" fontWeight="medium" color="gray.600">
                {title}
              </Text>
            </HStack>
          </HStack>

          <Text fontSize="xl" fontWeight="bold" alignSelf="start">
            {value.toLocaleString()}
          </Text>
        </VStack>
      </Card.Body>
    </Card.Root>
  )
}

export function DailyActivity({ stats, isLoading }: DailyActivityProps) {
  if (isLoading || !stats) {
    return (
      <Box>
        <Heading size="md" mb={4}>
          <HStack>
            <FiActivity />
            <Text>Daily Resource Activity</Text>
          </HStack>
        </Heading>
        <SimpleGrid columns={{ base: 1, md: 4 }} gap={4}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Card.Root key={i}>
              <Card.Body>
                <VStack gap={3}>
                  <Box w="18px" h="18px" bg="gray.200" borderRadius="md" />
                  <Box w="full" h="6" bg="gray.200" borderRadius="md" />
                </VStack>
              </Card.Body>
            </Card.Root>
          ))}
        </SimpleGrid>
      </Box>
    )
  }

  const totalActivity =
    stats.daily_created_resources +
    stats.daily_modified_resources +
    stats.daily_deleted_resources

  return (
    <Box>
      <Heading size="md" mb={4}>
        <HStack justify="space-between">
          <HStack>
            <FiActivity />
            <Text>Daily Resource Activity</Text>
          </HStack>
          <Text fontSize="sm" color="gray.500">
            Yesterday
          </Text>
        </HStack>
      </Heading>

      <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
        {/* Total Activity */}
        <ActivityCard
          icon={FiActivity}
          title="Total Changes"
          value={totalActivity}
          colorScheme="purple"
        />

        {/* Created Resources */}
        <ActivityCard
          icon={FiPlus}
          title="Created"
          value={stats.daily_created_resources}
          colorScheme="green"
        />

        {/* Modified Resources */}
        <ActivityCard
          icon={FiRefreshCw}
          title="Modified"
          value={stats.daily_modified_resources}
          colorScheme="blue"
        />

        {/* Deleted Resources */}
        <ActivityCard
          icon={FiMinus}
          title="Deleted"
          value={stats.daily_deleted_resources}
          colorScheme="red"
        />
      </SimpleGrid>
    </Box>
  )
}

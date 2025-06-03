import { Box, Flex, Heading, SimpleGrid, Stat, Tag } from "@chakra-ui/react"
import type React from "react"
import { useMemo } from "react"
import { FiGrid, FiHash, FiLayers, FiTag } from "react-icons/fi"

interface ResourceSummaryProps {
  resources: any[]
}

function getTopCounts(arr: any[], key: string, topN = 3) {
  const counts: Record<string, number> = {}
  for (const r of arr) {
    const val = r[key] || "<none>"
    counts[val] = (counts[val] || 0) + 1
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN)
}

export const ResourceSummary: React.FC<ResourceSummaryProps> = ({
  resources,
}) => {
  const total = resources.length
  const topKinds = useMemo(() => getTopCounts(resources, "kind"), [resources])
  const topStatuses = useMemo(
    () => getTopCounts(resources, "status"),
    [resources],
  )
  const topNamespaces = useMemo(
    () => getTopCounts(resources, "namespace"),
    [resources],
  )

  return (
    <Box mb={8}>
      <Heading as="h2" size="md" mb={4}>
        Resource Summary
      </Heading>
      <SimpleGrid columns={{ base: 1, md: 4 }} gap={4}>
        {/* Total resources */}
        <Stat.Root p={4} borderRadius="md" boxShadow="sm" bg="bg.surface">
          <Flex align="center" gap={2} mb={1}>
            <FiLayers />
            <Stat.Label fontWeight="bold">Total Resources</Stat.Label>
          </Flex>
          <Box fontSize="2xl" fontWeight="bold">
            {total}
          </Box>
        </Stat.Root>
        {/* Top Kinds */}
        <Stat.Root p={4} borderRadius="md" boxShadow="sm" bg="bg.surface">
          <Flex align="center" gap={2} mb={1}>
            <FiTag />
            <Stat.Label fontWeight="bold">Top Kinds</Stat.Label>
          </Flex>
          <Stat.HelpText>
            {topKinds.map(([kind, count]) => (
              <Tag.Root key={kind} mr={1} mb={1}>
                {kind}: {count}
              </Tag.Root>
            ))}
          </Stat.HelpText>
        </Stat.Root>
        {/* Top Statuses */}
        <Stat.Root p={4} borderRadius="md" boxShadow="sm" bg="bg.surface">
          <Flex align="center" gap={2} mb={1}>
            <FiHash />
            <Stat.Label fontWeight="bold">Top Statuses</Stat.Label>
          </Flex>
          <Stat.HelpText>
            {topStatuses.map(([status, count]) => (
              <Tag.Root key={status} mr={1} mb={1}>
                {status}: {count}
              </Tag.Root>
            ))}
          </Stat.HelpText>
        </Stat.Root>
        {/* Top Namespaces */}
        <Stat.Root p={4} borderRadius="md" boxShadow="sm" bg="bg.surface">
          <Flex align="center" gap={2} mb={1}>
            <FiGrid />
            <Stat.Label fontWeight="bold">Top Namespaces</Stat.Label>
          </Flex>
          <Stat.HelpText>
            {topNamespaces.map(([ns, count]) => (
              <Tag.Root key={ns} mr={1} mb={1}>
                {ns}: {count}
              </Tag.Root>
            ))}
          </Stat.HelpText>
        </Stat.Root>
      </SimpleGrid>
    </Box>
  )
}

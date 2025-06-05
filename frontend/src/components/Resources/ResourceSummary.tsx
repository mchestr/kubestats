import { Box, Flex, Heading, SimpleGrid, Stat, Tag } from "@chakra-ui/react"
import type React from "react"
import { useMemo } from "react"
import { FiLayers, FiTag } from "react-icons/fi"

interface ResourceSummaryProps {
  resources: any[]
  total: number
}

function getTopCombos(arr: any[], topN = 3) {
  return arr
    .map((g) => ({
      label: `${g.kind} / ${g.name}`,
      count: g.total_count,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, topN)
}

function getTopKinds(arr: any[], topN = 3) {
  const counts: Record<string, number> = {}
  for (const g of arr) {
    counts[g.kind] = (counts[g.kind] || 0) + g.total_count
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN)
}

export const ResourceSummary: React.FC<ResourceSummaryProps> = ({
  resources,
  total,
}) => {
  const topCombos = useMemo(() => getTopCombos(resources), [resources])
  const topKinds = useMemo(() => getTopKinds(resources), [resources])

  return (
    <Box mb={8}>
      <Heading as="h2" size="md" mb={4}>
        Resource Summary
      </Heading>
      <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
        {/* Total unique kind/name combos */}
        <Stat.Root p={4} borderRadius="md" boxShadow="sm" bg="bg.surface">
          <Flex align="center" gap={2} mb={1}>
            <FiLayers />
            <Stat.Label fontWeight="bold">Unique Kind/Name Combos</Stat.Label>
          </Flex>
          <Box fontSize="2xl" fontWeight="bold">
            {total}
          </Box>
        </Stat.Root>
        {/* Top Kind/Name Combos */}
        <Stat.Root p={4} borderRadius="md" boxShadow="sm" bg="bg.surface">
          <Flex align="center" gap={2} mb={1}>
            <FiTag />
            <Stat.Label fontWeight="bold">Most Popular Combos</Stat.Label>
          </Flex>
          <Stat.HelpText>
            {topCombos.map(({ label, count }) => (
              <Tag.Root key={label} mr={1} mb={1}>
                {label}: {count}
              </Tag.Root>
            ))}
          </Stat.HelpText>
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
      </SimpleGrid>
    </Box>
  )
}

import { Card, Grid, HStack, Stat, Text } from "@chakra-ui/react"
import {
  FiAlertCircle,
  FiGitBranch,
  FiHardDrive,
  FiLayers,
  FiStar,
} from "react-icons/fi"

import type { RepositoryPublic } from "../../client"

interface MetricsCardsProps {
  repository: RepositoryPublic
}

function MetricsCards({ repository }: MetricsCardsProps) {
  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`
    }
    return num.toString()
  }

  const formatSize = (sizeInKB: number) => {
    if (sizeInKB >= 1000000) {
      return `${(sizeInKB / 1000000).toFixed(1)} GB`
    }
    if (sizeInKB >= 1000) {
      return `${(sizeInKB / 1000).toFixed(1)} MB`
    }
    return `${sizeInKB} KB`
  }

  const metrics = repository.latest_metrics

  return (
    <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
      <Card.Root>
        <Card.Body>
          <Stat.Root>
            <HStack justifyContent="space-between">
              <Stat.Label color="fg.muted">Stars</Stat.Label>
              <FiStar color="orange" size={20} />
            </HStack>
            <Stat.ValueText fontSize="2xl" fontWeight="bold">
              {metrics ? formatNumber(metrics.stars_count) : "0"}
            </Stat.ValueText>
          </Stat.Root>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Body>
          <Stat.Root>
            <HStack justifyContent="space-between">
              <Stat.Label color="fg.muted">Forks</Stat.Label>
              <FiGitBranch color="blue" size={20} />
            </HStack>
            <Stat.ValueText fontSize="2xl" fontWeight="bold">
              {metrics ? formatNumber(metrics.forks_count) : "0"}
            </Stat.ValueText>
          </Stat.Root>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Body>
          <Stat.Root>
            <HStack justifyContent="space-between">
              <Stat.Label color="fg.muted">Total Resources</Stat.Label>
              <FiLayers color="green" size={20} />
            </HStack>
            <Stat.ValueText fontSize="2xl" fontWeight="bold">
              {repository.last_scan_total_resources != null
                ? formatNumber(repository.last_scan_total_resources)
                : "N/A"}
            </Stat.ValueText>
          </Stat.Root>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Body>
          <Stat.Root>
            <HStack justifyContent="space-between">
              <Stat.Label color="fg.muted">Open Issues</Stat.Label>
              <FiAlertCircle color="red" size={20} />
            </HStack>
            <Stat.ValueText fontSize="2xl" fontWeight="bold">
              {metrics ? formatNumber(metrics.open_issues_count) : "0"}
            </Stat.ValueText>
          </Stat.Root>
        </Card.Body>
      </Card.Root>

      <Card.Root>
        <Card.Body>
          <Stat.Root>
            <HStack justifyContent="space-between">
              <Stat.Label color="fg.muted">Repository Size</Stat.Label>
              <FiHardDrive color="purple" size={20} />
            </HStack>
            <Stat.ValueText fontSize="2xl" fontWeight="bold">
              {metrics ? formatSize(metrics.size) : "0 KB"}
            </Stat.ValueText>
          </Stat.Root>
        </Card.Body>
      </Card.Root>

      {metrics?.updated_at && (
        <Card.Root>
          <Card.Body>
            <Stat.Root>
              <Stat.Label color="fg.muted">Last Updated</Stat.Label>
              <Text fontSize="sm" color="fg.subtle" mt={2}>
                {new Date(metrics.updated_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "short",
                  day: "numeric",
                })}
              </Text>
            </Stat.Root>
          </Card.Body>
        </Card.Root>
      )}
    </Grid>
  )
}

export default MetricsCards

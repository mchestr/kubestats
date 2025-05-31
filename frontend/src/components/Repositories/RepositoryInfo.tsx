import {
  Badge,
  Card,
  Flex,
  Grid,
  HStack,
  Heading,
  Link,
  Stack,
  Text,
} from "@chakra-ui/react"
import {
  FiCalendar,
  FiExternalLink,
  FiFileText,
  FiGitBranch,
  FiTag,
  FiUser,
} from "react-icons/fi"

import type { RepositoryPublic } from "../../client"

interface RepositoryInfoProps {
  repository: RepositoryPublic
}

function RepositoryInfo({ repository }: RepositoryInfoProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const InfoCard = ({
    title,
    children,
  }: { title: string; children: React.ReactNode }) => (
    <Card.Root>
      <Card.Header>
        <Heading size="md">{title}</Heading>
      </Card.Header>
      <Card.Body>{children}</Card.Body>
    </Card.Root>
  )

  return (
    <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={6}>
      <InfoCard title="Repository Details">
        <Stack gap={4}>
          <Flex alignItems="center" gap={2}>
            <FiUser size={16} />
            <Text fontWeight="medium">Owner:</Text>
            <Text color="fg.muted">{repository.owner}</Text>
          </Flex>

          <Flex alignItems="center" gap={2}>
            <FiGitBranch size={16} />
            <Text fontWeight="medium">Default Branch:</Text>
            <Badge variant="outline">{repository.default_branch}</Badge>
          </Flex>

          <Flex alignItems="center" gap={2}>
            <FiCalendar size={16} />
            <Text fontWeight="medium">Created:</Text>
            <Text color="fg.muted">{formatDate(repository.created_at)}</Text>
          </Flex>

          <Flex alignItems="center" gap={2}>
            <FiCalendar size={16} />
            <Text fontWeight="medium">Discovered:</Text>
            <Text color="fg.muted">{formatDate(repository.discovered_at)}</Text>
          </Flex>

          {repository.language && (
            <Flex alignItems="center" gap={2}>
              <Text fontWeight="medium">Primary Language:</Text>
              <Badge colorPalette="blue" variant="outline">
                {repository.language}
              </Badge>
            </Flex>
          )}

          {repository.license_name && (
            <Flex alignItems="center" gap={2}>
              <FiFileText size={16} />
              <Text fontWeight="medium">License:</Text>
              <Badge variant="subtle">{repository.license_name}</Badge>
            </Flex>
          )}
        </Stack>
      </InfoCard>

      <InfoCard title="Additional Information">
        <Stack gap={4}>
          {repository.topics && repository.topics.length > 0 && (
            <Stack gap={2}>
              <Flex alignItems="center" gap={2}>
                <FiTag size={16} />
                <Text fontWeight="medium">Topics:</Text>
              </Flex>
              <Flex gap={2} flexWrap="wrap">
                {repository.topics.map((topic) => (
                  <Badge key={topic} variant="subtle" size="sm">
                    {topic}
                  </Badge>
                ))}
              </Flex>
            </Stack>
          )}

          {repository.discovery_tags &&
            repository.discovery_tags.length > 0 && (
              <Stack gap={2}>
                <Text fontWeight="medium">Discovery Tags:</Text>
                <Flex gap={2} flexWrap="wrap">
                  {repository.discovery_tags.map((tag) => (
                    <Badge
                      key={tag}
                      colorPalette="purple"
                      variant="subtle"
                      size="sm"
                    >
                      {tag}
                    </Badge>
                  ))}
                </Flex>
              </Stack>
            )}

          <Stack gap={2}>
            <Text fontWeight="medium">GitHub Repository:</Text>
            <Link
              href={`https://github.com/${repository.full_name}`}
              target="_blank"
              rel="noopener noreferrer"
              color="blue.500"
              _hover={{ color: "blue.600" }}
            >
              <HStack gap={2}>
                <Text>{repository.full_name}</Text>
                <FiExternalLink size={14} />
              </HStack>
            </Link>
          </Stack>

          {repository.latest_metrics && (
            <Stack gap={2}>
              <Text fontWeight="medium">Last Activity:</Text>
              <Text color="fg.muted" fontSize="sm">
                {repository.latest_metrics.pushed_at
                  ? `Last push: ${formatDate(repository.latest_metrics.pushed_at)}`
                  : "No recent activity"}
              </Text>
              <Text color="fg.muted" fontSize="sm">
                Last updated: {formatDate(repository.latest_metrics.updated_at)}
              </Text>
            </Stack>
          )}
        </Stack>
      </InfoCard>
    </Grid>
  )
}

export default RepositoryInfo

import { EcosystemService, type HelmReleaseActivityListPublic } from "@/client"
import {
  Badge,
  Box,
  Card,
  Flex,
  HStack,
  Heading,
  IconButton,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react"
import { Collapse } from "@chakra-ui/transition"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import {
  FiChevronDown,
  FiChevronUp,
  FiFileText,
  FiRefreshCw,
} from "react-icons/fi"

export function HelmReleaseActivitySummary() {
  const [expanded, setExpanded] = useState<string | null>(null)
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["helm-release-activity"],
    queryFn: () =>
      EcosystemService.ecosystemGetHelmReleaseActivity({
        query: { limit: 10 },
      }),
    refetchOnWindowFocus: false,
  })

  // Type assertion for OpenAPI response
  const activity = data?.data as HelmReleaseActivityListPublic | undefined

  if (isLoading) {
    return (
      <Card.Root>
        <Card.Header>
          <HStack justify="space-between">
            <Heading size="md">Helm Release Activity</Heading>
            <Spinner size="sm" />
          </HStack>
        </Card.Header>
        <Card.Body>
          <Flex justify="center" py={8}>
            <Spinner />
          </Flex>
        </Card.Body>
      </Card.Root>
    )
  }

  if (isError || !activity) {
    return (
      <Card.Root>
        <Card.Header>
          <HStack justify="space-between">
            <Heading size="md">Helm Release Activity</Heading>
            <IconButton
              aria-label="Refresh"
              loading={isFetching}
              size="sm"
              onClick={() => refetch()}
              variant="outline"
            >
              <FiRefreshCw />
            </IconButton>
          </HStack>
        </Card.Header>
        <Card.Body>
          <Text color="red.500">Failed to load Helm release activity.</Text>
        </Card.Body>
      </Card.Root>
    )
  }

  return (
    <Stack gap={4}>
      {activity.data?.length === 0 ? (
        <Card.Root>
          <Card.Header>
            <Heading size="md">Helm Release Activity</Heading>
          </Card.Header>
          <Card.Body>
            <Text color="fg.muted">No recent Helm release activity found.</Text>
          </Card.Body>
        </Card.Root>
      ) : (
        activity.data?.map((release) => (
          <Card.Root key={release.release_name}>
            <Card.Header>
              <HStack justify="space-between" align="center">
                <HStack>
                  <FiFileText />
                  <Text fontWeight="bold">{release.release_name}</Text>
                </HStack>
                <IconButton
                  aria-label={
                    expanded === release.release_name ? "Collapse" : "Expand"
                  }
                  size="sm"
                  variant="ghost"
                  onClick={() =>
                    setExpanded(
                      expanded === release.release_name
                        ? null
                        : release.release_name,
                    )
                  }
                >
                  {expanded === release.release_name ? (
                    <FiChevronUp />
                  ) : (
                    <FiChevronDown />
                  )}
                </IconButton>
              </HStack>
            </Card.Header>
            <Card.Body>
              <Stack gap={2}>
                {release.changes.map((change, idx) => (
                  <Box
                    key={idx}
                    borderBottom="1px solid"
                    borderColor="gray.100"
                    pb={2}
                    mb={2}
                  >
                    <HStack gap={2} align="center">
                      <Badge
                        colorScheme={
                          change.change_type === "CREATED"
                            ? "green"
                            : change.change_type === "MODIFIED"
                              ? "blue"
                              : change.change_type === "DELETED"
                                ? "red"
                                : "gray"
                        }
                      >
                        {change.change_type}
                      </Badge>
                      <Text fontSize="sm" color="gray.500">
                        {new Date(change.timestamp).toLocaleString()}
                      </Text>
                      {change.user && (
                        <Text fontSize="sm" color="gray.600">
                          by {change.user}
                        </Text>
                      )}
                    </HStack>
                    <Collapse
                      in={expanded === release.release_name}
                      animateOpacity
                    >
                      {change.yaml && (
                        <Box
                          mt={2}
                          p={3}
                          borderRadius="md"
                          fontFamily="mono"
                          fontSize="sm"
                          whiteSpace="pre-wrap"
                          overflowX="auto"
                        >
                          {change.yaml}
                        </Box>
                      )}
                    </Collapse>
                  </Box>
                ))}
              </Stack>
            </Card.Body>
          </Card.Root>
        ))
      )}
    </Stack>
  )
}

export default HelmReleaseActivitySummary

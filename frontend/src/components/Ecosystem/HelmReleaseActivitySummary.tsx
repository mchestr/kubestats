import { EcosystemService, type HelmReleaseActivityListPublic } from "@/client"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Badge,
  Box,
  Button,
  Card,
  Flex,
  HStack,
  Heading,
  IconButton,
  Spinner,
  Table,
  Text,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import {
  FiChevronDown,
  FiChevronRight,
  FiEye,
  FiRefreshCw,
} from "react-icons/fi"

export function HelmReleaseActivitySummary() {
  const [selectedYaml, setSelectedYaml] = useState<string | null>(null)
  const [selectedTitle, setSelectedTitle] = useState<string>("")
  const [isOpen, setIsOpen] = useState(false)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
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

  const handleViewYaml = (yaml: string, title: string) => {
    setSelectedYaml(yaml)
    setSelectedTitle(title)
    setIsOpen(true)
  }

  const toggleExpand = (releaseName: string) => {
    setExpanded((prev) => ({ ...prev, [releaseName]: !prev[releaseName] }))
  }

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
    <Card.Root>
      <Card.Header>
        <HStack justify="space-between" align="center">
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
        {(activity.data || []).length === 0 ? (
          <Text color="fg.muted">No recent Helm release activity found.</Text>
        ) : (
          <div>
            {(activity.data || []).map((release) => (
              <Box
                key={release.release_name}
                borderWidth="1px"
                borderRadius="md"
                p={3}
              >
                <HStack
                  as="button"
                  w="100%"
                  justify="space-between"
                  onClick={() => toggleExpand(release.release_name)}
                  cursor="pointer"
                >
                  <HStack>
                    {expanded[release.release_name] ? (
                      <FiChevronDown />
                    ) : (
                      <FiChevronRight />
                    )}
                    <Heading size="sm">{release.release_name}</Heading>
                    <Badge colorScheme="purple" fontSize="0.8em">
                      {release.changes.length} change
                      {release.changes.length !== 1 ? "s" : ""}
                    </Badge>
                  </HStack>
                  <Text fontSize="sm" color="gray.500">
                    Most recent:{" "}
                    {release.changes[0]?.timestamp
                      ? new Date(release.changes[0].timestamp).toLocaleString()
                      : "-"}
                  </Text>
                </HStack>
                {expanded[release.release_name] && (
                  <Box mt={3}>
                    <Table.Root size="sm" minW="600px">
                      <Table.Header>
                        <Table.Row>
                          <Table.ColumnHeader>Type</Table.ColumnHeader>
                          <Table.ColumnHeader>Timestamp</Table.ColumnHeader>
                          <Table.ColumnHeader>User</Table.ColumnHeader>
                          <Table.ColumnHeader>YAML</Table.ColumnHeader>
                        </Table.Row>
                      </Table.Header>
                      <Table.Body>
                        {release.changes.map((change, idx) => (
                          <Table.Row key={idx}>
                            <Table.Cell>
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
                                fontSize="0.8em"
                                px={2}
                                py={1}
                                borderRadius="md"
                              >
                                {change.change_type}
                              </Badge>
                            </Table.Cell>
                            <Table.Cell>
                              <Text fontSize="sm" color="gray.600">
                                {new Date(change.timestamp).toLocaleString()}
                              </Text>
                            </Table.Cell>
                            <Table.Cell>
                              <Text fontSize="sm" color="gray.600">
                                {change.user || "-"}
                              </Text>
                            </Table.Cell>
                            <Table.Cell>
                              {change.yaml ? (
                                <IconButton
                                  aria-label="View YAML"
                                  size="xs"
                                  variant="ghost"
                                  onClick={() =>
                                    handleViewYaml(
                                      change.yaml || "",
                                      `${release.release_name} (${change.change_type})`,
                                    )
                                  }
                                >
                                  <FiEye />
                                </IconButton>
                              ) : (
                                <Text color="gray.400" fontSize="sm">
                                  -
                                </Text>
                              )}
                            </Table.Cell>
                          </Table.Row>
                        ))}
                      </Table.Body>
                    </Table.Root>
                  </Box>
                )}
              </Box>
            ))}
          </div>
        )}
        <DialogRoot open={isOpen} onOpenChange={() => setIsOpen(false)}>
          <DialogContent maxW="4xl">
            <DialogHeader>
              <DialogTitle>{selectedTitle} YAML</DialogTitle>
            </DialogHeader>
            <DialogCloseTrigger />
            <DialogBody>
              <Box
                as="pre"
                fontSize="sm"
                fontFamily="mono"
                whiteSpace="pre-wrap"
                overflowX="auto"
                p={3}
                borderRadius="md"
                maxH="60vh"
              >
                {selectedYaml}
              </Box>
            </DialogBody>
            <DialogFooter>
              <Button onClick={() => setIsOpen(false)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </DialogRoot>
      </Card.Body>
    </Card.Root>
  )
}

export default HelmReleaseActivitySummary

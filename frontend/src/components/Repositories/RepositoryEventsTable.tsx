import {
  Badge,
  Box,
  Button,
  ButtonGroup,
  Card,
  Flex,
  HStack,
  Heading,
  Link,
  Skeleton,
  Stack,
  Table,
  Text,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { FiClock, FiFileText, FiGitCommit } from "react-icons/fi"

import type {
  KubernetesResourceEventPublic,
  KubernetesResourceEventsPublic,
  RepositoryPublic,
} from "../../client"
import { Repositories } from "../../client"
import { Pagination } from "../ui/pagination"

interface RepositoryEventsTableProps {
  repository: RepositoryPublic
}

function RepositoryEventsTable({ repository }: RepositoryEventsTableProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("")
  const [resourceKindFilter, setResourceKindFilter] = useState<string>("")
  const [resourceNamespaceFilter, setResourceNamespaceFilter] =
    useState<string>("")

  const {
    data: eventsData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: [
      "repository-events",
      repository.id,
      currentPage,
      itemsPerPage,
      eventTypeFilter,
      resourceKindFilter,
      resourceNamespaceFilter,
    ],
    queryFn: () =>
      Repositories.repositoriesReadRepositoryEvents({
        path: { repository_id: repository.id },
        query: {
          skip: (currentPage - 1) * itemsPerPage,
          limit: itemsPerPage,
          event_type: eventTypeFilter || undefined,
          resource_kind: resourceKindFilter || undefined,
          resource_namespace: resourceNamespaceFilter || undefined,
        },
      }),
    enabled: !!repository.id,
  })

  const events =
    (eventsData?.data as KubernetesResourceEventsPublic | undefined)?.data || []
  const totalCount =
    (eventsData?.data as KubernetesResourceEventsPublic | undefined)?.count || 0

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const getEventTypeBadge = (eventType: string) => {
    const colorMap: Record<string, string> = {
      CREATED: "green",
      MODIFIED: "blue",
      DELETED: "red",
    }
    return (
      <Badge colorPalette={colorMap[eventType] || "gray"} variant="subtle">
        {eventType}
      </Badge>
    )
  }

  const getChangesPreview = (changes: string[]) => {
    if (!changes || changes.length === 0) return "No changes detected"
    if (changes.length === 1) return changes[0]
    return `${changes[0]} (+${changes.length - 1} more)`
  }

  if (isLoading) {
    return (
      <Card.Root>
        <Card.Header>
          <Heading size="lg">Resource Events</Heading>
          <Text color="fg.muted">
            Recent Kubernetes resource lifecycle events
          </Text>
        </Card.Header>
        <Card.Body>
          <Stack gap={4}>
            <Skeleton height="40px" />
            <Skeleton height="300px" />
          </Stack>
        </Card.Body>
      </Card.Root>
    )
  }

  if (isError) {
    return (
      <Card.Root>
        <Card.Header>
          <Heading size="lg">Resource Events</Heading>
          <Text color="fg.muted">
            Recent Kubernetes resource lifecycle events
          </Text>
        </Card.Header>
        <Card.Body>
          <Box textAlign="center" py={12}>
            <Text color="fg.muted">Unable to load events data</Text>
          </Box>
        </Card.Body>
      </Card.Root>
    )
  }

  return (
    <Card.Root>
      <Card.Header>
        <Heading size="lg">Resource Events</Heading>
        <Text color="fg.muted">
          Recent Kubernetes resource lifecycle events
        </Text>
      </Card.Header>
      <Card.Body>
        <Stack gap={4}>
          {/* Filters */}
          <HStack gap={4} flexWrap="wrap">
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={2}>
                Event Type
              </Text>
              <ButtonGroup size="sm" variant="outline">
                <Button
                  variant={eventTypeFilter === "" ? "solid" : "outline"}
                  onClick={() => {
                    setEventTypeFilter("")
                    setCurrentPage(1)
                  }}
                >
                  All
                </Button>
                <Button
                  variant={eventTypeFilter === "CREATED" ? "solid" : "outline"}
                  onClick={() => {
                    setEventTypeFilter("CREATED")
                    setCurrentPage(1)
                  }}
                >
                  Created
                </Button>
                <Button
                  variant={eventTypeFilter === "MODIFIED" ? "solid" : "outline"}
                  onClick={() => {
                    setEventTypeFilter("MODIFIED")
                    setCurrentPage(1)
                  }}
                >
                  Modified
                </Button>
                <Button
                  variant={eventTypeFilter === "DELETED" ? "solid" : "outline"}
                  onClick={() => {
                    setEventTypeFilter("DELETED")
                    setCurrentPage(1)
                  }}
                >
                  Deleted
                </Button>
              </ButtonGroup>
            </Box>

            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={2}>
                Resource Kind
              </Text>
              <ButtonGroup size="sm" variant="outline">
                <Button
                  variant={resourceKindFilter === "" ? "solid" : "outline"}
                  onClick={() => {
                    setResourceKindFilter("")
                    setCurrentPage(1)
                  }}
                >
                  All
                </Button>
                <Button
                  variant={
                    resourceKindFilter === "HelmRelease" ? "solid" : "outline"
                  }
                  onClick={() => {
                    setResourceKindFilter("HelmRelease")
                    setCurrentPage(1)
                  }}
                >
                  HelmRelease
                </Button>
                <Button
                  variant={
                    resourceKindFilter === "Kustomization" ? "solid" : "outline"
                  }
                  onClick={() => {
                    setResourceKindFilter("Kustomization")
                    setCurrentPage(1)
                  }}
                >
                  Kustomization
                </Button>
                <Button
                  variant={
                    resourceKindFilter === "GitRepository" ? "solid" : "outline"
                  }
                  onClick={() => {
                    setResourceKindFilter("GitRepository")
                    setCurrentPage(1)
                  }}
                >
                  GitRepository
                </Button>
                <Button
                  variant={
                    resourceKindFilter === "OCIRepository" ? "solid" : "outline"
                  }
                  onClick={() => {
                    setResourceKindFilter("OCIRepository")
                    setCurrentPage(1)
                  }}
                >
                  OCIRepository
                </Button>
              </ButtonGroup>
            </Box>

            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={2}>
                Namespace
              </Text>
              <ButtonGroup size="sm" variant="outline">
                <Button
                  variant={resourceNamespaceFilter === "" ? "solid" : "outline"}
                  onClick={() => {
                    setResourceNamespaceFilter("")
                    setCurrentPage(1)
                  }}
                >
                  All
                </Button>
                <Button
                  variant={
                    resourceNamespaceFilter === "default" ? "solid" : "outline"
                  }
                  onClick={() => {
                    setResourceNamespaceFilter("default")
                    setCurrentPage(1)
                  }}
                >
                  default
                </Button>
                <Button
                  variant={
                    resourceNamespaceFilter === "kube-system"
                      ? "solid"
                      : "outline"
                  }
                  onClick={() => {
                    setResourceNamespaceFilter("kube-system")
                    setCurrentPage(1)
                  }}
                >
                  kube-system
                </Button>
              </ButtonGroup>
            </Box>
          </HStack>

          {/* Events Table */}
          {events.length === 0 ? (
            <Box textAlign="center" py={12}>
              <Text color="fg.muted">No events found</Text>
              {(eventTypeFilter ||
                resourceKindFilter ||
                resourceNamespaceFilter) && (
                <Text fontSize="sm" color="fg.muted" mt={2}>
                  Try adjusting your filters
                </Text>
              )}
            </Box>
          ) : (
            <>
              <Box overflowX="auto">
                <Table.Root size="sm">
                  <Table.Header>
                    <Table.Row>
                      <Table.ColumnHeader>Event</Table.ColumnHeader>
                      <Table.ColumnHeader>Resource</Table.ColumnHeader>
                      <Table.ColumnHeader>Namespace</Table.ColumnHeader>
                      <Table.ColumnHeader>Changes</Table.ColumnHeader>
                      <Table.ColumnHeader>File Path</Table.ColumnHeader>
                      <Table.ColumnHeader>Timestamp</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {events.map((event: KubernetesResourceEventPublic) => (
                      <Table.Row key={event.id}>
                        <Table.Cell>
                          <Flex alignItems="center" gap={2}>
                            <FiGitCommit size={14} />
                            {getEventTypeBadge(event.event_type)}
                          </Flex>
                        </Table.Cell>
                        <Table.Cell>
                          <Stack gap={1}>
                            <Text fontWeight="medium" fontSize="sm">
                              {event.resource_name}
                            </Text>
                            <Text fontSize="xs" color="fg.muted">
                              {event.resource_kind}
                            </Text>
                          </Stack>
                        </Table.Cell>
                        <Table.Cell>
                          <Text fontSize="sm" fontFamily="mono">
                            {event.resource_namespace || (
                              <Text
                                as="span"
                                color="fg.muted"
                                fontStyle="italic"
                              >
                                cluster-scoped
                              </Text>
                            )}
                          </Text>
                        </Table.Cell>
                        <Table.Cell>
                          <Text fontSize="sm" color="fg.muted">
                            {getChangesPreview(event.changes_detected)}
                          </Text>
                        </Table.Cell>
                        <Table.Cell>
                          <Link
                            href={`https://github.com/${repository.full_name}/blob/${repository.default_branch}/${event.file_path}`}
                            target="_blank"
                          >
                            <Flex alignItems="center" gap={1}>
                              <FiFileText size={12} />
                              <Text
                                fontSize="xs"
                                fontFamily="mono"
                                color="fg.muted"
                                maxW="200px"
                                truncate
                              >
                                {event.file_path}
                              </Text>
                            </Flex>
                          </Link>
                        </Table.Cell>
                        <Table.Cell>
                          <Flex alignItems="center" gap={1}>
                            <FiClock size={12} />
                            <Text fontSize="xs" color="fg.muted">
                              {formatDate(event.event_timestamp)}
                            </Text>
                          </Flex>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
              </Box>

              {/* Pagination */}
              <Pagination
                currentPage={currentPage}
                totalItems={totalCount}
                itemsPerPage={itemsPerPage}
                onPageChange={setCurrentPage}
                onItemsPerPageChange={(newItemsPerPage) => {
                  setItemsPerPage(newItemsPerPage)
                  setCurrentPage(1)
                }}
                pageSizeOptions={[10, 25, 50, 100]}
              />
            </>
          )}
        </Stack>
      </Card.Body>
    </Card.Root>
  )
}

export default RepositoryEventsTable

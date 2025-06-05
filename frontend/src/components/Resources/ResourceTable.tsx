import { Box, Button, Flex, IconButton, Table } from "@chakra-ui/react"
import type React from "react"
import { FiChevronLeft, FiChevronRight } from "react-icons/fi"

interface ResourceTableProps {
  resources: any[]
  count: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onRowClick: (group: any) => void
}

export const ResourceTable: React.FC<ResourceTableProps> = ({
  resources,
  count,
  page,
  pageSize,
  onPageChange,
  onRowClick,
}) => {
  const totalPages = Math.ceil(count / pageSize)

  return (
    <Box mt={8} borderRadius="md" boxShadow="sm" overflowX="auto">
      <Table.Root width="full">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Kind</Table.ColumnHeader>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Total Count</Table.ColumnHeader>
            <Table.ColumnHeader>Repositories</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {resources.length === 0 ? (
            <Table.Row>
              <Table.Cell colSpan={4} textAlign="center">
                No resources found.
              </Table.Cell>
            </Table.Row>
          ) : (
            resources.map((g: any) => (
              <Table.Row
                key={`${g.kind}-${g.name}`}
                _hover={{ bg: "bg.muted", cursor: "pointer" }}
                onClick={() => onRowClick(g)}
              >
                <Table.Cell>{g.kind}</Table.Cell>
                <Table.Cell>{g.name}</Table.Cell>
                <Table.Cell>{g.total_count}</Table.Cell>
                <Table.Cell>
                  <Button
                    size="xs"
                    onClick={(e) => {
                      e.stopPropagation()
                      onRowClick(g)
                    }}
                  >
                    View Repositories ({g.repositories.length})
                  </Button>
                </Table.Cell>
              </Table.Row>
            ))
          )}
        </Table.Body>
        <Table.Footer>
          <Table.Row>
            <Table.Cell colSpan={4} textAlign="right">
              {/* Pagination controls can be placed here if desired, but we'll keep them outside for layout consistency */}
            </Table.Cell>
          </Table.Row>
        </Table.Footer>
      </Table.Root>
      {/* Pagination */}
      <Flex align="center" justify="flex-end" gap={2} p={4}>
        <IconButton
          aria-label="Previous page"
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          size="sm"
          variant="ghost"
        >
          <FiChevronLeft />
        </IconButton>
        <Box fontSize="sm">
          Page {page} of {totalPages}
        </Box>
        <IconButton
          aria-label="Next page"
          onClick={() => onPageChange(page + 1)}
          disabled={page === totalPages || totalPages === 0}
          size="sm"
          variant="ghost"
        >
          <FiChevronRight />
        </IconButton>
      </Flex>
    </Box>
  )
}

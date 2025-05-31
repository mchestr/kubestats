import {
  Button,
  ButtonGroup,
  Flex,
  HStack,
  Input,
  Separator,
  Stack,
  Text,
} from "@chakra-ui/react"
import { FiSearch, FiX } from "react-icons/fi"

export interface RepositoryFilters {
  search: string
  syncStatus: string
}

interface RepositoryFiltersProps {
  filters: RepositoryFilters
  onFiltersChange: (filters: RepositoryFilters) => void
}

export function RepositoryFiltersComponent({
  filters,
  onFiltersChange,
}: RepositoryFiltersProps) {
  const syncStatuses = [
    "success",
    "pending",
    "error",
    "syncing",
    "blocked",
    "pending_approval",
  ]

  const handleSearchChange = (value: string) => {
    onFiltersChange({ ...filters, search: value })
  }

  const handleSyncStatusChange = (status: string) => {
    onFiltersChange({
      ...filters,
      syncStatus: filters.syncStatus === status ? "" : status,
    })
  }

  const clearAllFilters = () => {
    onFiltersChange({ search: "", syncStatus: "" })
  }

  const hasActiveFilters = filters.search || filters.syncStatus

  return (
    <Stack
      gap={4}
      bg="bg.subtle"
      p={4}
      borderTopRadius="lg"
      borderBottomWidth="1px"
      borderColor="border.subtle"
    >
      {/* Desktop Layout */}
      <Flex
        gap={4}
        alignItems="center"
        flexWrap={{ base: "wrap", lg: "nowrap" }}
        display={{ base: "none", md: "flex" }}
      >
        {/* Search Input */}
        <HStack flex={1} minW="200px" maxW="400px">
          <FiSearch />
          <Input
            placeholder="Search repositories..."
            value={filters.search}
            onChange={(e) => handleSearchChange(e.target.value)}
            variant="outline"
            flex={1}
          />
        </HStack>

        {/* Sync Status Filter */}
        <Separator orientation="vertical" height="8" />
        <HStack gap={2}>
          <Text
            fontSize="sm"
            fontWeight="medium"
            color="fg.muted"
            minW="max-content"
          >
            Status:
          </Text>
          <ButtonGroup size="sm" variant="outline">
            {syncStatuses.map((status) => (
              <Button
                key={status}
                variant={filters.syncStatus === status ? "solid" : "outline"}
                onClick={() => handleSyncStatusChange(status)}
                size="sm"
              >
                {status
                  .split("_")
                  .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
                  .join(" ")}
              </Button>
            ))}
          </ButtonGroup>
        </HStack>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <>
            <Separator orientation="vertical" height="8" />
            <Button size="sm" variant="ghost" onClick={clearAllFilters}>
              <FiX />
              Clear
            </Button>
          </>
        )}
      </Flex>

      {/* Mobile Layout */}
      <Stack gap={3} display={{ base: "flex", md: "none" }}>
        {/* Search Input */}
        <HStack>
          <FiSearch />
          <Input
            placeholder="Search repositories..."
            value={filters.search}
            onChange={(e) => handleSearchChange(e.target.value)}
            variant="outline"
            flex={1}
          />
        </HStack>

        <Flex gap={4} flexWrap="wrap" alignItems="center">
          {/* Sync Status Filter */}
          <Stack gap={2} flex={1} minW="200px">
            <Text fontSize="sm" fontWeight="medium" color="fg.muted">
              Status:
            </Text>
            <ButtonGroup size="sm" variant="outline" flexWrap="wrap">
              {syncStatuses.map((status) => (
                <Button
                  key={status}
                  variant={filters.syncStatus === status ? "solid" : "outline"}
                  onClick={() => handleSyncStatusChange(status)}
                  size="sm"
                >
                  {status
                    .split("_")
                    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
                    .join(" ")}
                </Button>
              ))}
            </ButtonGroup>
          </Stack>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <Button
              size="sm"
              variant="ghost"
              onClick={clearAllFilters}
              alignSelf="flex-end"
            >
              <FiX />
              Clear All
            </Button>
          )}
        </Flex>
      </Stack>
    </Stack>
  )
}

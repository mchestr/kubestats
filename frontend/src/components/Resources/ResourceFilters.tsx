import {
  Box,
  Checkbox,
  CheckboxGroup,
  Flex,
  IconButton,
  Input,
  Select,
  Stack,
  createListCollection,
} from "@chakra-ui/react"
import React, { useState, useMemo } from "react"
import { IoClose } from "react-icons/io5"

interface ResourceFiltersProps {
  repositories: Array<{
    id: string
    name: string
  }>
  filterOptions: {
    kinds: string[]
    namespaces: string[]
    apiVersions: string[]
    statuses: string[]
  }
  repositoryId: string | null
  kind: string | null
  namespace: string | null
  status: string[]
  apiVersion: string | null
  search: string
  onRepositoryChange: (id: string | null) => void
  onKindChange: (kind: string | null) => void
  onNamespaceChange: (ns: string | null) => void
  onStatusChange: (status: string[]) => void
  onApiVersionChange: (apiVersion: string | null) => void
  onSearchChange: (search: string) => void
}

export const ResourceFilters: React.FC<ResourceFiltersProps> = ({
  repositories,
  filterOptions,
  repositoryId,
  kind,
  namespace,
  status,
  apiVersion,
  search,
  onRepositoryChange,
  onKindChange,
  onNamespaceChange,
  onStatusChange,
  onApiVersionChange,
  onSearchChange,
}) => {
  // Debounced search
  const [searchInput, setSearchInput] = useState(search)
  React.useEffect(() => {
    const handler = setTimeout(() => {
      onSearchChange(searchInput)
    }, 400)
    return () => clearTimeout(handler)
  }, [searchInput, onSearchChange])

  // Chakra v3 Select collections
  const repoCollection = useMemo(
    () =>
      createListCollection({
        items: repositories.map((r) => ({ label: r.name, value: r.id })),
      }),
    [repositories],
  )
  const kindCollection = useMemo(
    () =>
      createListCollection({
        items: filterOptions.kinds.map((k) => ({ label: k, value: k })),
      }),
    [filterOptions.kinds],
  )
  const nsCollection = useMemo(
    () =>
      createListCollection({
        items: filterOptions.namespaces.map((ns) => ({ label: ns, value: ns })),
      }),
    [filterOptions.namespaces],
  )
  const apiVersionCollection = useMemo(
    () =>
      createListCollection({
        items: filterOptions.apiVersions.map((v) => ({ label: v, value: v })),
      }),
    [filterOptions.apiVersions],
  )

  // Clear all filters
  const handleClear = () => {
    onRepositoryChange(null)
    onKindChange(null)
    onNamespaceChange(null)
    onStatusChange([])
    onApiVersionChange(null)
    setSearchInput("")
    onSearchChange("")
  }

  return (
    <Box mb={6} p={4} borderRadius="md" boxShadow="sm">
      <Flex wrap="wrap" gap={4} align="flex-end">
        {/* Repository */}
        <Box minW="200px">
          <label
            htmlFor="repo-select"
            style={{ fontSize: 13, fontWeight: 500 }}
          >
            Repository
          </label>
          <Select.Root
            id="repo-select"
            collection={repoCollection}
            value={repositoryId ? [repositoryId] : []}
            onValueChange={({ value }) => onRepositoryChange(value[0] || null)}
            size="sm"
          >
            <Select.HiddenSelect />
            <Select.Control>
              <Select.Trigger>
                <Select.ValueText placeholder="All repositories" />
              </Select.Trigger>
              <Select.IndicatorGroup>
                <Select.Indicator />
              </Select.IndicatorGroup>
            </Select.Control>
            <Select.Positioner>
              <Select.Content>
                {repoCollection.items.map((item) => (
                  <Select.Item item={item} key={item.value}>
                    {item.label}
                  </Select.Item>
                ))}
              </Select.Content>
            </Select.Positioner>
          </Select.Root>
        </Box>
        {/* Kind */}
        <Box minW="160px">
          <label
            htmlFor="kind-select"
            style={{ fontSize: 13, fontWeight: 500 }}
          >
            Kind
          </label>
          <Select.Root
            id="kind-select"
            collection={kindCollection}
            value={kind ? [kind] : []}
            onValueChange={({ value }) => onKindChange(value[0] || null)}
            size="sm"
          >
            <Select.HiddenSelect />
            <Select.Control>
              <Select.Trigger>
                <Select.ValueText placeholder="All kinds" />
              </Select.Trigger>
              <Select.IndicatorGroup>
                <Select.Indicator />
              </Select.IndicatorGroup>
            </Select.Control>
            <Select.Positioner>
              <Select.Content>
                {kindCollection.items.map((item) => (
                  <Select.Item item={item} key={item.value}>
                    {item.label}
                  </Select.Item>
                ))}
              </Select.Content>
            </Select.Positioner>
          </Select.Root>
        </Box>
        {/* Namespace */}
        <Box minW="160px">
          <label
            htmlFor="namespace-select"
            style={{ fontSize: 13, fontWeight: 500 }}
          >
            Namespace
          </label>
          <Select.Root
            id="namespace-select"
            collection={nsCollection}
            value={namespace ? [namespace] : []}
            onValueChange={({ value }) => onNamespaceChange(value[0] || null)}
            size="sm"
          >
            <Select.HiddenSelect />
            <Select.Control>
              <Select.Trigger>
                <Select.ValueText placeholder="All namespaces" />
              </Select.Trigger>
              <Select.IndicatorGroup>
                <Select.Indicator />
              </Select.IndicatorGroup>
            </Select.Control>
            <Select.Positioner>
              <Select.Content>
                {nsCollection.items.map((item) => (
                  <Select.Item item={item} key={item.value}>
                    {item.label}
                  </Select.Item>
                ))}
              </Select.Content>
            </Select.Positioner>
          </Select.Root>
        </Box>
        {/* Status (multi-select) */}
        <Box minW="180px">
          <label
            htmlFor="status-group"
            style={{ fontSize: 13, fontWeight: 500 }}
          >
            Status
          </label>
          <CheckboxGroup
            id="status-group"
            value={status}
            onChange={(vals) => onStatusChange(vals as unknown as string[])}
          >
            <Stack direction="row" wrap="wrap" mt={1}>
              {filterOptions.statuses.map((s) => (
                <Checkbox.Root key={s} value={s} size="sm">
                  {s}
                </Checkbox.Root>
              ))}
            </Stack>
          </CheckboxGroup>
        </Box>
        {/* API Version */}
        <Box minW="180px">
          <label
            htmlFor="api-version-select"
            style={{ fontSize: 13, fontWeight: 500 }}
          >
            API Version
          </label>
          <Select.Root
            id="api-version-select"
            collection={apiVersionCollection}
            value={apiVersion ? [apiVersion] : []}
            onValueChange={({ value }) => onApiVersionChange(value[0] || null)}
            size="sm"
          >
            <Select.HiddenSelect />
            <Select.Control>
              <Select.Trigger>
                <Select.ValueText placeholder="All versions" />
              </Select.Trigger>
              <Select.IndicatorGroup>
                <Select.Indicator />
              </Select.IndicatorGroup>
            </Select.Control>
            <Select.Positioner>
              <Select.Content>
                {apiVersionCollection.items.map((item) => (
                  <Select.Item item={item} key={item.value}>
                    {item.label}
                  </Select.Item>
                ))}
              </Select.Content>
            </Select.Positioner>
          </Select.Root>
        </Box>
        {/* Search */}
        <Box minW="200px">
          <label
            htmlFor="search-input"
            style={{ fontSize: 13, fontWeight: 500 }}
          >
            Search Name
          </label>
          <Input
            id="search-input"
            value={searchInput}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setSearchInput(e.target.value)
            }
            placeholder="Search by name..."
            size="sm"
            mt={1}
          />
        </Box>
        {/* Clear Button */}
        <Box>
          <IconButton
            aria-label="Clear filters"
            onClick={handleClear}
            size="sm"
            variant="outline"
            mt={1}
          >
            <IoClose />
          </IconButton>
        </Box>
      </Flex>
    </Box>
  )
}

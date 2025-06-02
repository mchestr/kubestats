import {
  Button,
  ButtonGroup,
  HStack,
  IconButton,
  Stack,
  Text,
} from "@chakra-ui/react"
import {
  FiChevronLeft,
  FiChevronRight,
  FiChevronsLeft,
  FiChevronsRight,
} from "react-icons/fi"

interface PaginationProps {
  currentPage: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
  onItemsPerPageChange: (itemsPerPage: number) => void
  pageSizeOptions?: number[]
}

export function Pagination({
  currentPage,
  totalItems,
  itemsPerPage,
  onPageChange,
  onItemsPerPageChange,
  pageSizeOptions = [10, 25, 50, 100],
}: PaginationProps) {
  const totalPages = Math.ceil(totalItems / itemsPerPage)
  const canGoPrevious = currentPage > 1
  const canGoNext = currentPage < totalPages

  // Generate page numbers to show
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const maxVisiblePages = 7

    if (totalPages <= maxVisiblePages) {
      // Show all pages
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // Show first page
      pages.push(1)

      if (currentPage <= 4) {
        // Show pages 2, 3, 4, 5, ..., last
        for (let i = 2; i <= 5; i++) {
          pages.push(i)
        }
        pages.push("...")
        pages.push(totalPages)
      } else if (currentPage >= totalPages - 3) {
        // Show 1, ..., last-4, last-3, last-2, last-1, last
        pages.push("...")
        for (let i = totalPages - 4; i <= totalPages; i++) {
          pages.push(i)
        }
      } else {
        // Show 1, ..., current-1, current, current+1, ..., last
        pages.push("...")
        pages.push(currentPage - 1)
        pages.push(currentPage)
        pages.push(currentPage + 1)
        pages.push("...")
        pages.push(totalPages)
      }
    }

    return pages
  }

  if (totalItems === 0) {
    return null
  }

  return (
    <Stack gap={4}>
      <HStack justifyContent="space-between" flexWrap="wrap">
        <HStack gap={2} />

        <HStack gap={2} marginTop={{ base: 2 }}>
          <Text fontSize="sm" color="fg.muted">
            Show:
          </Text>
          <ButtonGroup size="sm">
            {pageSizeOptions.map((size) => (
              <Button
                key={size}
                variant={size === itemsPerPage ? "solid" : "outline"}
                onClick={() => onItemsPerPageChange(size)}
              >
                {size}
              </Button>
            ))}
          </ButtonGroup>
          <Text fontSize="sm" color="fg.muted">
            per page
          </Text>
        </HStack>
      </HStack>

      {totalPages > 1 && (
        <HStack justifyContent="center" gap={1}>
          <IconButton
            variant="outline"
            size="sm"
            onClick={() => onPageChange(1)}
            disabled={!canGoPrevious}
            aria-label="First page"
          >
            <FiChevronsLeft />
          </IconButton>

          <IconButton
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={!canGoPrevious}
            aria-label="Previous page"
          >
            <FiChevronLeft />
          </IconButton>

          {getPageNumbers().map((page, index) => (
            <Button
              key={`${page}-${index}`}
              variant={page === currentPage ? "solid" : "outline"}
              size="sm"
              onClick={() => typeof page === "number" && onPageChange(page)}
              disabled={typeof page === "string"}
              minW="40px"
            >
              {page}
            </Button>
          ))}

          <IconButton
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={!canGoNext}
            aria-label="Next page"
          >
            <FiChevronRight />
          </IconButton>

          <IconButton
            variant="outline"
            size="sm"
            onClick={() => onPageChange(totalPages)}
            disabled={!canGoNext}
            aria-label="Last page"
          >
            <FiChevronsRight />
          </IconButton>
        </HStack>
      )}
    </Stack>
  )
}

import { Box, Flex, Text } from "@chakra-ui/react"
import { Link, useRouterState } from "@tanstack/react-router"
import { FiChevronRight, FiHome } from "react-icons/fi"

interface BreadcrumbItem {
  label: string
  path: string
  isCurrentPage?: boolean
}

const Breadcrumb = () => {
  const routerState = useRouterState()
  const pathname = routerState.location.pathname

  const getBreadcrumbItems = (): BreadcrumbItem[] => {
    const items: BreadcrumbItem[] = [{ label: "Home", path: "/" }]

    if (pathname === "/") {
      items[0].isCurrentPage = true
      return items
    }

    const pathSegments = pathname.split("/").filter(Boolean)

    for (let i = 0; i < pathSegments.length; i++) {
      const segment = pathSegments[i]
      const path = `/${pathSegments.slice(0, i + 1).join("/")}`
      const isLast = i === pathSegments.length - 1

      let label = segment.charAt(0).toUpperCase() + segment.slice(1)

      // Handle specific routes
      switch (segment) {
        case "repositories":
          label = "Repositories"
          break
        case "tasks":
          label = "Tasks"
          break
        default:
          break
      }

      items.push({
        label,
        path,
        isCurrentPage: isLast,
      })
    }

    return items
  }

  const breadcrumbItems = getBreadcrumbItems()

  if (breadcrumbItems.length <= 1) {
    return null
  }

  return (
    <Box mb={6}>
      <Flex align="center" gap={2} fontSize="sm">
        {breadcrumbItems.map((item, index) => (
          <Flex key={item.path} align="center" gap={2}>
            {index === 0 && <FiHome size="14px" />}

            {item.isCurrentPage ? (
              <Text fontWeight="medium" color="fg.emphasized">
                {item.label}
              </Text>
            ) : (
              <Link
                to={item.path}
                style={{
                  color: "var(--chakra-colors-fg-muted)",
                  textDecoration: "none",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = "var(--chakra-colors-ui-main)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = "var(--chakra-colors-fg-muted)"
                }}
              >
                {item.label}
              </Link>
            )}

            {index < breadcrumbItems.length - 1 && (
              <FiChevronRight
                size="14px"
                color="var(--chakra-colors-fg-muted)"
              />
            )}
          </Flex>
        ))}
      </Flex>
    </Box>
  )
}

export default Breadcrumb

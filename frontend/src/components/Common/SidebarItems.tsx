import { Box, Flex, Stack, Text } from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink, useRouterState } from "@tanstack/react-router"
import {
  FiActivity,
  FiDatabase,
  FiGitBranch,
  FiHome,
  FiTrendingUp,
} from "react-icons/fi"
import type { IconType } from "react-icons/lib"

import type { UserPublic } from "@/client"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiTrendingUp, title: "Ecosystem", path: "/ecosystem" },
  { icon: FiDatabase, title: "Resources", path: "/resources" },
]

interface SidebarItemsProps {
  onClose?: () => void
}

interface Item {
  icon: IconType
  title: string
  path: string
}

interface NavItemProps {
  item: Item
  isActive: boolean
  onClose?: () => void
}

const NavItem = ({ item, isActive, onClose }: NavItemProps) => {
  const { icon: Icon, title, path } = item

  return (
    <RouterLink to={path} onClick={onClose}>
      <Flex
        align="center"
        gap={3}
        px={3}
        py={2.5}
        rounded="md"
        transition="all 0.2s"
        bg={isActive ? "bg.emphasized" : "transparent"}
        color={isActive ? "fg.emphasized" : "fg.default"}
        fontWeight={isActive ? "semibold" : "medium"}
        borderLeft={isActive ? "3px solid" : "3px solid transparent"}
        borderColor={isActive ? "ui.main" : "transparent"}
        position="relative"
        _hover={{
          bg: isActive ? "bg.emphasized" : "bg.subtle",
          color: "fg.emphasized",
          transform: "translateX(2px)",
        }}
        _focus={{
          outline: "2px solid",
          outlineColor: "ui.main",
          outlineOffset: "2px",
        }}
        _active={{
          transform: "translateX(0)",
        }}
        cursor="pointer"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            onClose?.()
          }
        }}
      >
        <Icon size="18px" />
        <Text fontSize="sm">{title}</Text>
        {isActive && (
          <Box
            position="absolute"
            right={3}
            w="6px"
            h="6px"
            bg="ui.main"
            rounded="full"
          />
        )}
      </Flex>
    </RouterLink>
  )
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  const finalItems: Item[] = currentUser?.is_superuser
    ? [
        ...items,
        { icon: FiGitBranch, title: "Repositories", path: "/repositories" },
        { icon: FiActivity, title: "Tasks", path: "/tasks" },
      ]
    : items

  return (
    <Stack gap={1}>
      <Text
        fontSize="xs"
        px={3}
        py={2}
        fontWeight="semibold"
        color="fg.muted"
        textTransform="uppercase"
        letterSpacing="wider"
      >
        Navigation
      </Text>
      <Stack gap={1}>
        {finalItems.map((item) => (
          <NavItem
            key={item.title}
            item={item}
            isActive={currentPath === item.path}
            onClose={onClose}
          />
        ))}
      </Stack>
    </Stack>
  )
}

export default SidebarItems

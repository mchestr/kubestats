import {
  Box,
  Button,
  Flex,
  HStack,
  IconButton,
  Stack,
  Text,
} from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { FaBars } from "react-icons/fa"
import { FiLogOut, FiMoon, FiSun, FiX } from "react-icons/fi"

import type { UserPublic } from "@/client"
import useAuth from "@/hooks/useAuth"
import { useColorMode } from "../ui/color-mode"
import {
  DrawerBackdrop,
  DrawerBody,
  DrawerContent,
  DrawerHeader,
  DrawerRoot,
  DrawerTrigger,
} from "../ui/drawer"
import SidebarItems from "./SidebarItems"

interface UserSectionProps {
  user: UserPublic
  isCompact?: boolean
}

const UserSection = ({ user, isCompact = false }: UserSectionProps) => {
  const getInitials = () => {
    if (user.full_name) {
      const nameParts = user.full_name.split(" ")
      if (nameParts.length >= 2) {
        return `${nameParts[0][0]}${nameParts[1][0]}`.toUpperCase()
      }
      return user.full_name[0].toUpperCase()
    }
    return user.email[0].toUpperCase()
  }

  const displayName = user.full_name || user.email.split("@")[0]

  return (
    <HStack gap={3} w="full">
      <Flex
        align="center"
        justify="center"
        w={isCompact ? "32px" : "40px"}
        h={isCompact ? "32px" : "40px"}
        bg="ui.main"
        color="white"
        borderRadius="full"
        fontSize={isCompact ? "sm" : "md"}
        fontWeight="medium"
      >
        {getInitials()}
      </Flex>
      {!isCompact && (
        <Stack gap={0} flex={1} minW={0}>
          <Text fontSize="sm" fontWeight="medium" truncate w="full">
            {displayName}
          </Text>
          <Text fontSize="xs" color="fg.muted" truncate w="full">
            {user.email}
          </Text>
        </Stack>
      )}
    </HStack>
  )
}

interface SidebarActionProps {
  icon: React.ElementType
  label: string
  onClick: () => void
  variant?: "ghost" | "solid"
}

const SidebarAction = ({
  icon: Icon,
  label,
  onClick,
  variant = "ghost",
}: SidebarActionProps) => (
  <Button
    variant={variant}
    size="sm"
    w="full"
    justifyContent="flex-start"
    onClick={onClick}
    gap={2}
    _hover={{
      bg: variant === "ghost" ? "bg.subtle" : undefined,
    }}
  >
    <Icon />
    {label}
  </Button>
)

const Sidebar = () => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const { logout } = useAuth()
  const { colorMode, toggleColorMode } = useColorMode()
  const [open, setOpen] = useState(false)

  const handleClose = () => setOpen(false)

  return (
    <>
      {/* Mobile Trigger */}
      <Box
        display={{ base: "block", md: "none" }}
        position="fixed"
        top={4}
        left={4}
        zIndex={1000}
      >
        <DrawerRoot
          placement="start"
          open={open}
          onOpenChange={(e) => setOpen(e.open)}
        >
          <DrawerTrigger asChild>
            <IconButton
              variant="solid"
              bg="bg.panel"
              border="1px solid"
              borderColor="border.subtle"
              shadow="lg"
              aria-label="Open navigation menu"
              size="sm"
              transition="all 0.2s"
              _hover={{
                shadow: "xl",
                transform: "translateY(-1px)",
              }}
              _active={{
                transform: "translateY(0)",
              }}
            >
              <FaBars />
            </IconButton>
          </DrawerTrigger>

          <DrawerBackdrop />
          <DrawerContent maxW="xs" p={0} animationDuration="0.3s">
            <DrawerHeader
              p={4}
              borderBottom="1px solid"
              borderColor="border.subtle"
              display="flex"
              alignItems="center"
              justifyContent="space-between"
              bg="bg.panel"
            >
              <Text fontWeight="semibold" fontSize="lg" color="ui.main">
                KubeStats
              </Text>
              <IconButton
                variant="ghost"
                size="sm"
                aria-label="Close menu"
                onClick={handleClose}
                _hover={{ bg: "bg.subtle" }}
              >
                <FiX />
              </IconButton>
            </DrawerHeader>

            <DrawerBody p={0}>
              <Stack gap={0} align="stretch" h="full">
                {/* User Section */}
                <Box p={4} bg="bg.subtle">
                  {currentUser && <UserSection user={currentUser} />}
                </Box>

                {/* Navigation */}
                <Box flex={1} p={4}>
                  <SidebarItems onClose={handleClose} />
                </Box>

                {/* Actions */}
                <Box p={4} borderTop="1px solid" borderColor="border.subtle">
                  <Stack gap={2} align="stretch">
                    <SidebarAction
                      icon={colorMode === "light" ? FiMoon : FiSun}
                      label={colorMode === "light" ? "Dark Mode" : "Light Mode"}
                      onClick={toggleColorMode}
                    />
                    <SidebarAction
                      icon={FiLogOut}
                      label="Sign Out"
                      onClick={logout}
                      variant="ghost"
                    />
                  </Stack>
                </Box>
              </Stack>
            </DrawerBody>
          </DrawerContent>
        </DrawerRoot>
      </Box>

      {/* Desktop Sidebar */}
      <Box
        display={{ base: "none", md: "flex" }}
        position="sticky"
        top={0}
        minW="280px"
        maxW="280px"
        h="100vh"
        bg="bg.panel"
        borderRight="1px solid"
        borderColor="border.subtle"
        flexDirection="column"
        boxShadow="sm"
      >
        <Stack gap={0} align="stretch" h="full">
          {/* Header */}
          <Box p={6} borderBottom="1px solid" borderColor="border.subtle">
            <Text fontWeight="bold" fontSize="xl" color="ui.main">
              KubeStats
            </Text>
          </Box>

          {/* User Section */}
          {currentUser && (
            <Box p={4} bg="bg.subtle">
              <UserSection user={currentUser} />
            </Box>
          )}

          {/* Navigation */}
          <Box flex={1} p={4}>
            <SidebarItems />
          </Box>

          {/* Desktop Actions */}
          <Box p={4} borderTop="1px solid" borderColor="border.subtle">
            <Stack gap={2} align="stretch">
              <SidebarAction
                icon={colorMode === "light" ? FiMoon : FiSun}
                label={colorMode === "light" ? "Dark Mode" : "Light Mode"}
                onClick={toggleColorMode}
              />
              <SidebarAction
                icon={FiLogOut}
                label="Sign Out"
                onClick={logout}
                variant="ghost"
              />
            </Stack>
          </Box>
        </Stack>
      </Box>
    </>
  )
}

export default Sidebar

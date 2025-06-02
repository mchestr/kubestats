import { Box, Button, Flex, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { FiLogOut, FiSettings } from "react-icons/fi"

import { useColorModeValue } from "@/components/ui/color-mode"
import useAuth from "@/hooks/useAuth"
import { MenuContent, MenuItem, MenuRoot, MenuTrigger } from "../ui/menu"

const UserMenu = () => {
  const { user, logout } = useAuth()
  const menuBgColor = useColorModeValue("white", "gray.800")
  const menuBorderColor = useColorModeValue("gray.200", "gray.700")
  const avatarBgColor = useColorModeValue("teal.500", "teal.400")

  const handleLogout = async () => {
    logout()
  }

  // Get initials from full name or use first letter of email
  const getInitials = () => {
    if (user?.full_name) {
      const nameParts = user.full_name.split(" ")
      if (nameParts.length >= 2) {
        return `${nameParts[0][0]}${nameParts[nameParts.length - 1][0]}`.toUpperCase()
      }
      return user.full_name[0].toUpperCase()
    }
    return user?.email?.[0].toUpperCase() || "U"
  }

  return (
    <Flex>
      <MenuRoot>
        <MenuTrigger asChild>
          <Button
            size="sm"
            bg={avatarBgColor}
            color="white"
            cursor="pointer"
            data-testid="user-menu"
            _hover={{ opacity: 0.9 }}
            fontSize="sm"
            borderRadius="full"
            minW="36px"
            height="36px"
            p={0}
          >
            {getInitials()}
          </Button>
        </MenuTrigger>

        <MenuContent
          bg={menuBgColor}
          borderColor={menuBorderColor}
          minW="200px"
        >
          <Box
            px={4}
            py={2}
            borderBottom="1px solid"
            borderColor={menuBorderColor}
          >
            <Text fontWeight="medium">{user?.full_name || "User"}</Text>
            <Text
              fontSize="xs"
              color="gray.500"
              overflow="hidden"
              textOverflow="ellipsis"
              whiteSpace="nowrap"
            >
              {user?.email || ""}
            </Text>
          </Box>

          <Link to="settings">
            <MenuItem
              closeOnSelect
              value="user-settings"
              gap={2}
              py={2}
              style={{ cursor: "pointer" }}
            >
              <FiSettings fontSize="16px" />
              <Box flex="1">Settings</Box>
            </MenuItem>
          </Link>

          <MenuItem
            value="logout"
            gap={2}
            py={2}
            onClick={handleLogout}
            style={{ cursor: "pointer" }}
          >
            <FiLogOut fontSize="16px" />
            <Box flex="1">Log Out</Box>
          </MenuItem>
        </MenuContent>
      </MenuRoot>
    </Flex>
  )
}

export default UserMenu

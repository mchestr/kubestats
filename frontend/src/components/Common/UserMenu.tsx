import { Box, Button, Flex, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { FiLogOut, FiSettings } from "react-icons/fi"

import { useColorModeValue } from "@/components/ui/color-mode"
import useAuth from "@/hooks/useAuth"
import { MenuContent, MenuItem, MenuRoot, MenuTrigger } from "../ui/menu"

const UserMenu = () => {
  const { user, logout } = useAuth()
  const menuBg = useColorModeValue("white", "gray.800")
  const menuBorderColor = useColorModeValue("gray.200", "gray.700")
  const avatarBg = useColorModeValue("teal.500", "teal.400")
  const textSecondary = useColorModeValue("gray.600", "gray.400")
  const shadowColor = useColorModeValue(
    "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    "0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.2)",
  )

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
    <MenuRoot>
      <MenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          cursor="pointer"
          data-testid="user-menu"
          p={1}
          borderRadius="full"
          transition="all 0.2s"
          _hover={{
            bg: "bg.subtle",
            transform: "scale(1.05)",
          }}
          _active={{ transform: "scale(0.95)" }}
        >
          <Flex
            align="center"
            justify="center"
            w="32px"
            h="32px"
            bg={avatarBg}
            color="white"
            fontWeight="medium"
            fontSize="sm"
            borderRadius="full"
          >
            {getInitials()}
          </Flex>
        </Button>
      </MenuTrigger>

      <MenuContent
        bg={menuBg}
        borderColor={menuBorderColor}
        borderWidth="1px"
        borderRadius="lg"
        boxShadow={shadowColor}
        minW="220px"
        p={1}
      >
        {/* User Info Header */}
        <Box
          px={3}
          py={3}
          mb={1}
          borderBottom="1px solid"
          borderColor={menuBorderColor}
        >
          <Flex align="center" gap={3}>
            <Flex
              align="center"
              justify="center"
              w="28px"
              h="28px"
              bg={avatarBg}
              color="white"
              fontWeight="medium"
              fontSize="xs"
              borderRadius="full"
            >
              {getInitials()}
            </Flex>
            <Box flex="1" minW={0}>
              <Text
                fontWeight="semibold"
                fontSize="sm"
                lineHeight="short"
                textOverflow="ellipsis"
                overflow="hidden"
                whiteSpace="nowrap"
              >
                {user?.full_name || "User"}
              </Text>
              <Text
                fontSize="xs"
                color={textSecondary}
                lineHeight="short"
                textOverflow="ellipsis"
                overflow="hidden"
                whiteSpace="nowrap"
              >
                {user?.email || ""}
              </Text>
            </Box>
          </Flex>
        </Box>

        {/* Menu Items */}
        <Box p={1}>
          <Link to="/settings">
            <MenuItem
              closeOnSelect
              value="user-settings"
              borderRadius="md"
              py={2.5}
              px={3}
              transition="all 0.2s"
              _hover={{ bg: "bg.subtle" }}
              cursor="pointer"
            >
              <Flex align="center" gap={3}>
                <Box color={textSecondary}>
                  <FiSettings size={16} />
                </Box>
                <Text fontWeight="medium" fontSize="sm">
                  Settings
                </Text>
              </Flex>
            </MenuItem>
          </Link>

          <MenuItem
            value="logout"
            borderRadius="md"
            py={2.5}
            px={3}
            transition="all 0.2s"
            _hover={{
              bg: "red.50",
              _dark: { bg: "red.900/20" },
            }}
            onClick={handleLogout}
            cursor="pointer"
          >
            <Flex align="center" gap={3}>
              <Box color="red.500">
                <FiLogOut size={16} />
              </Box>
              <Text fontWeight="medium" fontSize="sm" color="red.500">
                Log Out
              </Text>
            </Flex>
          </MenuItem>
        </Box>
      </MenuContent>
    </MenuRoot>
  )
}

export default UserMenu

import { Box, Flex, IconButton } from "@chakra-ui/react"
import { FiMoon, FiSun } from "react-icons/fi"

import { useColorMode, useColorModeValue } from "../ui/color-mode"
import UserMenu from "./UserMenu"

function Navbar() {
  const { colorMode, toggleColorMode } = useColorMode()
  const navBg = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.700")
  const shadowColor = useColorModeValue(
    "0 1px 3px 0 rgb(0 0 0 / 0.1)",
    "0 1px 3px 0 rgb(0 0 0 / 0.2)",
  )

  return (
    <Box
      as="nav"
      position="sticky"
      top={0}
      zIndex={10}
      bg={navBg}
      borderBottomWidth="1px"
      borderBottomColor={borderColor}
      boxShadow={shadowColor}
      backdropFilter="blur(8px)"
    >
      <Flex
        align="center"
        justify="flex-end"
        maxW="100%"
        mx="auto"
        px={{ base: 4, md: 6 }}
        py={3}
        minH="64px"
      >
        {/* Right Side Actions */}
        <Flex align="center" gap={2}>
          {/* Theme Toggle */}
          <IconButton
            variant="ghost"
            size="sm"
            aria-label={`Switch to ${colorMode === "light" ? "dark" : "light"} mode`}
            onClick={toggleColorMode}
            transition="all 0.2s"
            _hover={{
              bg: "bg.subtle",
              transform: "scale(1.05)",
            }}
          >
            {colorMode === "light" ? <FiMoon size={18} /> : <FiSun size={18} />}
          </IconButton>

          {/* User Menu */}
          <UserMenu />
        </Flex>
      </Flex>
    </Box>
  )
}

export default Navbar

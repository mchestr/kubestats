import { Flex, Heading, useBreakpointValue } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"

import { ColorModeButton, useColorModeValue } from "../ui/color-mode"
import UserMenu from "./UserMenu"

function Navbar() {
  const display = useBreakpointValue({ base: "none", md: "flex" })
  const logoColor = useColorModeValue("teal.600", "teal.300")

  return (
    <Flex
      display={display}
      justify="space-between"
      position="sticky"
      align="center"
      bg="bg.muted"
      w="100%"
      top={0}
      p={4}
    >
      <Link to="/">
        <Heading
          as="h1"
          size="xl"
          fontWeight="bold"
          color={logoColor}
          letterSpacing="tight"
          _hover={{ opacity: 0.9 }}
          cursor="pointer"
          py={1}
        >
          KubeStats
        </Heading>
      </Link>
      <Flex gap={4} alignItems="center">
        <ColorModeButton />
        <UserMenu />
      </Flex>
    </Flex>
  )
}

export default Navbar

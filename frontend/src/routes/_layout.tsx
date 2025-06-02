import { Flex } from "@chakra-ui/react"
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

import Breadcrumb from "@/components/Common/Breadcrumb"
import Navbar from "@/components/Common/Navbar"
import Sidebar from "@/components/Common/Sidebar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  return (
    <Flex h="100vh" overflow="hidden">
      <Sidebar />
      <Flex flex="1" direction="column" overflow="hidden">
        <Navbar />
        <Flex
          flex="1"
          direction="column"
          p={{ base: 4, md: 6 }}
          overflowY="auto"
          bg="bg.default"
        >
          <Breadcrumb />
          <Outlet />
        </Flex>
      </Flex>
    </Flex>
  )
}

export default Layout

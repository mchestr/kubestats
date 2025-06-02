import { Container, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import DatabaseStats from "@/components/Admin/DatabaseStats"

export const Route = createFileRoute("/_layout/")({
  component: Admin,
})

function Admin() {
  return (
    <Container maxW="full">
      <VStack gap={8} align="start" py={8}>
        <DatabaseStats />
      </VStack>
    </Container>
  )
}

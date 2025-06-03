import { Container, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import { EcosystemDashboard } from "@/components/Ecosystem"

export const Route = createFileRoute("/_layout/ecosystem")({
  component: Ecosystem,
})

function Ecosystem() {
  return (
    <Container maxW="full">
      <VStack gap={8} align="start" py={8}>
        <EcosystemDashboard />
      </VStack>
    </Container>
  )
}

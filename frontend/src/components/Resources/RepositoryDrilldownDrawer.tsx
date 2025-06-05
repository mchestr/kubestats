import { Box, Flex, Heading, List, Text } from "@chakra-ui/react"
import type React from "react"
import { useColorModeValue } from "../ui/color-mode"
import {
  DrawerBackdrop,
  DrawerBody,
  DrawerCloseTrigger,
  DrawerContent,
  DrawerHeader,
  DrawerRoot,
} from "../ui/drawer"

interface RepositoryDrilldownDrawerProps {
  open: boolean
  onClose: () => void
  group: any | null
}

export const RepositoryDrilldownDrawer: React.FC<
  RepositoryDrilldownDrawerProps
> = ({ open, onClose, group }) => {
  const bg = useColorModeValue("white", "gray.800")
  if (!open || !group) return null

  return (
    <DrawerRoot
      placement="end"
      open={open}
      onOpenChange={(e) => {
        if (!e.open) onClose()
      }}
    >
      <DrawerBackdrop />
      <DrawerContent bg={bg} maxW="md">
        <DrawerHeader
          p={4}
          borderBottom="1px solid"
          borderColor="border.subtle"
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          bg="bg.panel"
        >
          <Heading size="md">
            {group.kind} / {group.name}
          </Heading>
          <DrawerCloseTrigger />
        </DrawerHeader>
        <DrawerBody>
          <Box mb={4}>
            <Heading as="h3" size="sm" mb={2}>
              Repositories
            </Heading>
            <List.Root>
              {group.repositories.map((repo: any) => (
                <List.Item key={repo.repository_id}>
                  <Flex align="center" justify="space-between">
                    <Text fontWeight="medium">{repo.repository_name}</Text>
                    <Text color="gray.500">{repo.count}</Text>
                  </Flex>
                </List.Item>
              ))}
            </List.Root>
          </Box>
        </DrawerBody>
      </DrawerContent>
    </DrawerRoot>
  )
}

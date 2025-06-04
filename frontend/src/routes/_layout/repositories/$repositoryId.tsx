import { createFileRoute } from "@tanstack/react-router"

import RepositoryDetail from "@/components/Repositories/RepositoryDetail"

export const Route = createFileRoute("/_layout/repositories/$repositoryId")({
  component: RepositoryDetail,
})

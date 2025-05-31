import { createFileRoute } from "@tanstack/react-router"

import RepositoryDetail from "@/components/Repositories/RepositoryDetail"

export const Route = createFileRoute("/_layout/repositories/$repositoryId")({
  beforeLoad: async ({ params }) => {
    console.log("Loading repository detail for:", params.repositoryId)
  },
  component: RepositoryDetail,
})

import { createFileRoute } from "@tanstack/react-router"

import Repositories from "@/components/Repositories/Repositories"

export const Route = createFileRoute("/_layout/repositories/")({
  component: Repositories,
})

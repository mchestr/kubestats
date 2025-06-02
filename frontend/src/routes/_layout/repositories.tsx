import { Outlet, createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/repositories")({
  component: RepositoriesLayout,
})

function RepositoriesLayout() {
  return <Outlet />
}

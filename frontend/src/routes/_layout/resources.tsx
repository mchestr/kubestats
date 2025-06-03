import { createFileRoute } from "@tanstack/react-router"
import { ResourceDashboard } from "../../components/Resources/ResourceDashboard"

export const Route = createFileRoute("/_layout/resources")({
  component: ResourceDashboard,
})

export default function ResourcesRoute() {
  return <ResourceDashboard />
}

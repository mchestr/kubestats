import { TasksPage } from "@/components/Tasks/TasksPage"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/tasks")({
  component: TasksPage,
})

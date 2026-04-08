import { api, ScrapeTask } from "@/lib/api"
import { TasksClient } from "./tasks-client"

export default async function TasksPage() {
  let tasks: ScrapeTask[] = []
  
  try {
    tasks = await api.tasks.list()
  } catch (e) {
    console.error("Failed to load tasks:", e)
  }

  return <TasksClient initialTasks={tasks} />
}

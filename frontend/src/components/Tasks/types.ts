export interface SystemHealth {
  redis_status: string
  active_workers: number
  running_tasks: number
  queue_depth: number
  failed_tasks_24h: number
}

export interface TaskData {
  id: string
  name: string
  time_start?: number
}

export interface WorkerData {
  worker_name: string
  worker_id: string
  status: string
  pool?: {
    max_concurrency?: number
  }
  total?: Record<string, number>
}

export interface PeriodicTaskData {
  name: string
  task: string
  schedule: string
  enabled: boolean
  total_run_count?: number
}

export interface WorkerStatus {
  active?: Record<string, TaskData[]>
  stats?: Record<string, any>
  periodic_tasks?: PeriodicTaskData[]
}

export interface TaskDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  selectedTaskId: string | null
  taskStatus: any
  statusLoading: boolean
  getStatusColor: (status: string) => string
  renderTaskResult: (result: unknown) => string
}

export interface WorkerStatsModalProps {
  isOpen: boolean
  onClose: () => void
  selectedWorkerData: WorkerData | null
}

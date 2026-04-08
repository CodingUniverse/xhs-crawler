"use client"

import { useState, useEffect } from "react"
import { api, ScrapeTask } from "@/lib/api"
import { X, Plus, Play, Pause, Loader2, Trash2 } from "lucide-react"

interface TasksClientProps {
  initialTasks: ScrapeTask[]
}

export function TasksClient({ initialTasks }: TasksClientProps) {
  const [tasks, setTasks] = useState(initialTasks)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [executingTaskId, setExecutingTaskId] = useState<number | null>(null)

  const refreshTasks = async () => {
    try {
      const data = await api.tasks.list()
      setTasks(data)
    } catch (e) {
      console.error("Failed to refresh tasks:", e)
    }
  }

  const handleToggle = async (taskId: number) => {
    try {
      await api.tasks.toggle(taskId)
      refreshTasks()
    } catch (e) {
      console.error("Failed to toggle task:", e)
    }
  }

  const handleExecute = async (taskId: number) => {
    setExecutingTaskId(taskId)
    try {
      await api.tasks.execute(taskId)
      refreshTasks()
    } catch (e) {
      console.error("Failed to execute task:", e)
    } finally {
      setExecutingTaskId(null)
    }
  }

  const handleDelete = async (taskId: number) => {
    if (!confirm("Are you sure you want to delete this task?")) return
    try {
      await api.tasks.delete(taskId)
      refreshTasks()
    } catch (e) {
      console.error("Failed to delete task:", e)
    }
  }

  const platformLabels: Record<string, string> = {
    xiaohongshu: "小红书",
    zhihu: "知乎",
    wechat: "公众号",
    douyin: "抖音",
  }

  const taskTypeLabels: Record<string, string> = {
    keyword: "Keyword",
    author: "Author",
  }

  const statusColors: Record<string, string> = {
    running: "text-[#16a34a]",
    paused: "text-[#d97706]",
    stopped: "text-[#dc2626]",
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-[#1a1a1a] tracking-tight mb-1">Scrape Tasks</h1>
          <p className="text-[#737373] text-sm">Create and manage scraping jobs</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-[#2563eb] text-white rounded-lg hover:bg-[#1d4ed8] transition-all duration-200 flex items-center gap-2 text-sm font-medium shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Create Task
        </button>
      </div>

      {tasks.length === 0 ? (
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-12 text-center shadow-sm">
          <p className="text-[#737373] mb-4">No tasks yet</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="text-[#2563eb] hover:underline text-sm font-medium"
          >
            Create your first task
          </button>
        </div>
      ) : (
        <div className="bg-white border border-[#e5e5e5] rounded-lg overflow-hidden shadow-sm">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#e5e5e5] bg-[#fafafa]">
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Platform</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Type</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Target</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Frequency</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Status</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Last Run</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id} className="border-b border-[#e5e5e5] last:border-0 hover:bg-[#fafafa]">
                  <td className="p-4 text-[#1a1a1a] text-sm">{platformLabels[task.platform]}</td>
                  <td className="p-4 text-[#1a1a1a] text-sm">{taskTypeLabels[task.task_type]}</td>
                  <td className="p-4 font-mono text-sm max-w-xs truncate text-[#1a1a1a]">{task.target_value}</td>
                  <td className="p-4 font-mono text-sm text-[#525252]">{task.frequency}</td>
                  <td className="p-4">
                    <span className={statusColors[task.status]}>{task.status}</span>
                  </td>
                  <td className="p-4 text-[#737373] text-sm">
                    <span suppressHydrationWarning>
                      {task.last_run_time 
                        ? new Date(task.last_run_time).toLocaleString() 
                        : "Never"}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleToggle(task.id)}
                        className="p-2 hover:bg-[#f5f5f5] rounded transition-all duration-200"
                        title={task.status === "running" ? "Pause" : "Run"}
                      >
                        {task.status === "running" ? (
                          <Pause className="w-4 h-4 text-[#525252]" />
                        ) : (
                          <Play className="w-4 h-4 text-[#525252]" />
                        )}
                      </button>
                      <button
                        onClick={() => handleExecute(task.id)}
                        disabled={executingTaskId === task.id}
                        className="p-2 hover:bg-[#f5f5f5] rounded transition-all duration-200 disabled:opacity-50"
                        title="Execute now"
                      >
                        {executingTaskId === task.id ? (
                          <Loader2 className="w-4 h-4 animate-spin text-[#2563eb]" />
                        ) : (
                          <Play className="w-4 h-4 text-[#2563eb]" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(task.id)}
                        className="p-2 hover:bg-[#f5f5f5] rounded transition-all duration-200 text-[#dc2626]"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreateModal && (
        <CreateTaskModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false)
            refreshTasks()
          }}
        />
      )}
    </div>
  )
}

interface CreateTaskModalProps {
  onClose: () => void
  onSuccess: () => void
}

function CreateTaskModal({ onClose, onSuccess }: CreateTaskModalProps) {
  const [platform, setPlatform] = useState<string>("xiaohongshu")
  const [taskType, setTaskType] = useState<string>("author")
  const [targetValue, setTargetValue] = useState("")
  const [frequency, setFrequency] = useState("0 */6 * * *")
  const [depth, setDepth] = useState(2)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      await api.tasks.create({
        task_type: taskType as "keyword" | "author",
        target_value: targetValue,
        platform: platform as "xiaohongshu" | "zhihu" | "wechat" | "douyin",
        frequency,
        depth,
        retry_times: 3,
        status: "paused",
      })
      onSuccess()
    } catch (e: any) {
      setError(e.message || "Failed to create task")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      
      <div className="relative bg-white border border-[#e5e5e5] rounded-lg w-[500px] p-6 shadow-xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-[#f5f5f5] rounded transition-all duration-200"
        >
          <X className="w-5 h-5 text-[#737373]" />
        </button>

        <h2 className="text-lg font-semibold text-[#1a1a1a] mb-5">Create New Task</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#525252] mb-2">Platform</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-[#e5e5e5] rounded-lg text-[#1a1a1a] text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
              required
            >
              <option value="xiaohongshu">小红书</option>
              <option value="zhihu">知乎</option>
              <option value="wechat">公众号</option>
              <option value="douyin">抖音</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#525252] mb-2">Task Type</label>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-[#e5e5e5] rounded-lg text-[#1a1a1a] text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
              required
            >
              <option value="author">Author (Author ID/URL)</option>
              <option value="keyword">Keyword Search</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#525252] mb-2">
              {taskType === "author" ? "Author ID / Homepage URL" : "Keyword"}
            </label>
            <input
              type="text"
              value={targetValue}
              onChange={(e) => setTargetValue(e.target.value)}
              placeholder={taskType === "author" ? "e.g., user123 or https://www.xiaohongshu.com/user/profile/xxx" : "e.g., 美食推荐"}
              className="w-full px-3 py-2 bg-white border border-[#e5e5e5] rounded-lg text-[#1a1a1a] text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#525252] mb-2">Frequency (Cron)</label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-[#e5e5e5] rounded-lg text-[#1a1a1a] text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
            >
              <option value="0 */6 * * *">Every 6 hours</option>
              <option value="0 */12 * * *">Every 12 hours</option>
              <option value="0 0 * * *">Daily at midnight</option>
              <option value="0 */1 * * *">Every hour</option>
              <option value="*/30 * * * *">Every 30 minutes</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#525252] mb-2">Depth (pages)</label>
            <input
              type="number"
              value={depth}
              onChange={(e) => setDepth(parseInt(e.target.value))}
              min={1}
              max={20}
              className="w-full px-3 py-2 bg-white border border-[#e5e5e5] rounded-lg text-[#1a1a1a] text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
            />
          </div>

          {error && (
            <p className="text-[#dc2626] text-sm">{error}</p>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-[#e5e5e5] rounded-lg hover:bg-[#f5f5f5] transition-all duration-200 text-sm font-medium text-[#525252]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-[#2563eb] text-white rounded-lg hover:bg-[#1d4ed8] transition-all duration-200 disabled:opacity-50 flex items-center gap-2 text-sm font-medium"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
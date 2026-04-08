const API_URL = process.env.NEXT_PUBLIC_API_URL || ""

export interface PlatformAccount {
  id: number
  platform_name: "xiaohongshu" | "zhihu" | "wechat" | "douyin"
  account_name: string
  cookie_data: string
  status: "active" | "expired" | "pending"
  created_at: string
  updated_at: string
}

export interface ScrapeTask {
  id: number
  task_type: "keyword" | "author"
  target_value: string
  platform: "xiaohongshu" | "zhihu" | "wechat" | "douyin"
  frequency: string
  depth: number
  retry_times: number
  status: "running" | "paused" | "stopped"
  last_run_time: string | null
  created_at: string
  updated_at: string
}

export interface ContentAsset {
  id: number
  platform_post_id: string
  platform: "xiaohongshu" | "zhihu" | "wechat" | "douyin"
  source_url: string | null
  title: string | null
  content_text: string | null
  author_name: string | null
  author_id: string | null
  publish_date: string | null
  media_urls: { images: string[]; video: string | null } | null
  metrics: { likes: number; comments: number; shares: number; views: number } | null
  is_starred: boolean
  is_archived: boolean
  is_deleted: boolean
  manual_outline: string | null
  ai_analysis: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ContentListResponse {
  items: ContentAsset[]
  total: number
  page: number
  page_size: number
}

export interface QRCodeResponse {
  qr_code: string
  session_id: string
  status: string
}

export interface LoginStatusResponse {
  session_id: string
  status: "pending" | "success" | "expired" | "timeout" | "error"
  account_id?: number
  message?: string
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }))
    throw new Error(error.detail || "Request failed")
  }
  
  if (response.status === 204) {
    return undefined as T
  }
  
  return response.json()
}

export const api = {
  accounts: {
    list: (platform?: string, status?: string) =>
      fetchAPI<PlatformAccount[]>(
        `/accounts${[platform && `platform=${platform}`, status && `status=${status}`].filter(Boolean).join("&") ? "?" + [platform && `platform=${platform}`, status && `status=${status}`].filter(Boolean).join("&") : ""}`
      ),
    get: (id: number) => fetchAPI<PlatformAccount>(`/accounts/${id}`),
    create: (data: { platform_name: string; account_name: string; cookie_data: string }) =>
      fetchAPI<PlatformAccount>("/accounts", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: number, data: Partial<PlatformAccount>) =>
      fetchAPI<PlatformAccount>(`/accounts/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: number) => fetchAPI<void>(`/accounts/${id}`, { method: "DELETE" }),
  },
  
  tasks: {
    list: (platform?: string, status?: string, taskType?: string) =>
      fetchAPI<ScrapeTask[]>(
        `/tasks${[platform && `platform=${platform}`, status && `status=${status}`, taskType && `task_type=${taskType}`].filter(Boolean).join("&") ? "?" + [platform && `platform=${platform}`, status && `status=${status}`, taskType && `task_type=${taskType}`].filter(Boolean).join("&") : ""}`
      ),
    get: (id: number) => fetchAPI<ScrapeTask>(`/tasks/${id}`),
    create: (data: Omit<ScrapeTask, "id" | "last_run_time" | "created_at" | "updated_at">) =>
      fetchAPI<ScrapeTask>("/tasks", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: number, data: Partial<ScrapeTask>) =>
      fetchAPI<ScrapeTask>(`/tasks/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: number) => fetchAPI<void>(`/tasks/${id}`, { method: "DELETE" }),
    run: (id: number) => fetchAPI<ScrapeTask>(`/tasks/${id}/run`, { method: "POST" }),
    pause: (id: number) => fetchAPI<ScrapeTask>(`/tasks/${id}/pause`, { method: "POST" }),
    toggle: (id: number) => fetchAPI<ScrapeTask>(`/tasks/${id}/toggle`, { method: "POST" }),
    execute: (id: number) => fetchAPI<{task_id: number; inserted: number; updated: number}>(`/tasks/${id}/execute`, { method: "POST" }),
  },
  
  content: {
    list: (params?: { 
      platform?: string; 
      author_name?: string; 
      search?: string;
      is_starred?: boolean;
      is_archived?: boolean;
      is_deleted?: boolean;
      page?: number; 
      page_size?: number; 
      order_by?: string;
      sort_order?: string;
    }) => {
      const query = new URLSearchParams()
      if (params?.platform) query.set("platform", params.platform)
      if (params?.author_name) query.set("author_name", params.author_name)
      if (params?.search) query.set("search", params.search)
      if (params?.is_starred !== undefined) query.set("is_starred", String(params.is_starred))
      if (params?.is_archived !== undefined) query.set("is_archived", String(params.is_archived))
      if (params?.is_deleted !== undefined) query.set("is_deleted", String(params.is_deleted))
      if (params?.page) query.set("page", String(params.page))
      if (params?.page_size) query.set("page_size", String(params.page_size))
      if (params?.order_by) query.set("order_by", params.order_by)
      if (params?.sort_order) query.set("sort_order", params.sort_order)
      return fetchAPI<ContentListResponse>(`/content?${query.toString()}`)
    },
    get: (id: number) => fetchAPI<ContentAsset>(`/content/${id}`),
    update: (id: number, data: Partial<ContentAsset>) =>
      fetchAPI<ContentAsset>(`/content/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    star: (id: number) => fetchAPI<ContentAsset>(`/content/${id}/star`, { method: "POST" }),
    archive: (id: number) => fetchAPI<ContentAsset>(`/content/${id}/archive`, { method: "POST" }),
    saveOutline: (id: number, outline: string) =>
      fetchAPI<ContentAsset>(`/content/${id}/outline`, {
        method: "PATCH",
        body: JSON.stringify({ outline }),
      }),
    aiAnalyze: (id: number) =>
      fetchAPI<{
        status: string
        message: string
        mock_data: Record<string, unknown>
      }>(`/content/${id}/ai-analyze`, { method: "POST" }),
    delete: (id: number, hard: boolean = false) => fetchAPI<void>(`/content/${id}?hard=${hard}`, { method: "DELETE" }),
    batchDelete: (ids: number[], hard: boolean = false) => fetchAPI<void>(`/content/batch-delete?hard=${hard}`, {
      method: "POST",
      body: JSON.stringify(ids),
    }),
    batchRestore: (ids: number[]) => fetchAPI<void>(`/content/batch-restore`, {
      method: "POST",
      body: JSON.stringify(ids),
    }),
  },

  xhs: {
    generateQR: () => fetchAPI<QRCodeResponse>("/accounts/xhs/qr", { method: "POST" }),
    getStatus: (sessionId: string) => fetchAPI<LoginStatusResponse>(`/accounts/xhs/status/${sessionId}`),
  },

  scrape: {
    instant: (url: string) =>
      fetchAPI<{
        success: boolean
        message: string
        platform: string | null
        platform_post_id: string | null
        title: string | null
        author_name: string | null
        metrics: Record<string, unknown> | null
        count: number | null
      }>("/api/scrape/instant", {
        method: "POST",
        body: JSON.stringify({ url }),
      }),
  },
}

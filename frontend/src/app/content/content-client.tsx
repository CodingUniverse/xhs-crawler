"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { api, ContentAsset } from "@/lib/api"
import { 
  Search, Filter, Grid3X3, List, 
  Heart, MessageCircle, Share2, Eye,
  Star, Archive, ChevronUp, ChevronDown,
  X, Loader2, ExternalLink, Save, Sparkles,
  ChevronLeft, ChevronRight, Zap, AlertCircle, CheckCircle,
  Trash2, RotateCcw, CheckSquare, Square
} from "lucide-react"

interface ContentClientProps {
  initialContent: { items: ContentAsset[]; total: number; page: number; page_size: number }
}

type ViewMode = "card" | "table"

export function ContentClient({ initialContent }: ContentClientProps) {
  const [content, setContent] = useState(initialContent)
  const [viewMode, setViewMode] = useState<ViewMode>("card")
  const [loading, setLoading] = useState(false)
  const [showDeleted, setShowDeleted] = useState(false)
  const [selectedItems, setSelectedItems] = useState<number[]>([])
  const [filters, setFilters] = useState({
    platform: "",
    search: "",
    order_by: "publish_date",
    sort_order: "desc",
  })
  const [selectedItem, setSelectedItem] = useState<ContentAsset | null>(null)
  
  const [quickScrapeUrl, setQuickScrapeUrl] = useState("")
  const [scrapeLoading, setScrapeLoading] = useState(false)
  const [scrapeError, setScrapeError] = useState<string | null>(null)
  const [scrapeSuccess, setScrapeSuccess] = useState<string | null>(null)

  const fetchContent = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.content.list({
        platform: filters.platform || undefined,
        search: filters.search || undefined,
        order_by: filters.order_by,
        sort_order: filters.sort_order,
        is_deleted: showDeleted,
        page: content.page,
        page_size: content.page_size,
      })
      setContent(data)
      setSelectedItems([])
    } catch (e) {
      console.error("Failed to fetch content:", e)
    } finally {
      setLoading(false)
    }
  }, [filters, content.page, content.page_size, showDeleted])

  useEffect(() => {
    fetchContent()
  }, [fetchContent])

  const handleSort = (field: string) => {
    if (filters.order_by === field) {
      setFilters(f => ({ ...f, sort_order: f.sort_order === "desc" ? "asc" : "desc" }))
    } else {
      setFilters(f => ({ ...f, order_by: field, sort_order: "desc" }))
    }
  }

  const handleStar = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.content.star(id)
      fetchContent()
    } catch (e) {
      console.error("Failed to star:", e)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm(showDeleted ? "Permanently delete this item?" : "Delete this item?")) return
    try {
      await api.content.delete(id, showDeleted)
      fetchContent()
    } catch (e) {
      console.error("Failed to delete:", e)
    }
  }

  const handleBatchDelete = async () => {
    if (!confirm(`Delete ${selectedItems.length} items?`)) return
    try {
      await api.content.batchDelete(selectedItems, showDeleted)
      fetchContent()
    } catch (e) {
      console.error("Failed to batch delete:", e)
    }
  }

  const handleBatchRestore = async () => {
    if (!confirm(`Restore ${selectedItems.length} items?`)) return
    try {
      await api.content.batchRestore(selectedItems)
      fetchContent()
    } catch (e) {
      console.error("Failed to batch restore:", e)
    }
  }

  const toggleSelectAll = () => {
    if (selectedItems.length === content.items.length) {
      setSelectedItems([])
    } else {
      setSelectedItems(content.items.map(item => item.id))
    }
  }

  const toggleSelect = (id: number) => {
    if (selectedItems.includes(id)) {
      setSelectedItems(selectedItems.filter(i => i !== id))
    } else {
      setSelectedItems([...selectedItems, id])
    }
  }

  const handleItemUpdate = (updatedItem: ContentAsset) => {
    setContent(c => ({
      ...c,
      items: c.items.map(item => item.id === updatedItem.id ? updatedItem : item)
    }))
    setSelectedItem(updatedItem)
  }

  const handleQuickScrape = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!quickScrapeUrl.trim()) return
    
    setScrapeLoading(true)
    setScrapeError(null)
    setScrapeSuccess(null)
    
    try {
      const result = await api.scrape.instant(quickScrapeUrl)
      setScrapeSuccess(result.message)
      setQuickScrapeUrl("")
      fetchContent()
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : "Failed to scrape URL"
      setScrapeError(errMsg)
    } finally {
      setScrapeLoading(false)
    }
  }

  const platformLabels: Record<string, string> = {
    xiaohongshu: "小红书",
    zhihu: "知乎",
    wechat: "公众号",
    douyin: "抖音",
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-[#1a1a1a] tracking-tight mb-1">Content Assets</h1>
          <p className="text-[#737373] text-sm">View and manage collected content</p>
        </div>
        
        <div className="flex items-center gap-2 bg-[#f5f5f5] p-1 rounded-lg">
          <button
            onClick={() => setViewMode("card")}
            className={`px-3 py-1.5 rounded-md flex items-center gap-2 text-sm transition-all duration-200 ${
              viewMode === "card" ? "bg-white shadow-sm text-[#1a1a1a]" : "text-[#737373] hover:text-[#1a1a1a]"
            }`}
          >
            <Grid3X3 className="w-4 h-4" />
            Card
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`px-3 py-1.5 rounded-md flex items-center gap-2 text-sm transition-all duration-200 ${
              viewMode === "table" ? "bg-white shadow-sm text-[#1a1a1a]" : "text-[#737373] hover:text-[#1a1a1a]"
            }`}
          >
            <List className="w-4 h-4" />
            Table
          </button>
        </div>
      </div>

      <div className="mb-6 p-4 bg-white rounded-lg border border-[#e5e5e5] shadow-sm">
        <form onSubmit={handleQuickScrape} className="flex gap-2">
          <div className="relative flex-1">
            <Zap className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#2563eb]" />
            <input
              type="text"
              placeholder="Paste Xiaohongshu or Zhihu post/author URL..."
              value={quickScrapeUrl}
              onChange={(e) => setQuickScrapeUrl(e.target.value)}
              disabled={scrapeLoading}
              className="w-full pl-10 pr-4 py-2 bg-white border border-[#e5e5e5] rounded-lg disabled:opacity-50 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            disabled={scrapeLoading || !quickScrapeUrl.trim()}
            className="px-4 py-2 bg-[#2563eb] text-white rounded-lg flex items-center gap-2 hover:bg-[#1d4ed8] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 text-sm font-medium shadow-sm"
          >
            {scrapeLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Scraping...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>解析</span>
              </>
            )}
          </button>
        </form>
        
        {scrapeError && (
          <div className="mt-2 flex items-center gap-2 text-[#dc2626] text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>{scrapeError}</span>
          </div>
        )}
        
        {scrapeSuccess && (
          <div className="mt-2 flex items-center gap-2 text-[#16a34a] text-sm">
            <CheckCircle className="w-4 h-4" />
            <span>{scrapeSuccess}</span>
          </div>
        )}
        
        <p className="mt-2 text-xs text-[#737373]">
          Supports: 小红书/知乎 post URLs and author profile URLs
        </p>
      </div>

      <div className="flex gap-4 mb-6 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#737373]" />
          <input
            type="text"
            placeholder="Search title or content..."
            value={filters.search}
            onChange={(e) => setFilters(f => ({ ...f, search: e.target.value }))}
            className="w-full pl-10 pr-4 py-2 bg-white border border-[#e5e5e5] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
          />
        </div>

        <select
          value={filters.platform}
          onChange={(e) => setFilters(f => ({ ...f, platform: e.target.value }))}
          className="px-3 py-2 bg-white border border-[#e5e5e5] rounded-lg text-sm text-[#1a1a1a] focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
        >
          <option value="">All Platforms</option>
          <option value="xiaohongshu">小红书</option>
          <option value="zhihu">知乎</option>
          <option value="wechat">公众号</option>
          <option value="douyin">抖音</option>
        </select>

        <select
          value={`${filters.order_by}-${filters.sort_order}`}
          onChange={(e) => {
            const [order_by, sort_order] = e.target.value.split("-")
            setFilters(f => ({ ...f, order_by, sort_order }))
          }}
          className="px-3 py-2 bg-white border border-[#e5e5e5] rounded-lg text-sm text-[#1a1a1a] focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
        >
          <option value="publish_date-desc">Latest</option>
          <option value="likes-desc">Most Likes</option>
          <option value="comments-desc">Most Comments</option>
          <option value="shares-desc">Most Shares</option>
          <option value="views-desc">Most Views</option>
        </select>

        <button
          onClick={() => setShowDeleted(!showDeleted)}
          className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            showDeleted 
              ? "bg-[#fef3c7] text-[#d97706] border border-[#fcd34d]" 
              : "bg-white border border-[#e5e5e5] text-[#737373] hover:text-[#1a1a1a]"
          }`}
        >
          {showDeleted ? "🗑️ Recycle Bin" : "🗑️ Deleted"}
        </button>
      </div>

      {selectedItems.length > 0 && (
        <div className="mb-4 flex items-center justify-between bg-[#f0f9ff] border border-[#bae6fd] rounded-lg p-3">
          <span className="text-sm text-[#0369a1]">
            {selectedItems.length} item(s) selected
          </span>
          <div className="flex gap-2">
            {showDeleted ? (
              <>
                <button
                  onClick={handleBatchRestore}
                  className="px-3 py-1.5 bg-[#16a34a] text-white rounded-lg text-sm font-medium hover:bg-[#15803d] transition-all duration-200 flex items-center gap-1"
                >
                  <RotateCcw className="w-4 h-4" />
                  Restore
                </button>
                <button
                  onClick={handleBatchDelete}
                  className="px-3 py-1.5 bg-[#dc2626] text-white rounded-lg text-sm font-medium hover:bg-[#b91c1c] transition-all duration-200 flex items-center gap-1"
                >
                  <Trash2 className="w-4 h-4" />
                  Permanently Delete
                </button>
              </>
            ) : (
              <button
                onClick={handleBatchDelete}
                className="px-3 py-1.5 bg-[#dc2626] text-white rounded-lg text-sm font-medium hover:bg-[#b91c1c] transition-all duration-200 flex items-center gap-1"
              >
                <Trash2 className="w-4 h-4" />
                Delete Selected
              </button>
            )}
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-[#737373]" />
        </div>
      ) : content.items.length === 0 ? (
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-12 text-center shadow-sm">
          <p className="text-[#737373]">No content yet. Create tasks to start collecting.</p>
        </div>
      ) : viewMode === "card" ? (
        <CardView 
          items={content.items} 
          onStar={handleStar} 
          onSelect={setSelectedItem}
          onDelete={handleDelete}
          selectedItems={selectedItems}
          onToggleSelect={toggleSelect}
          platformLabels={platformLabels}
        />
      ) : (
        <TableView 
          items={content.items} 
          onStar={handleStar} 
          onSelect={setSelectedItem}
          onDelete={handleDelete}
          onSort={handleSort}
          sortConfig={{ field: filters.order_by, order: filters.sort_order }}
          selectedItems={selectedItems}
          onToggleSelect={toggleSelect}
          onToggleSelectAll={toggleSelectAll}
          platformLabels={platformLabels}
        />
      )}

      <div className="flex justify-center gap-2 mt-6">
        {content.page > 1 && (
          <button
            onClick={() => setContent(c => ({ ...c, page: c.page - 1 }))}
            className="px-4 py-2 bg-white border border-[#e5e5e5] rounded-lg text-sm hover:bg-[#f5f5f5] transition-all duration-200"
          >
            Previous
          </button>
        )}
        <span className="px-4 py-2 text-[#737373] text-sm">
          Page {content.page} of {Math.ceil(content.total / content.page_size)}
        </span>
        {content.page * content.page_size < content.total && (
          <button
            onClick={() => setContent(c => ({ ...c, page: c.page + 1 }))}
            className="px-4 py-2 bg-white border border-[#e5e5e5] rounded-lg text-sm hover:bg-[#f5f5f5] transition-all duration-200"
          >
            Next
          </button>
        )}
      </div>

      {selectedItem && (
        <WorkspaceModal 
          item={selectedItem} 
          onClose={() => setSelectedItem(null)}
          onUpdate={handleItemUpdate}
          platformLabels={platformLabels}
        />
      )}
    </div>
  )
}

function CardView({ 
  items, 
  onStar, 
  onSelect,
  onDelete,
  selectedItems,
  onToggleSelect,
  platformLabels 
}: { 
  items: ContentAsset[]
  onStar: (id: number, e: React.MouseEvent) => void
  onSelect: (item: ContentAsset) => void
  onDelete: (id: number) => void
  selectedItems: number[]
  onToggleSelect: (id: number) => void
  platformLabels: Record<string, string>
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {items.map((item) => {
        const validImages = (item.media_urls?.images || []).filter((img): img is string => typeof img === 'string' && img.startsWith('http'))
        const isSelected = selectedItems.includes(item.id)
        return (
        <div
          key={item.id}
          className={`bg-white border rounded-lg overflow-hidden hover:shadow-md transition-all duration-200 cursor-pointer ${
            isSelected ? "border-[#2563eb] ring-2 ring-[#2563eb]/30" : "border-[#e5e5e5]"
          }`}
        >
          <div className="absolute top-2 left-2 z-10">
            <button
              onClick={(e) => { e.stopPropagation(); onToggleSelect(item.id); }}
              className="p-1 bg-white rounded border border-[#e5e5e5] hover:border-[#2563eb] transition-all duration-200"
            >
              {isSelected ? <CheckSquare className="w-4 h-4 text-[#2563eb]" /> : <Square className="w-4 h-4 text-[#737373]" />}
            </button>
          </div>
          <div className="aspect-square bg-[#f5f5f5] relative" onClick={() => onSelect(item)}>
            {validImages[0] ? (
              <img 
                src={validImages[0]} 
                alt={item.title || ""}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-[#737373]">
                {item.media_urls?.video ? "Video" : "No Media"}
              </div>
            )}
            <button
              onClick={(e) => onStar(item.id, e)}
              className="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full hover:bg-white transition-all duration-200 shadow-sm"
            >
              <Star className={`w-4 h-4 ${item.is_starred ? "fill-[#facc15] text-[#facc15]" : "text-[#737373]"}`} />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(item.id); }}
              className="absolute bottom-2 right-2 p-1.5 bg-white/90 rounded-full hover:bg-white transition-all duration-200 shadow-sm text-[#dc2626]"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          
          <div className="p-3">
            <h3 className="font-medium text-sm line-clamp-2 mb-1 text-[#1a1a1a]">
              {item.title || item.content_text?.slice(0, 50) || "Untitled"}
            </h3>
            <p className="text-xs text-[#737373] mb-2">
              {item.author_name || "Unknown"} · {platformLabels[item.platform]}
            </p>
            
            <div className="flex items-center gap-3 text-xs text-[#737373]">
              <span className="flex items-center gap-1">
                <Heart className="w-3 h-3" /> {item.metrics?.likes || 0}
              </span>
              <span className="flex items-center gap-1">
                <MessageCircle className="w-3 h-3" /> {item.metrics?.comments || 0}
              </span>
              <span className="flex items-center gap-1">
                <Share2 className="w-3 h-3" /> {item.metrics?.shares || 0}
              </span>
            </div>
          </div>
        </div>
      )})}
    </div>
  )
}

function TableView({ 
  items, 
  onStar, 
  onSelect,
  onDelete,
  onSort,
  sortConfig,
  selectedItems,
  onToggleSelect,
  onToggleSelectAll,
  platformLabels 
}: { 
  items: ContentAsset[]
  onStar: (id: number, e: React.MouseEvent) => void
  onSelect: (item: ContentAsset) => void
  onDelete: (id: number) => void
  onSort: (field: string) => void
  sortConfig: { field: string; order: string }
  selectedItems: number[]
  onToggleSelect: (id: number) => void
  onToggleSelectAll: () => void
  platformLabels: Record<string, string>
}) {
  const SortIcon = ({ field }: { field: string }) => {
    if (sortConfig.field !== field) return null
    return sortConfig.order === "desc" ? 
      <ChevronDown className="w-4 h-4" /> : 
      <ChevronUp className="w-4 h-4" />
  }

  return (
    <div className="bg-white border border-[#e5e5e5] rounded-lg overflow-hidden shadow-sm">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[#e5e5e5] bg-[#fafafa]">
            <th className="text-left p-4 font-medium text-[#525252] text-sm w-10">
              <button onClick={onToggleSelectAll}>
                {selectedItems.length === items.length && items.length > 0 ? (
                  <CheckSquare className="w-4 h-4 text-[#2563eb]" />
                ) : (
                  <Square className="w-4 h-4 text-[#737373]" />
                )}
              </button>
            </th>
            <th className="text-left p-4 font-medium text-[#525252] text-sm w-20">Cover</th>
            <th className="text-left p-4 font-medium text-[#525252] text-sm">Title</th>
            <th className="text-left p-4 font-medium text-[#525252] text-sm">Author</th>
            <th className="text-left p-4 font-medium text-[#525252] text-sm">Platform</th>
            <th className="text-left p-4 font-medium text-[#525252] text-sm cursor-pointer hover:text-[#2563eb]" onClick={() => onSort("publish_date")}>
              <span className="flex items-center gap-1">Date <SortIcon field="publish_date" /></span>
            </th>
            <th className="text-left p-4 font-medium text-[#525252] text-sm cursor-pointer hover:text-[#2563eb]" onClick={() => onSort("likes")}>
              <span className="flex items-center gap-1">Likes <SortIcon field="likes" /></span>
            </th>
            <th className="text-left p-4 font-medium text-[#525252] text-sm cursor-pointer hover:text-[#2563eb]" onClick={() => onSort("comments")}>
              <span className="flex items-center gap-1">Comments <SortIcon field="comments" /></span>
            </th>
            <th className="text-left p-4 font-medium text-[#525252] text-sm w-24">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const validImages = (item.media_urls?.images || []).filter((img): img is string => typeof img === 'string' && img.startsWith('http'))
            const isSelected = selectedItems.includes(item.id)
            return (
            <tr key={item.id} className={`border-b border-[#e5e5e5] last:border-0 hover:bg-[#fafafa] ${isSelected ? "bg-[#f0f9ff]" : ""}`}>
              <td className="p-4">
                <button onClick={() => onToggleSelect(item.id)}>
                  {isSelected ? (
                    <CheckSquare className="w-4 h-4 text-[#2563eb]" />
                  ) : (
                    <Square className="w-4 h-4 text-[#737373]" />
                  )}
                </button>
              </td>
              <td className="p-4">
                <div className="w-12 h-12 bg-[#f5f5f5] rounded overflow-hidden">
                  {validImages[0] ? (
                    <img 
                      src={validImages[0]} 
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : null}
                </div>
              </td>
              <td className="p-4 max-w-xs truncate text-[#1a1a1a] text-sm">{item.title || item.content_text?.slice(0, 30) || "-"}</td>
              <td className="p-4 text-[#1a1a1a] text-sm">{item.author_name || "-"}</td>
              <td className="p-4">
                <span className="px-2 py-1 bg-[#eff6ff] text-[#2563eb] rounded text-xs font-medium">
                  {platformLabels[item.platform]}
                </span>
              </td>
              <td className="p-4 text-sm text-[#737373]">
                <span suppressHydrationWarning>
                  {item.publish_date 
                    ? new Date(item.publish_date).toLocaleDateString() 
                    : "-"}
                </span>
              </td>
              <td className="p-4 text-[#1a1a1a] text-sm">{item.metrics?.likes || 0}</td>
              <td className="p-4 text-[#1a1a1a] text-sm">{item.metrics?.comments || 0}</td>
              <td className="p-4">
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => onStar(item.id, e)}
                    className="p-1.5 hover:bg-[#f5f5f5] rounded transition-all duration-200"
                  >
                    <Star className={`w-4 h-4 ${item.is_starred ? "fill-[#facc15] text-[#facc15]" : "text-[#737373]"}`} />
                  </button>
                  <button
                    onClick={() => onSelect(item)}
                    className="p-1.5 hover:bg-[#f5f5f5] rounded transition-all duration-200"
                  >
                    <ExternalLink className="w-4 h-4 text-[#737373]" />
                  </button>
                  <button
                    onClick={() => onDelete(item.id)}
                    className="p-1.5 hover:bg-[#f5f5f5] rounded transition-all duration-200 text-[#dc2626]"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          )})}
        </tbody>
      </table>
    </div>
  )
}

function WorkspaceModal({ 
  item, 
  onClose,
  onUpdate,
  platformLabels 
}: { 
  item: ContentAsset
  onClose: () => void
  onUpdate: (item: ContentAsset) => void
  platformLabels: Record<string, string>
}) {
  const [outline, setOutline] = useState(item.manual_outline || "")
  const [aiResult, setAiResult] = useState<Record<string, unknown> | null>(item.ai_analysis || null)
  const [saving, setSaving] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const saveTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)

  const rawImages = item.media_urls?.images || []
  const images = rawImages.filter((img): img is string => typeof img === 'string' && img.startsWith('http'))

  const handleOutlineChange = (value: string) => {
    setOutline(value)
    
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    
    saveTimeoutRef.current = setTimeout(async () => {
      setSaving(true)
      try {
        const updated = await api.content.saveOutline(item.id, value)
        onUpdate(updated)
      } catch (e) {
        console.error("Failed to save outline:", e)
      } finally {
        setSaving(false)
      }
    }, 1000)
  }

  const handleAiAnalyze = async () => {
    setAnalyzing(true)
    try {
      const result = await api.content.aiAnalyze(item.id)
      setAiResult(result.mock_data)
    } catch (e) {
      console.error("Failed to analyze:", e)
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative bg-white border border-[#e5e5e5] rounded-lg w-[1400px] h-[90vh] flex flex-col shadow-xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-[#f5f5f5] rounded z-10 transition-all duration-200"
        >
          <X className="w-5 h-5 text-[#737373]" />
        </button>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-1/2 border-r border-[#e5e5e5] overflow-y-auto">
            <div className="sticky top-0 bg-white z-10 p-4 border-b border-[#e5e5e5]">
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-[#eff6ff] text-[#2563eb] rounded text-xs font-medium">
                  {platformLabels[item.platform]}
                </span>
                <h2 className="text-lg font-semibold text-[#1a1a1a]">{item.title || "Untitled"}</h2>
              </div>
              <p className="text-sm text-[#737373] mt-1">
                <span suppressHydrationWarning>
                  By {item.author_name} · {item.publish_date ? new Date(item.publish_date).toLocaleDateString() : "Unknown date"}
                </span>
                {item.source_url && (
                  <a 
                    href={item.source_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="ml-2 flex items-center gap-1 text-[#2563eb] hover:underline"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Original
                  </a>
                )}
              </p>
            </div>

            {images.length > 0 && (
              <div className="relative">
                <div className="aspect-video bg-[#1a1a1a] flex items-center justify-center">
                  {images[currentImageIndex] ? (
                    <img 
                      src={images[currentImageIndex]} 
                      alt={item.title || ""}
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <span className="text-[#737373]">No Image</span>
                  )}
                </div>
                {images.length > 1 && (
                  <>
                    <button
                      onClick={() => setCurrentImageIndex(i => Math.max(0, i - 1))}
                      className="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-white/90 rounded-full shadow-sm hover:bg-white transition-all duration-200"
                      disabled={currentImageIndex === 0}
                    >
                      <ChevronLeft className="w-5 h-5 text-[#1a1a1a]" />
                    </button>
                    <button
                      onClick={() => setCurrentImageIndex(i => Math.min(images.length - 1, i + 1))}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-white/90 rounded-full shadow-sm hover:bg-white transition-all duration-200"
                      disabled={currentImageIndex === images.length - 1}
                    >
                      <ChevronRight className="w-5 h-5 text-[#1a1a1a]" />
                    </button>
                    <div className="flex justify-center gap-2 p-2">
                      {images.map((_, idx) => (
                        <button
                          key={idx}
                          onClick={() => setCurrentImageIndex(idx)}
                          className={`w-2 h-2 rounded-full ${idx === currentImageIndex ? "bg-[#2563eb]" : "bg-[#d4d4d4]"}`}
                        />
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            <div className="p-4">
              <div className="flex items-center gap-6 mb-4 text-sm border-b border-[#e5e5e5] pb-4">
                <span className="flex items-center gap-2 text-[#525252]">
                  <Heart className="w-4 h-4" /> {item.metrics?.likes || 0} likes
                </span>
                <span className="flex items-center gap-2 text-[#525252]">
                  <MessageCircle className="w-4 h-4" /> {item.metrics?.comments || 0} comments
                </span>
                <span className="flex items-center gap-2 text-[#525252]">
                  <Share2 className="w-4 h-4" /> {item.metrics?.shares || 0} shares
                </span>
                <span className="flex items-center gap-2 text-[#525252]">
                  <Eye className="w-4 h-4" /> {item.metrics?.views || 0} views
                </span>
              </div>

              <h3 className="font-medium text-[#1a1a1a] mb-2">Content</h3>
              <p className="text-[#525252] whitespace-pre-wrap text-sm leading-relaxed">
                {item.content_text || "No content text available."}
              </p>
            </div>
          </div>

          <div className="w-1/2 flex flex-col">
            <div className="p-4 border-b border-[#e5e5e5] flex items-center justify-between">
              <h3 className="font-semibold text-[#1a1a1a]">Workspace</h3>
              <button
                onClick={handleAiAnalyze}
                disabled={analyzing}
                className="px-3 py-1.5 bg-gradient-to-r from-[#8b5cf6] to-[#ec4899] text-white rounded-lg flex items-center gap-2 text-sm hover:opacity-90 transition-opacity disabled:opacity-50 font-medium"
              >
                {analyzing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                AI 一键拆解 (Beta)
              </button>
            </div>

            {aiResult && (
              <div className="p-4 border-b border-[#e5e5e5] bg-[#faf5ff]">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-[#8b5cf6]" />
                  <span className="font-medium text-sm text-[#1a1a1a]">AI Analysis (Mock)</span>
                </div>
                <div className="space-y-2 text-sm">
                  <p className="text-[#525252]"><strong>Hook:</strong> {(aiResult as { hook: string }).hook}</p>
                  <div>
                    <strong className="text-[#1a1a1a]">Structure:</strong>
                    <ul className="ml-4 mt-1 text-[#737373]">
                      {((aiResult as { body_structure: Array<{ section: string }> }).body_structure || []).map((s, i) => (
                        <li key={i}>{s.section}</li>
                      ))}
                    </ul>
                  </div>
                  <p className="text-[#525252]"><strong>Hot Phrases:</strong> {((aiResult as { hot_phrases: string[] }).hot_phrases || []).join(", ")}</p>
                  <p className="text-[#525252]"><strong>CTA:</strong> {(aiResult as { call_to_action: string }).call_to_action}</p>
                </div>
              </div>
            )}

            <div className="flex-1 p-4 flex flex-col">
              <div className="flex items-center justify-between mb-2">
                <label className="font-medium text-[#1a1a1a]">Manual Outline / Notes</label>
                {saving && <span className="text-xs text-[#737373] flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Saving...</span>}
              </div>
              <textarea
                value={outline}
                onChange={(e) => handleOutlineChange(e.target.value)}
                placeholder="Write your outline, notes, or rewrite ideas here..."
                className="flex-1 w-full p-4 bg-[#fafafa] border border-[#e5e5e5] rounded-lg resize-none font-mono text-sm text-[#1a1a1a] focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent"
              />
              <button
                onClick={async () => {
                  setSaving(true)
                  try {
                    const updated = await api.content.saveOutline(item.id, outline)
                    onUpdate(updated)
                  } catch (e) {
                    console.error("Failed to save:", e)
                  } finally {
                    setSaving(false)
                  }
                }}
                disabled={saving}
                className="mt-2 px-4 py-2 bg-[#2563eb] text-white rounded-lg flex items-center justify-center gap-2 hover:bg-[#1d4ed8] disabled:opacity-50 transition-all duration-200 text-sm font-medium"
              >
                <Save className="w-4 h-4" />
                Save Notes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
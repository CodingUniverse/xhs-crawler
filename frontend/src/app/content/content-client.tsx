"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { api, ContentAsset } from "@/lib/api"
import { 
  Search, Filter, Grid3X3, List, 
  Heart, MessageCircle, Share2, Eye,
  Star, Archive, ChevronUp, ChevronDown,
  X, Loader2, ExternalLink, Save, Sparkles,
  ChevronLeft, ChevronRight, Zap, AlertCircle, CheckCircle
} from "lucide-react"

interface ContentClientProps {
  initialContent: { items: ContentAsset[]; total: number; page: number; page_size: number }
}

type ViewMode = "card" | "table"

export function ContentClient({ initialContent }: ContentClientProps) {
  const [content, setContent] = useState(initialContent)
  const [viewMode, setViewMode] = useState<ViewMode>("card")
  const [loading, setLoading] = useState(false)
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
        page: content.page,
        page_size: content.page_size,
      })
      setContent(data)
    } catch (e) {
      console.error("Failed to fetch content:", e)
    } finally {
      setLoading(false)
    }
  }, [filters, content.page, content.page_size])

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
          <h1 className="text-3xl font-bold mb-2">Content Assets</h1>
          <p className="text-muted-foreground">View and manage collected content</p>
        </div>
        
        <div className="flex items-center gap-2 bg-sidebar-border p-1 rounded-lg">
          <button
            onClick={() => setViewMode("card")}
            className={`px-3 py-1.5 rounded-md flex items-center gap-2 text-sm ${
              viewMode === "card" ? "bg-card-bg shadow-sm" : "text-muted-foreground"
            }`}
          >
            <Grid3X3 className="w-4 h-4" />
            Card
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`px-3 py-1.5 rounded-md flex items-center gap-2 text-sm ${
              viewMode === "table" ? "bg-card-bg shadow-sm" : "text-muted-foreground"
            }`}
          >
            <List className="w-4 h-4" />
            Table
          </button>
        </div>
      </div>

      <div className="mb-6 p-4 bg-gradient-to-r from-primary/10 to-primary/5 rounded-lg border border-primary/20">
        <form onSubmit={handleQuickScrape} className="flex gap-2">
          <div className="relative flex-1">
            <Zap className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary" />
            <input
              type="text"
              placeholder="Paste Xiaohongshu or Zhihu post/author URL..."
              value={quickScrapeUrl}
              onChange={(e) => setQuickScrapeUrl(e.target.value)}
              disabled={scrapeLoading}
              className="w-full pl-10 pr-4 py-2 bg-card-bg border border-card-border rounded-lg disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={scrapeLoading || !quickScrapeUrl.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg flex items-center gap-2 hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
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
          <div className="mt-2 flex items-center gap-2 text-red-500 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>{scrapeError}</span>
          </div>
        )}
        
        {scrapeSuccess && (
          <div className="mt-2 flex items-center gap-2 text-green-500 text-sm">
            <CheckCircle className="w-4 h-4" />
            <span>{scrapeSuccess}</span>
          </div>
        )}
        
        <p className="mt-2 text-xs text-muted-foreground">
          Supports: 小红书/知乎 post URLs and author profile URLs
        </p>
      </div>

      <div className="flex gap-4 mb-6 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search title or content..."
            value={filters.search}
            onChange={(e) => setFilters(f => ({ ...f, search: e.target.value }))}
            className="w-full pl-10 pr-4 py-2 bg-card-bg border border-card-border rounded-lg"
          />
        </div>

        <select
          value={filters.platform}
          onChange={(e) => setFilters(f => ({ ...f, platform: e.target.value }))}
          className="px-3 py-2 bg-card-bg border border-card-border rounded-lg"
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
          className="px-3 py-2 bg-card-bg border border-card-border rounded-lg"
        >
          <option value="publish_date-desc">Latest</option>
          <option value="likes-desc">Most Likes</option>
          <option value="comments-desc">Most Comments</option>
          <option value="shares-desc">Most Shares</option>
          <option value="views-desc">Most Views</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : content.items.length === 0 ? (
        <div className="bg-card-bg border border-card-border rounded-lg p-12 text-center">
          <p className="text-muted-foreground">No content yet. Create tasks to start collecting.</p>
        </div>
      ) : viewMode === "card" ? (
        <CardView 
          items={content.items} 
          onStar={handleStar} 
          onSelect={setSelectedItem}
          platformLabels={platformLabels}
        />
      ) : (
        <TableView 
          items={content.items} 
          onStar={handleStar} 
          onSelect={setSelectedItem}
          onSort={handleSort}
          sortConfig={{ field: filters.order_by, order: filters.sort_order }}
          platformLabels={platformLabels}
        />
      )}

      <div className="flex justify-center gap-2 mt-6">
        {content.page > 1 && (
          <button
            onClick={() => setContent(c => ({ ...c, page: c.page - 1 }))}
            className="px-4 py-2 bg-card-bg border border-card-border rounded-lg"
          >
            Previous
          </button>
        )}
        <span className="px-4 py-2 text-muted-foreground">
          Page {content.page} of {Math.ceil(content.total / content.page_size)}
        </span>
        {content.page * content.page_size < content.total && (
          <button
            onClick={() => setContent(c => ({ ...c, page: c.page + 1 }))}
            className="px-4 py-2 bg-card-bg border border-card-border rounded-lg"
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
  platformLabels 
}: { 
  items: ContentAsset[]
  onStar: (id: number, e: React.MouseEvent) => void
  onSelect: (item: ContentAsset) => void
  platformLabels: Record<string, string>
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {items.map((item) => {
        const validImages = (item.media_urls?.images || []).filter((img): img is string => typeof img === 'string' && img.startsWith('http'))
        return (
        <div
          key={item.id}
          onClick={() => onSelect(item)}
          className="bg-card-bg border border-card-border rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="aspect-square bg-sidebar-border relative">
            {validImages[0] ? (
              <img 
                src={validImages[0]} 
                alt={item.title || ""}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                {item.media_urls?.video ? "Video" : "No Media"}
              </div>
            )}
            <button
              onClick={(e) => onStar(item.id, e)}
              className="absolute top-2 right-2 p-1.5 bg-black/50 rounded-full hover:bg-black/70 transition-colors"
            >
              <Star className={`w-4 h-4 ${item.is_starred ? "fill-yellow-400 text-yellow-400" : "text-white"}`} />
            </button>
          </div>
          
          <div className="p-3">
            <h3 className="font-medium text-sm line-clamp-2 mb-1">
              {item.title || item.content_text?.slice(0, 50) || "Untitled"}
            </h3>
            <p className="text-xs text-muted-foreground mb-2">
              {item.author_name || "Unknown"} · {platformLabels[item.platform]}
            </p>
            
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
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
  onSort,
  sortConfig,
  platformLabels 
}: { 
  items: ContentAsset[]
  onStar: (id: number, e: React.MouseEvent) => void
  onSelect: (item: ContentAsset) => void
  onSort: (field: string) => void
  sortConfig: { field: string; order: string }
  platformLabels: Record<string, string>
}) {
  const SortIcon = ({ field }: { field: string }) => {
    if (sortConfig.field !== field) return null
    return sortConfig.order === "desc" ? 
      <ChevronDown className="w-4 h-4" /> : 
      <ChevronUp className="w-4 h-4" />
  }

  return (
    <div className="bg-card-bg border border-card-border rounded-lg overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-card-border">
            <th className="text-left p-4 font-medium w-20">Cover</th>
            <th className="text-left p-4 font-medium">Title</th>
            <th className="text-left p-4 font-medium">Author</th>
            <th className="text-left p-4 font-medium">Platform</th>
            <th className="text-left p-4 font-medium cursor-pointer hover:text-primary" onClick={() => onSort("publish_date")}>
              <span className="flex items-center gap-1">Date <SortIcon field="publish_date" /></span>
            </th>
            <th className="text-left p-4 font-medium cursor-pointer hover:text-primary" onClick={() => onSort("likes")}>
              <span className="flex items-center gap-1">Likes <SortIcon field="likes" /></span>
            </th>
            <th className="text-left p-4 font-medium cursor-pointer hover:text-primary" onClick={() => onSort("comments")}>
              <span className="flex items-center gap-1">Comments <SortIcon field="comments" /></span>
            </th>
            <th className="text-left p-4 font-medium w-20">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const validImages = (item.media_urls?.images || []).filter((img): img is string => typeof img === 'string' && img.startsWith('http'))
            return (
            <tr key={item.id} className="border-b border-card-border last:border-0 hover:bg-sidebar-border/50">
              <td className="p-4">
                <div className="w-12 h-12 bg-sidebar-border rounded overflow-hidden">
                  {validImages[0] ? (
                    <img 
                      src={validImages[0]} 
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : null}
                </div>
              </td>
              <td className="p-4 max-w-xs truncate">{item.title || item.content_text?.slice(0, 30) || "-"}</td>
              <td className="p-4">{item.author_name || "-"}</td>
              <td className="p-4">
                <span className="px-2 py-1 bg-primary/10 text-primary rounded text-xs">
                  {platformLabels[item.platform]}
                </span>
              </td>
              <td className="p-4 text-sm text-muted-foreground">
                <span suppressHydrationWarning>
                  {item.publish_date 
                    ? new Date(item.publish_date).toLocaleDateString() 
                    : "-"}
                </span>
              </td>
              <td className="p-4">{item.metrics?.likes || 0}</td>
              <td className="p-4">{item.metrics?.comments || 0}</td>
              <td className="p-4">
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => onStar(item.id, e)}
                    className="p-1.5 hover:bg-sidebar-border rounded"
                  >
                    <Star className={`w-4 h-4 ${item.is_starred ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground"}`} />
                  </button>
                  <button
                    onClick={() => onSelect(item)}
                    className="p-1.5 hover:bg-sidebar-border rounded"
                  >
                    <ExternalLink className="w-4 h-4 text-muted-foreground" />
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
  const [imageError, setImageError] = useState(false)
  const saveTimeoutRef = useRef<NodeJS.Timeout>()

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
      <div className="relative bg-card-bg border border-card-border rounded-lg w-[1400px] h-[90vh] flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-sidebar-border rounded z-10"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-1/2 border-r border-card-border overflow-y-auto">
            <div className="sticky top-0 bg-card-bg z-10 p-4 border-b border-card-border">
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-primary/10 text-primary rounded text-xs">
                  {platformLabels[item.platform]}
                </span>
                <h2 className="text-lg font-bold">{item.title || "Untitled"}</h2>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                <span suppressHydrationWarning>
                  By {item.author_name} · {item.publish_date ? new Date(item.publish_date).toLocaleDateString() : "Unknown date"}
                </span>
              </p>
            </div>

            {images.length > 0 && (
              <div className="relative">
                <div className="aspect-video bg-black flex items-center justify-center">
                  {images[currentImageIndex] ? (
                    <img 
                      src={images[currentImageIndex]} 
                      alt={item.title || ""}
                      className="w-full h-full object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none'
                      }}
                    />
                  ) : (
                    <span className="text-muted-foreground">No Image</span>
                  )}
                </div>
                {images.length > 1 && (
                  <>
                    <button
                      onClick={() => setCurrentImageIndex(i => Math.max(0, i - 1))}
                      className="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-black/50 rounded-full"
                      disabled={currentImageIndex === 0}
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => setCurrentImageIndex(i => Math.min(images.length - 1, i + 1))}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-black/50 rounded-full"
                      disabled={currentImageIndex === images.length - 1}
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                    <div className="flex justify-center gap-2 p-2">
                      {images.map((_, idx) => (
                        <button
                          key={idx}
                          onClick={() => setCurrentImageIndex(idx)}
                          className={`w-2 h-2 rounded-full ${idx === currentImageIndex ? "bg-primary" : "bg-muted-foreground"}`}
                        />
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            <div className="p-4">
              <div className="flex items-center gap-6 mb-4 text-sm border-b border-card-border pb-4">
                <span className="flex items-center gap-2">
                  <Heart className="w-4 h-4" /> {item.metrics?.likes || 0} likes
                </span>
                <span className="flex items-center gap-2">
                  <MessageCircle className="w-4 h-4" /> {item.metrics?.comments || 0} comments
                </span>
                <span className="flex items-center gap-2">
                  <Share2 className="w-4 h-4" /> {item.metrics?.shares || 0} shares
                </span>
                <span className="flex items-center gap-2">
                  <Eye className="w-4 h-4" /> {item.metrics?.views || 0} views
                </span>
              </div>

              <h3 className="font-medium mb-2">Content</h3>
              <p className="text-muted-foreground whitespace-pre-wrap">
                {item.content_text || "No content text available."}
              </p>
            </div>
          </div>

          <div className="w-1/2 flex flex-col">
            <div className="p-4 border-b border-card-border flex items-center justify-between">
              <h3 className="font-bold">Workspace</h3>
              <button
                onClick={handleAiAnalyze}
                disabled={analyzing}
                className="px-3 py-1.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg flex items-center gap-2 text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
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
              <div className="p-4 border-b border-card-border bg-purple-500/10">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-purple-500" />
                  <span className="font-medium text-sm">AI Analysis (Mock)</span>
                </div>
                <div className="space-y-2 text-sm">
                  <p><strong>Hook:</strong> {(aiResult as { hook: string }).hook}</p>
                  <div>
                    <strong>Structure:</strong>
                    <ul className="ml-4 mt-1 text-muted-foreground">
                      {((aiResult as { body_structure: Array<{ section: string }> }).body_structure || []).map((s, i) => (
                        <li key={i}>{s.section}</li>
                      ))}
                    </ul>
                  </div>
                  <p><strong>Hot Phrases:</strong> {((aiResult as { hot_phrases: string[] }).hot_phrases || []).join(", ")}</p>
                  <p><strong>CTA:</strong> {(aiResult as { call_to_action: string }).call_to_action}</p>
                </div>
              </div>
            )}

            <div className="flex-1 p-4 flex flex-col">
              <div className="flex items-center justify-between mb-2">
                <label className="font-medium">Manual Outline / Notes</label>
                {saving && <span className="text-xs text-muted-foreground flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Saving...</span>}
              </div>
              <textarea
                value={outline}
                onChange={(e) => handleOutlineChange(e.target.value)}
                placeholder="Write your outline, notes, or rewrite ideas here..."
                className="flex-1 w-full p-4 bg-sidebar-border rounded-lg resize-none font-mono text-sm"
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
                className="mt-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg flex items-center justify-center gap-2 hover:bg-primary/90 disabled:opacity-50"
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

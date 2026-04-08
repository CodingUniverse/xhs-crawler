import { api, ContentAsset } from "@/lib/api"
import { ContentClient } from "./content-client"

export default async function ContentPage({
  searchParams,
}: {
  searchParams: Promise<{ 
    platform?: string; 
    author?: string; 
    page?: string; 
    order_by?: string;
    sort_order?: string;
  }>
}) {
  const params = await searchParams
  
  let content = { items: [] as ContentAsset[], total: 0, page: 1, page_size: 20 }
  
  try {
    content = await api.content.list({
      platform: params.platform,
      page: params.page ? parseInt(params.page) : 1,
      order_by: params.order_by || "publish_date",
      sort_order: params.sort_order || "desc",
    })
  } catch (e) {
    console.error("Failed to load content:", e)
  }

  return <ContentClient initialContent={content} />
}

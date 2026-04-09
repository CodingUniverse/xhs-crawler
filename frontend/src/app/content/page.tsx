import { ContentClient } from "./content-client"

export default function ContentPage() {
  return <ContentClient initialContent={{ items: [], total: 0, page: 1, page_size: 20 }} />
}

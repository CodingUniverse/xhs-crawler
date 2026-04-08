import type { Metadata } from "next"
import "./globals.css"
import { Sidebar } from "@/components/sidebar"

export const metadata: Metadata = {
  title: "XHS Crawler - Social Media Analytics",
  description: "Social media content crawler and analytics system",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-white">
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 overflow-auto bg-white lg:pl-0 pl-16">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
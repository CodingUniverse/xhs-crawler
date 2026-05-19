import type { Metadata } from "next"
import "./globals.css"
import { Sidebar } from "@/components/sidebar"

export const metadata: Metadata = {
  title: "XHS Crawler - 小红书内容采集系统",
  description: "社交媒体内容采集与分析平台",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-white">
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 overflow-auto bg-white lg:ml-0 ml-16">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}

"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Users,
  Clock,
  FileText,
  Settings,
} from "lucide-react"

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/accounts", label: "Account Pool", icon: Users },
  { href: "/tasks", label: "Tasks", icon: Clock },
  { href: "/content", label: "Content Assets", icon: FileText },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 h-screen bg-[#fafafa] border-r border-[#e5e5e5] flex flex-col">
      <div className="p-6 border-b border-[#e5e5e5]">
        <h1 className="text-xl font-semibold text-[#1a1a1a] tracking-tight">XHS Crawler</h1>
        <p className="text-sm text-[#737373] mt-0.5">Social Media Analytics</p>
      </div>
      
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== "/" && pathname.startsWith(item.href))
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-[#2563eb] text-white shadow-sm"
                  : "text-[#525252] hover:bg-[#f5f5f5] hover:text-[#1a1a1a]"
              )}
            >
              <item.icon className="w-4.5 h-4.5" />
              {item.label}
            </Link>
          )
        })}
      </nav>
      
      <div className="p-4 border-t border-[#e5e5e5]">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-[#525252] hover:bg-[#f5f5f5] hover:text-[#1a1a1a] transition-all duration-200"
        >
          <Settings className="w-4.5 h-4.5" />
          Settings
        </Link>
      </div>
    </aside>
  )
}
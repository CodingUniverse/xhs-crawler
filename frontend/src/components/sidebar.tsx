"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Users,
  Clock,
  FileText,
  Settings,
  Menu,
  X,
} from "lucide-react"

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/accounts", label: "Account Pool", icon: Users },
  { href: "/tasks", label: "Tasks", icon: Clock },
  { href: "/content", label: "Content Assets", icon: FileText },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white border border-[#e5e5e5] rounded-lg shadow-sm"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-40 w-64 h-screen bg-[#fafafa] border-r border-[#e5e5e5] flex flex-col transition-transform duration-300 lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="p-6 border-b border-[#e5e5e5]">
          <h1 className="text-xl font-semibold text-[#1a1a1a] tracking-tight">XHS Crawler</h1>
          <p className="text-sm text-[#737373] mt-0.5">Social Media Analytics</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== "/" && pathname.startsWith(item.href))
            
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
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
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-[#525252] hover:bg-[#f5f5f5] hover:text-[#1a1a1a] transition-all duration-200"
          >
            <Settings className="w-4.5 h-4.5" />
            Settings
          </Link>
        </div>
      </aside>
    </>
  )
}
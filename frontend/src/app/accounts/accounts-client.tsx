"use client"

import { useState } from "react"
import { api, PlatformAccount } from "@/lib/api"
import { XHSLoginModal } from "@/components/xhs-login-modal"
import { Plus, QrCode, AlertCircle } from "lucide-react"

interface AccountsClientProps {
  initialAccounts: PlatformAccount[]
  error?: string | null
}

export function AccountsClient({ initialAccounts, error }: AccountsClientProps) {
  const [accounts, setAccounts] = useState(initialAccounts)
  const [showXHSModal, setShowXHSModal] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(error || null)

  const refreshAccounts = async () => {
    try {
      const data = await api.accounts.list()
      setAccounts(data)
    } catch (e) {
      console.error("Failed to refresh accounts:", e)
    }
  }

  const platformLabels: Record<string, string> = {
    xiaohongshu: "小红书",
    zhihu: "知乎",
    wechat: "公众号",
    douyin: "抖音",
  }

  const statusColors: Record<string, string> = {
    active: "bg-[#16a34a]",
    expired: "bg-[#dc2626]",
    pending: "bg-[#d97706]",
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-[#1a1a1a] tracking-tight mb-1">Account Pool</h1>
          <p className="text-[#737373] text-sm">Manage platform accounts and cookies</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowXHSModal(true)}
            className="px-4 py-2 bg-[#2563eb] text-white rounded-lg hover:bg-[#1d4ed8] transition-all duration-200 flex items-center gap-2 text-sm font-medium shadow-sm"
          >
            <QrCode className="w-4 h-4" />
            Add XHS Account
          </button>
        </div>
      </div>

      {connectionError && (
        <div className="bg-[#fef2f2] border border-[#fecaca] rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-[#dc2626] flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-[#dc2626]">Cannot connect to backend</p>
            <p className="text-sm text-[#737373]">{connectionError}</p>
            <p className="text-sm text-[#737373] mt-1">Make sure the backend is running at http://localhost:8000</p>
          </div>
        </div>
      )}

      {accounts.length === 0 && !connectionError ? (
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-12 text-center shadow-sm">
          <p className="text-[#737373] mb-4">No accounts yet</p>
          <button
            onClick={() => setShowXHSModal(true)}
            className="text-[#2563eb] hover:underline text-sm font-medium"
          >
            Add your first account
          </button>
        </div>
      ) : (
        <div className="bg-white border border-[#e5e5e5] rounded-lg overflow-hidden shadow-sm">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#e5e5e5] bg-[#fafafa]">
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Platform</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Account Name</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Status</th>
                <th className="text-left p-4 font-medium text-[#525252] text-sm">Updated</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.id} className="border-b border-[#e5e5e5] last:border-0 hover:bg-[#fafafa]">
                  <td className="p-4 text-[#1a1a1a] text-sm">{platformLabels[account.platform_name]}</td>
                  <td className="p-4 text-[#1a1a1a] text-sm">{account.account_name}</td>
                  <td className="p-4">
                    <span className={`inline-block w-2 h-2 rounded-full ${statusColors[account.status]} mr-2`} />
                    <span className="text-sm text-[#525252]">{account.status}</span>
                  </td>
                  <td className="p-4 text-[#737373] text-sm">
                    <span suppressHydrationWarning>
                      {new Date(account.updated_at).toLocaleDateString()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <XHSLoginModal
        isOpen={showXHSModal}
        onClose={() => setShowXHSModal(false)}
        onSuccess={() => {
          setShowXHSModal(false)
          refreshAccounts()
        }}
      />
    </div>
  )
}
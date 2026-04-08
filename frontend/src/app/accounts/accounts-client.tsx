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
    active: "bg-success",
    expired: "bg-destructive",
    pending: "bg-warning",
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Account Pool</h1>
          <p className="text-muted-foreground">Manage platform accounts and cookies</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowXHSModal(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2"
          >
            <QrCode className="w-4 h-4" />
            Add XHS Account
          </button>
        </div>
      </div>

      {connectionError && (
        <div className="bg-destructive/10 border border-destructive rounded-lg p-4 mb-6 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <div>
            <p className="font-medium text-destructive">Cannot connect to backend</p>
            <p className="text-sm text-muted-foreground">{connectionError}</p>
            <p className="text-sm text-muted-foreground mt-1">Make sure the backend is running at http://localhost:8000</p>
          </div>
        </div>
      )}

      {accounts.length === 0 && !connectionError ? (
        <div className="bg-card-bg border border-card-border rounded-lg p-12 text-center">
          <p className="text-muted-foreground mb-4">No accounts yet</p>
          <button
            onClick={() => setShowXHSModal(true)}
            className="text-primary hover:underline"
          >
            Add your first account
          </button>
        </div>
      ) : (
        <div className="bg-card-bg border border-card-border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-card-border">
                <th className="text-left p-4 font-medium">Platform</th>
                <th className="text-left p-4 font-medium">Account Name</th>
                <th className="text-left p-4 font-medium">Status</th>
                <th className="text-left p-4 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.id} className="border-b border-card-border last:border-0">
                  <td className="p-4">{platformLabels[account.platform_name]}</td>
                  <td className="p-4">{account.account_name}</td>
                  <td className="p-4">
                    <span className={`inline-block w-2 h-2 rounded-full ${statusColors[account.status]} mr-2`} />
                    {account.status}
                  </td>
                  <td className="p-4 text-muted-foreground">
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

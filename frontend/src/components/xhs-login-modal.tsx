"use client"

import { useState, useEffect, useCallback } from "react"
import { api, QRCodeResponse, LoginStatusResponse } from "@/lib/api"
import { X, QrCode, Loader2, CheckCircle, AlertCircle } from "lucide-react"

interface XHSLoginModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export function XHSLoginModal({ isOpen, onClose, onSuccess }: XHSLoginModalProps) {
  const [qrData, setQrData] = useState<QRCodeResponse | null>(null)
  const [status, setStatus] = useState<LoginStatusResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const checkStatus = useCallback(async (sessionId: string) => {
    try {
      const statusData = await api.xhs.getStatus(sessionId)
      setStatus(statusData)

      if (statusData.status === "success") {
        onSuccess()
        return true
      } else if (statusData.status === "expired" || statusData.status === "timeout" || statusData.status === "error") {
        setError(statusData.message || "Login failed")
        return true
      }
    } catch (e) {
      console.error("Status check failed:", e)
    }
    return false
  }, [onSuccess])

  useEffect(() => {
    if (!isOpen) {
      setQrData(null)
      setStatus(null)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    api.xhs.generateQR()
      .then((data) => {
        setQrData(data)
      })
      .catch((e) => {
        setError(e.message || "Failed to generate QR code")
      })
      .finally(() => {
        setLoading(false)
      })
  }, [isOpen])

  useEffect(() => {
    if (!qrData?.session_id || status?.status === "success" || status?.status === "expired" || status?.status === "timeout" || status?.status === "error") {
      return
    }

    const interval = setInterval(async () => {
      const done = await checkStatus(qrData.session_id)
      if (done) {
        clearInterval(interval)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [qrData?.session_id, status, checkStatus])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      
      <div className="relative bg-white border border-[#e5e5e5] rounded-lg w-[400px] p-6 shadow-xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-[#f5f5f5] rounded transition-all duration-200"
        >
          <X className="w-5 h-5 text-[#737373]" />
        </button>

        <div className="text-center mb-6">
          <h2 className="text-lg font-semibold text-[#1a1a1a]">Add Xiaohongshu Account</h2>
          <p className="text-sm text-[#737373] mt-1">Scan QR code to login</p>
        </div>

        {loading && (
          <div className="flex flex-col items-center py-12">
            <Loader2 className="w-12 h-12 animate-spin text-[#2563eb]" />
            <p className="mt-4 text-[#737373]">Generating QR code...</p>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center py-8">
            <AlertCircle className="w-12 h-12 text-[#dc2626]" />
            <p className="mt-4 text-[#dc2626]">{error}</p>
            <button
              onClick={() => {
                setError(null)
                setQrData(null)
                setLoading(true)
                api.xhs.generateQR()
                  .then(setQrData)
                  .catch((e) => setError(e.message))
                  .finally(() => setLoading(false))
              }}
              className="mt-4 px-4 py-2 bg-[#2563eb] text-white rounded-lg hover:bg-[#1d4ed8] transition-all duration-200 text-sm font-medium"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && qrData && (
          <div className="flex flex-col items-center">
            {status?.status === "success" ? (
              <div className="flex flex-col items-center py-8">
                <CheckCircle className="w-16 h-16 text-[#16a34a]" />
                <p className="mt-4 text-lg font-medium text-[#1a1a1a]">Login Successful!</p>
                <p className="text-sm text-[#737373]">Redirecting...</p>
              </div>
            ) : status?.status === "pending" || !status ? (
              <>
                <div className="bg-white p-4 rounded-lg border border-[#e5e5e5]">
                  <img
                    src={`data:image/png;base64,${qrData.qr_code}`}
                    alt="Login QR Code"
                    className="w-48 h-48"
                  />
                </div>
                <p className="mt-4 text-sm text-[#737373]">
                  Open Xiaohongshu Creator App and scan the QR code
                </p>
                <div className="mt-4 flex items-center gap-2 text-sm text-[#737373]">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Waiting for scan...
                </div>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
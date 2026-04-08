import { api, PlatformAccount } from "@/lib/api"
import { AccountsClient } from "./accounts-client"

export default async function AccountsPage() {
  let accounts: PlatformAccount[] = []
  let error = null
  
  try {
    accounts = await api.accounts.list()
  } catch (e) {
    console.error("Failed to load accounts:", e)
    error = e instanceof Error ? e.message : "Failed to connect to backend"
  }

  return <AccountsClient initialAccounts={accounts} error={error} />
}

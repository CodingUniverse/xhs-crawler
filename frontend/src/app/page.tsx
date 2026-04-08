export default function Home() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
      <p className="text-muted-foreground mb-8">
        Welcome to XHS Crawler - Social Media Analytics Platform
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-card-bg border border-card-border rounded-lg p-6">
          <div className="text-sm text-muted-foreground mb-2">Total Accounts</div>
          <div className="text-3xl font-bold">0</div>
        </div>
        
        <div className="bg-card-bg border border-card-border rounded-lg p-6">
          <div className="text-sm text-muted-foreground mb-2">Active Tasks</div>
          <div className="text-3xl font-bold">0</div>
        </div>
        
        <div className="bg-card-bg border border-card-border rounded-lg p-6">
          <div className="text-sm text-muted-foreground mb-2">Content Assets</div>
          <div className="text-3xl font-bold">0</div>
        </div>
        
        <div className="bg-card-bg border border-card-border rounded-lg p-6">
          <div className="text-sm text-muted-foreground mb-2">System Status</div>
          <div className="text-3xl font-bold text-success">OK</div>
        </div>
      </div>
      
      <div className="mt-8 bg-card-bg border border-card-border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Start</h2>
        <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
          <li>Add accounts in Account Pool (manual or QR scan)</li>
          <li>Create scraping tasks in Tasks</li>
          <li>View collected content in Content Assets</li>
        </ol>
      </div>
    </div>
  )
}

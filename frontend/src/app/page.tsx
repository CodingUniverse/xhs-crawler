export default function Home() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold text-[#1a1a1a] tracking-tight mb-1">Dashboard</h1>
      <p className="text-[#737373] mb-8 text-sm">
        Welcome to XHS Crawler - Social Media Analytics Platform
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-5 shadow-sm">
          <div className="text-sm text-[#737373] mb-1.5">Total Accounts</div>
          <div className="text-2xl font-semibold text-[#1a1a1a]">0</div>
        </div>
        
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-5 shadow-sm">
          <div className="text-sm text-[#737373] mb-1.5">Active Tasks</div>
          <div className="text-2xl font-semibold text-[#1a1a1a]">0</div>
        </div>
        
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-5 shadow-sm">
          <div className="text-sm text-[#737373] mb-1.5">Content Assets</div>
          <div className="text-2xl font-semibold text-[#1a1a1a]">0</div>
        </div>
        
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-5 shadow-sm">
          <div className="text-sm text-[#737373] mb-1.5">System Status</div>
          <div className="text-2xl font-semibold text-[#16a34a]">OK</div>
        </div>
      </div>
      
      <div className="mt-8 bg-white border border-[#e5e5e5] rounded-lg p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-[#1a1a1a] mb-4">Quick Start</h2>
        <ol className="list-decimal list-inside space-y-2 text-[#737373] text-sm">
          <li>Add accounts in Account Pool (manual or QR scan)</li>
          <li>Create scraping tasks in Tasks</li>
          <li>View collected content in Content Assets</li>
        </ol>
      </div>
    </div>
  )
}
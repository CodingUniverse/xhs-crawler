export default function Home() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold text-[#1a1a1a] tracking-tight mb-1">控制台</h1>
      <p className="text-[#737373] mb-8 text-sm">
        欢迎使用小红书内容采集与分析系统
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-5 shadow-sm">
          <div className="text-sm text-[#737373] mb-1.5">账号总数</div>
          <div className="text-2xl font-semibold text-[#1a1a1a]">0</div>
        </div>

        <div className="bg-white border border-[#e5e5e5] rounded-lg p-5 shadow-sm">
          <div className="text-sm text-[#737373] mb-1.5">进行中任务</div>
          <div className="text-2xl font-semibold text-[#1a1a1a]">0</div>
        </div>

        <div className="bg-white border border-[#e5e5e5] rounded-lg p-5 shadow-sm">
          <div className="text-sm text-[#737373] mb-1.5">内容总数</div>
          <div className="text-2xl font-semibold text-[#1a1a1a]">0</div>
        </div>

        <div className="bg-white border border-[#e5e5e5] rounded-lg p-5 shadow-sm">
          <div className="text-sm text-[#737373] mb-1.5">系统状态</div>
          <div className="text-2xl font-semibold text-[#16a34a]">正常</div>
        </div>
      </div>

      <div className="mt-8 bg-white border border-[#e5e5e5] rounded-lg p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-[#1a1a1a] mb-4">快速开始</h2>
        <ol className="list-decimal list-inside space-y-2 text-[#737373] text-sm">
          <li>在「账号池」中扫码添加平台账号</li>
          <li>在「采集任务」中创建定时采集任务</li>
          <li>在「内容资产」中查看和管理采集到的内容</li>
        </ol>
      </div>
    </div>
  )
}

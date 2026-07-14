import { Outlet } from 'react-router-dom'
import { Sidebar } from './layout/Sidebar'

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-neutral-950 text-neutral-100">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}

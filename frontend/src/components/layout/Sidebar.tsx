import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { useAuthStore } from '../../lib/authStore'
import { logout } from '../../lib/endpoints'
import { Magnetic } from '../Magnetic'
import { SidebarRepoList } from './SidebarRepoList'

function PrismMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2L22 20H2L12 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  )
}

function PlusIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function BackIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M15 18l-6-6 6-6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuthStore((s) => s.user)
  const clear = useAuthStore((s) => s.clear)
  const isAdmin = user?.role === 'admin'
  const onManagePage = location.pathname === '/repositories'

  async function handleLogout() {
    try {
      await logout()
    } finally {
      clear()
      navigate('/login', { replace: true })
    }
  }

  return (
    <aside className="flex h-screen w-[260px] shrink-0 flex-col border-r border-neutral-800 bg-neutral-950">
      <div className="flex items-center gap-2 px-4 py-5 text-neutral-200">
        <PrismMark />
        <span className="font-display text-base font-medium">Prism</span>
      </div>

      {onManagePage && (
        <Link
          to="/"
          className="mx-2 mb-2 flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-neutral-400 transition-colors hover:bg-neutral-900 hover:text-white"
        >
          <BackIcon />
          Back to workspace
        </Link>
      )}

      <div className="flex items-center justify-between px-4 pb-2">
        <span className="text-xs font-medium uppercase tracking-wide text-neutral-600">
          Repositories
        </span>
        {isAdmin && (
          <Link
            to="/repositories"
            className={`rounded p-1 transition-colors ${
              onManagePage ? 'text-[var(--brand-text)]' : 'text-neutral-600 hover:text-neutral-300'
            }`}
            title="Manage repositories"
          >
            <PlusIcon />
          </Link>
        )}
      </div>

      <div className="flex-1 overflow-y-auto pb-4">
        <SidebarRepoList />
      </div>

      <div className="border-t border-neutral-800 px-4 py-4">
        {user && (
          <div className="mb-3 flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-neutral-800 text-xs font-medium text-[var(--brand-text)]">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 leading-tight">
              <p className="truncate text-sm text-neutral-300">{user.name}</p>
              <p className="text-[11px] uppercase tracking-wide text-neutral-600">{user.role}</p>
            </div>
          </div>
        )}
        <Magnetic strength={0.15}>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleLogout}
            className="w-full rounded-md border border-neutral-800 px-3 py-1.5 text-sm text-neutral-300 transition-colors hover:bg-neutral-900"
          >
            Log out
          </motion.button>
        </Magnetic>
      </div>
    </aside>
  )
}

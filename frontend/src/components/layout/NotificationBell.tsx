import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'motion/react'
import { listNotifications, markNotificationRead } from '../../lib/endpoints'

function BellIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M13.73 21a2 2 0 0 1-3.46 0"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function formatRelativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diffMs / (1000 * 60))
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: listNotifications,
    refetchInterval: 30000,
  })

  async function handleMarkRead(notificationId: string) {
    await markNotificationRead(notificationId)
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  const unreadCount = data?.unreadCount ?? 0

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-md p-1.5 text-neutral-400 transition-colors hover:bg-neutral-900 hover:text-white"
        aria-label="Notifications"
      >
        <BellIcon />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-[var(--brand)] text-[9px] font-semibold text-neutral-950">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.15 }}
              className="absolute bottom-full left-0 z-20 mb-2 max-h-96 w-80 overflow-y-auto rounded-lg border border-neutral-800 bg-neutral-900 shadow-xl shadow-black/40"
            >
              <div className="border-b border-neutral-800 px-3.5 py-2.5">
                <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
                  Notifications
                </p>
              </div>
              {!data || data.notifications.length === 0 ? (
                <p className="px-3.5 py-6 text-center text-sm text-neutral-600">
                  No notifications yet.
                </p>
              ) : (
                data.notifications.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => !n.read && handleMarkRead(n.id)}
                    className={`flex w-full flex-col gap-1 border-b border-neutral-800 px-3.5 py-2.5 text-left transition-colors last:border-0 hover:bg-neutral-800/60 ${n.read ? '' : 'bg-neutral-800/30'}`}
                  >
                    <div className="flex items-start gap-2">
                      {!n.read && (
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--brand)]" />
                      )}
                      <p className={`text-sm ${n.read ? 'text-neutral-400' : 'text-neutral-100'}`}>
                        {n.message}
                      </p>
                    </div>
                    <span className="pl-3.5 text-[11px] text-neutral-600">
                      {formatRelativeTime(n.createdAt)}
                    </span>
                  </button>
                ))
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

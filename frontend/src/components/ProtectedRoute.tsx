import { useEffect, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { motion } from 'motion/react'
import { fetchMe } from '../lib/endpoints'
import { useAuthStore, applyUser } from '../lib/authStore'
import { useActiveRepoStore } from '../lib/activeRepoStore'
import { api } from '../lib/api'

export function ProtectedRoute() {
  const { accessToken, user, setAccessToken } = useAuthStore()
  const activeRepositoryId = useActiveRepoStore((s) => s.activeRepositoryId)
  const location = useLocation()
  const [status, setStatus] = useState<'checking' | 'ready' | 'unauthenticated'>(
    accessToken ? 'ready' : 'checking',
  )

  useEffect(() => {
    if (accessToken) {
      if (!user) {
        fetchMe().then(applyUser).catch(() => setStatus('unauthenticated'))
      }
      return
    }

    api
      .post<{ accessToken: string }>('/auth/refresh')
      .then(async (res) => {
        setAccessToken(res.data.accessToken)
        const me = await fetchMe()
        applyUser(me)
        setStatus('ready')
      })
      .catch(() => setStatus('unauthenticated'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, user, setAccessToken])

  if (status === 'checking') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <motion.div
          className="h-8 w-8 rounded-lg bg-[var(--brand)]"
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
    )
  }

  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }

  if (user) {
    const landsOnRepositoriesFirst = user.role === 'admin' || user.role === 'senior'
    const params = new URLSearchParams(location.search)
    // A repo param mid-flight (just navigated from a repo row, not yet consumed by
    // WorkspacePage's effect) or an already-active repo (param already consumed) both
    // exempt from the bare-landing redirect — otherwise the redirect races the effect
    // that strips the param and bounces the admin straight back to /repositories.
    const hasChosenRepo = params.has('repo') || !!activeRepositoryId
    const goingToWorkspace = location.pathname === '/' && !hasChosenRepo
    if (landsOnRepositoriesFirst && goingToWorkspace) {
      return <Navigate to="/repositories" replace />
    }
    if (!landsOnRepositoriesFirst && location.pathname === '/repositories') {
      return <Navigate to="/" replace />
    }
  }

  return <Outlet />
}

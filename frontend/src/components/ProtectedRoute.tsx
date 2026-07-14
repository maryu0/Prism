import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { motion } from 'motion/react'
import { fetchMe } from '../lib/endpoints'
import { useAuthStore } from '../lib/authStore'
import { api } from '../lib/api'

export function ProtectedRoute() {
  const { accessToken, user, setAccessToken, setUser } = useAuthStore()
  const [status, setStatus] = useState<'checking' | 'ready' | 'unauthenticated'>(
    accessToken ? 'ready' : 'checking',
  )

  useEffect(() => {
    if (accessToken) {
      if (!user) {
        fetchMe().then(setUser).catch(() => setStatus('unauthenticated'))
      }
      return
    }

    api
      .post<{ accessToken: string }>('/auth/refresh')
      .then(async (res) => {
        setAccessToken(res.data.accessToken)
        const me = await fetchMe()
        setUser(me)
        setStatus('ready')
      })
      .catch(() => setStatus('unauthenticated'))
  }, [accessToken, user, setAccessToken, setUser])

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

  return <Outlet />
}

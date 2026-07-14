import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import { login } from '../lib/endpoints'
import { fetchMe } from '../lib/endpoints'
import { useAuthStore } from '../lib/authStore'

function PrismMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2L22 20H2L12 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  )
}

function EyeIcon({ open }: { open: boolean }) {
  if (open) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    )
  }
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M3 3l18 18M10.6 10.7a3 3 0 0 0 4.2 4.2M6.5 6.7C4.3 8.1 2.9 10 2.5 12c1.2 4.2 5.3 7 9.5 7 1.6 0 3.1-.4 4.4-1.1M9.9 5.2A10.4 10.4 0 0 1 12 5c4.2 0 8.3 2.8 9.5 7-.4 1.4-1.1 2.7-2.1 3.8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function LoginPage() {
  const navigate = useNavigate()
  const setAccessToken = useAuthStore((s) => s.setAccessToken)
  const setUser = useAuthStore((s) => s.setUser)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const token = await login(email, password)
      setAccessToken(token)
      const me = await fetchMe()
      setUser(me)
      navigate('/', { replace: true })
    } catch {
      setError('Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden bg-neutral-950 px-4">
      <svg
        className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.35]"
        viewBox="0 0 1600 900"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M120 60c80 120-60 180 40 280s220-40 260 80-100 200 20 300"
          stroke="#5e7748"
          strokeWidth="1.5"
        />
        <circle cx="120" cy="60" r="4" fill="#5e7748" />
        <circle cx="420" cy="420" r="4" fill="#5e7748" />
        <path
          d="M1500 80c-60 140 80 160-20 260s-200-20-240 100 120 180-10 280"
          stroke="#5e7748"
          strokeWidth="1.5"
        />
        <circle cx="1500" cy="80" r="4" fill="#5e7748" />
        <circle cx="1260" cy="440" r="4" fill="#5e7748" />
      </svg>

      <div className="absolute left-8 top-8 flex items-center gap-2 text-neutral-200">
        <PrismMark />
        <span className="font-display text-base font-medium">Prism</span>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-[440px] rounded-2xl border border-neutral-800 bg-neutral-900 p-10"
      >
        <h1 className="font-serif-display text-3xl text-white">Sign in</h1>
        <p className="mt-2 text-sm text-neutral-500">
          AI-powered onboarding for your codebase.
        </p>

        <form onSubmit={handleSubmit} className="mt-8">
          <div className="space-y-5">
            <div>
              <label className="mb-1.5 flex items-center gap-1 text-sm font-medium text-neutral-300">
                Email
                <span className="h-1 w-1 rounded-full bg-red-500" />
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-sm text-white placeholder-neutral-600 outline-none transition-colors focus:border-[var(--brand)]"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label className="flex items-center gap-1 text-sm font-medium text-neutral-300">
                  Password
                  <span className="h-1 w-1 rounded-full bg-red-500" />
                </label>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-md border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 pr-10 text-sm text-white placeholder-neutral-600 outline-none transition-colors focus:border-[var(--brand)]"
                  placeholder="Your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 transition-colors hover:text-neutral-300"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  <EyeIcon open={showPassword} />
                </button>
              </div>
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-3 text-sm text-red-400"
                role="alert"
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>

          <button
            type="submit"
            disabled={loading}
            className="mt-7 flex w-full items-center justify-center gap-2 rounded-md bg-[var(--brand)] py-2.5 text-sm font-semibold text-white shadow-md shadow-black/30 transition-all hover:bg-[var(--brand-hover)] hover:shadow-lg hover:shadow-black/40 active:bg-[var(--brand-active)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading && (
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            )}
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </motion.div>
    </div>
  )
}

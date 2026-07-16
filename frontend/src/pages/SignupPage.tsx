import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import axios from 'axios'
import { register, login, fetchMe } from '../lib/endpoints'
import { useAuthStore, applyUser } from '../lib/authStore'
import { AuthLayout } from '../components/AuthLayout'

const EXPERIENCE_OPTIONS: { value: 'junior' | 'mid' | 'senior'; label: string }[] = [
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
]

export function SignupPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const inviteToken = searchParams.get('invite')
  const setAccessToken = useAuthStore((s) => s.setAccessToken)

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [experienceLevel, setExperienceLevel] = useState<'junior' | 'mid' | 'senior'>('mid')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (!inviteToken) {
    return (
      <AuthLayout>
        <h1 className="font-serif-display text-3xl text-white">Invite required</h1>
        <p className="mt-2 text-sm text-neutral-500">
          You need an invite link from your team admin to create an account.
        </p>
        <p className="mt-6 text-center text-sm text-neutral-500">
          Already have an account?{' '}
          <Link to="/login" className="text-[var(--brand-text)] hover:underline">
            Sign in
          </Link>
        </p>
      </AuthLayout>
    )
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await register({
        email,
        password,
        name,
        inviteToken: inviteToken ?? undefined,
        experienceLevel,
      })
      const token = await login(email, password)
      setAccessToken(token)
      const me = await fetchMe()
      applyUser(me)
      navigate('/', { replace: true })
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined
      setError(typeof detail === 'string' ? detail : 'Could not create your account. Check your details and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <h1 className="font-serif-display text-3xl text-white">Create your account</h1>
      <p className="mt-2 text-sm text-neutral-500">
        Set a password and tell us your experience level to get a personalized learning path.
      </p>

      <form onSubmit={handleSubmit} className="mt-8">
        <div className="space-y-5">
          <div>
            <label className="mb-1.5 flex items-center gap-1 text-sm font-medium text-neutral-300">
              Name
              <span className="h-1 w-1 rounded-full bg-red-500" />
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-sm text-white placeholder-neutral-600 outline-none transition-colors focus:border-[var(--brand)]"
              placeholder="Your name"
            />
          </div>
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
            <label className="mb-1.5 flex items-center gap-1 text-sm font-medium text-neutral-300">
              Password
              <span className="h-1 w-1 rounded-full bg-red-500" />
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-sm text-white placeholder-neutral-600 outline-none transition-colors focus:border-[var(--brand)]"
              placeholder="At least 8 characters"
            />
          </div>
          <div>
            <label className="mb-1.5 flex items-center gap-1 text-sm font-medium text-neutral-300">
              Experience level
              <span className="h-1 w-1 rounded-full bg-red-500" />
            </label>
            <select
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value as 'junior' | 'mid' | 'senior')}
              className="w-full rounded-md border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-sm text-white outline-none transition-colors focus:border-[var(--brand)]"
            >
              {EXPERIENCE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
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
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-neutral-500">
        Already have an account?{' '}
        <Link to="/login" className="text-[var(--brand-text)] hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}

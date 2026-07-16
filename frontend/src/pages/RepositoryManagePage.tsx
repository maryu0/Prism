import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'motion/react'
import axios from 'axios'
import {
  connectRepository,
  getAuditLog,
  inviteDeveloper,
  listRepositories,
  syncRepository,
} from '../lib/endpoints'
import { useAuthStore, type Role } from '../lib/authStore'
import { STATUS_META, repoName } from '../lib/repoDisplay'
import { BlurText } from '../components/ui/BlurText'
import type { Repository } from '../lib/types'

const ROLE_OPTIONS: { value: Role; label: string }[] = [
  { value: 'developer', label: 'Developer' },
  { value: 'senior', label: 'Senior' },
  { value: 'admin', label: 'Admin' },
]

function InviteDeveloperForm({ repositories }: { repositories: Repository[] }) {
  const workspaceId = useAuthStore((s) => s.user?.workspaceId)
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<Role>('developer')
  const [repositoryId, setRepositoryId] = useState(repositories[0]?.id ?? '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [inviteUrl, setInviteUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!workspaceId || !repositoryId) return
    setError(null)
    setInviteUrl(null)
    setSubmitting(true)
    try {
      const result = await inviteDeveloper({ workspaceId, email, role, assignedRepositoryId: repositoryId })
      setInviteUrl(result.inviteUrl)
      setEmail('')
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined
      setError(typeof detail === 'string' ? detail : 'Could not create invite. Check the email and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCopy() {
    if (!inviteUrl) return
    await navigator.clipboard.writeText(inviteUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8 rounded-xl border border-neutral-800 bg-neutral-900 p-5"
    >
      <label className="mb-2 block text-xs font-medium tracking-wide text-neutral-400">
        INVITE A DEVELOPER
      </label>
      <div className="grid grid-cols-[2fr_1fr_1.5fr_auto] gap-2">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="developer@company.com"
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-sm text-white placeholder-neutral-600 outline-none transition-colors focus:border-[var(--brand)]"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as Role)}
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-sm text-white outline-none transition-colors focus:border-[var(--brand)]"
        >
          {ROLE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <select
          value={repositoryId}
          onChange={(e) => setRepositoryId(e.target.value)}
          required
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-sm text-white outline-none transition-colors focus:border-[var(--brand)]"
        >
          {repositories.length === 0 && <option value="">No repositories connected</option>}
          {repositories.map((repo) => (
            <option key={repo.id} value={repo.id}>
              {repoName(repo.githubUrl)}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={submitting || repositories.length === 0}
          className="shrink-0 rounded-lg bg-[var(--brand)] px-5 py-2.5 text-sm font-medium text-neutral-950 transition-colors hover:bg-[var(--brand-hover)] disabled:opacity-60"
        >
          {submitting ? 'Sending…' : 'Invite'}
        </button>
      </div>
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-2.5 text-sm text-red-400"
          >
            {error}
          </motion.p>
        )}
        {inviteUrl && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-3 flex items-center gap-2 rounded-lg border border-neutral-800 bg-neutral-950 px-3.5 py-2.5"
          >
            <span className="flex-1 truncate font-mono text-xs text-neutral-400">{inviteUrl}</span>
            <button
              type="button"
              onClick={handleCopy}
              className="shrink-0 rounded-md border border-neutral-800 px-2.5 py-1 text-xs text-neutral-300 transition-colors hover:bg-neutral-800 hover:text-white"
            >
              {copied ? 'Copied' : 'Copy link'}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.form>
  )
}

const listVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0 },
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 border-b border-neutral-800 px-5 py-4 last:border-0">
      <div className="h-9 w-9 shrink-0 animate-pulse rounded-lg bg-white/5" />
      <div className="flex-1 space-y-2">
        <div className="h-3.5 w-48 animate-pulse rounded bg-white/10" />
        <div className="h-3 w-32 animate-pulse rounded bg-white/5" />
      </div>
      <div className="h-5 w-16 animate-pulse rounded-full bg-white/5" />
    </div>
  )
}

const PILL_CLASS =
  'rounded-md px-2 py-1 font-mono text-[11px] font-medium uppercase tracking-wide bg-white/5 text-neutral-400'

const ACTION_LABELS: Record<string, string> = {
  'invite.created': 'Invited a developer',
  'user.registered_via_invite': 'Joined via invite',
}

function AuditLogSection() {
  const { data, isLoading } = useQuery({
    queryKey: ['audit-log'],
    queryFn: getAuditLog,
  })

  if (isLoading) {
    return <div className="h-32 animate-pulse rounded-xl border border-neutral-800 bg-neutral-900/40" />
  }

  if (!data || data.entries.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 py-8 text-center">
        <p className="text-sm text-neutral-500">No activity recorded yet.</p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/40">
      {data.entries.map((entry, i) => (
        <div
          key={i}
          className="flex items-center justify-between gap-4 border-b border-neutral-800 px-5 py-3 last:border-0"
        >
          <div className="flex min-w-0 items-center gap-3">
            <span className={PILL_CLASS}>{ACTION_LABELS[entry.action] ?? entry.action}</span>
            <p className="truncate font-mono text-xs text-neutral-500">{entry.targetId}</p>
          </div>
          <span className="shrink-0 text-xs text-neutral-600">
            {new Date(entry.timestamp).toLocaleString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
      ))}
    </div>
  )
}

export function RepositoryManagePage() {
  const isAdmin = useAuthStore((s) => s.user?.role === 'admin')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: repositories, isLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: listRepositories,
    refetchInterval: 5000,
  })

  const [githubUrl, setGithubUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  async function handleConnect(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await connectRepository({ githubUrl })
      setGithubUrl('')
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    } catch {
      setFormError('Could not connect repository. Check the URL and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleSync(repositoryId: string) {
    await syncRepository(repositoryId)
    queryClient.invalidateQueries({ queryKey: ['repositories'] })
  }

  return (
    <div className="mx-auto max-w-4xl px-8 py-8">
      <div className="mb-8 flex items-end justify-between gap-4 border-b border-neutral-800 pb-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-white">
            <BlurText text="Manage repositories" />
          </h1>
          <p className="mt-1.5 text-sm text-neutral-500">
            Connect a GitHub repository to index its code for search and AI chat.
          </p>
        </div>
        {repositories && repositories.length > 0 && (
          <span className="shrink-0 whitespace-nowrap text-sm text-neutral-500">
            {repositories.length} connected
          </span>
        )}
      </div>

      {isAdmin && (
        <motion.form
          onSubmit={handleConnect}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 rounded-xl border border-neutral-800 bg-neutral-900 p-5"
        >
          <label className="mb-2 block text-xs font-medium tracking-wide text-neutral-400">
            GITHUB REPOSITORY URL
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              required
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/org/repo"
              className="flex-1 rounded-lg border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-sm text-white placeholder-neutral-600 outline-none transition-colors focus:border-[var(--brand)]"
            />
            <button
              type="submit"
              disabled={submitting}
              className="shrink-0 rounded-lg bg-[var(--brand)] px-5 py-2.5 text-sm font-medium text-neutral-950 transition-colors hover:bg-[var(--brand-hover)] disabled:opacity-60"
            >
              {submitting ? 'Connecting…' : 'Connect'}
            </button>
          </div>
          <AnimatePresence>
            {formError && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-2.5 text-sm text-red-400"
              >
                {formError}
              </motion.p>
            )}
          </AnimatePresence>
        </motion.form>
      )}

      {isAdmin && repositories && repositories.length > 0 && (
        repositories.some((r) => r.status === 'ready') ? (
          <InviteDeveloperForm repositories={repositories.filter((r) => r.status === 'ready')} />
        ) : (
          <div className="mb-8 rounded-xl border border-dashed border-neutral-800 px-5 py-4 text-sm text-neutral-500">
            Invites unlock once a repository finishes syncing.
          </div>
        )
      )}

      {isLoading && (
        <div className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/40">
          <SkeletonRow />
          <SkeletonRow />
        </div>
      )}

      {repositories && repositories.length === 0 && (
        <div className="rounded-xl border border-dashed border-neutral-800 py-12 text-center">
          <p className="text-sm text-neutral-500">No repositories connected yet.</p>
        </div>
      )}

      {repositories && repositories.length > 0 && (
        <motion.div
          variants={listVariants}
          initial="hidden"
          animate="show"
          className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/40"
        >
          <AnimatePresence>
            {repositories.map((repo) => {
              const meta = STATUS_META[repo.status]
              const isReady = repo.status === 'ready'
              return (
                <motion.div
                  key={repo.id}
                  variants={itemVariants}
                  layout
                  onClick={() => isReady && navigate(`/?repo=${repo.id}`)}
                  className={`group flex items-center gap-4 border-b border-neutral-800 px-5 py-4 transition-colors last:border-0 hover:bg-neutral-900/40 ${isReady ? 'cursor-pointer' : ''}`}
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--brand)]/15 font-mono text-xs font-semibold text-[var(--brand-text)]">
                    {repoName(repo.githubUrl).slice(0, 2).toUpperCase()}
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-white">
                      {repoName(repo.githubUrl)}
                    </p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <span className={PILL_CLASS}>{repo.defaultBranch}</span>
                      <span className={PILL_CLASS}>{repo.locCount.toLocaleString()} lines</span>
                      {repo.lastSyncedAt && (
                        <span className={PILL_CLASS}>
                          synced{' '}
                          {new Date(repo.lastSyncedAt).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center gap-4">
                    <div className="flex items-center gap-1.5">
                      <span className="relative flex h-1.5 w-1.5">
                        {repo.status === 'syncing' && (
                          <motion.span
                            className={`absolute inline-flex h-full w-full rounded-full ${meta.dot}`}
                            animate={{ scale: [1, 2], opacity: [0.7, 0] }}
                            transition={{ duration: 1.4, repeat: Infinity }}
                          />
                        )}
                        <span className={`relative inline-flex h-1.5 w-1.5 rounded-full ${meta.dot}`} />
                      </span>
                      <span className={`text-xs font-medium ${meta.text}`}>{meta.label}</span>
                    </div>
                    {isAdmin && (
                      <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.96 }}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleSync(repo.id)
                        }}
                        className="rounded-md border border-neutral-800 px-3 py-1.5 text-xs text-neutral-400 opacity-0 transition-all hover:bg-neutral-800 hover:text-white group-hover:opacity-100"
                      >
                        Re-sync
                      </motion.button>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </motion.div>
      )}

      {isAdmin && (
        <div className="mt-10">
          <h2 className="mb-4 border-b border-neutral-800 pb-3 text-sm font-medium tracking-wide text-neutral-400">
            ACTIVITY LOG
          </h2>
          <AuditLogSection />
        </div>
      )}
    </div>
  )
}

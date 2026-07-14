import { useState, type FormEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'motion/react'
import { connectRepository, listRepositories, syncRepository } from '../lib/endpoints'
import { useAuthStore } from '../lib/authStore'
import { STATUS_META, repoName } from '../lib/repoDisplay'
import { BlurText } from '../components/ui/BlurText'

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

export function RepositoryManagePage() {
  const isAdmin = useAuthStore((s) => s.user?.role === 'admin')
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
              return (
                <motion.div
                  key={repo.id}
                  variants={itemVariants}
                  layout
                  className="group flex items-center gap-4 border-b border-neutral-800 px-5 py-4 transition-colors last:border-0 hover:bg-neutral-900/40"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--brand)]/15 font-mono text-xs font-semibold text-[var(--brand-text)]">
                    {repoName(repo.githubUrl).slice(0, 2).toUpperCase()}
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-white">
                      {repoName(repo.githubUrl)}
                    </p>
                    <p className="mt-0.5 truncate text-xs text-neutral-500">
                      {repo.defaultBranch} · {repo.locCount.toLocaleString()} lines
                      {repo.lastSyncedAt &&
                        ` · synced ${new Date(repo.lastSyncedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`}
                    </p>
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
                        onClick={() => handleSync(repo.id)}
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
    </div>
  )
}

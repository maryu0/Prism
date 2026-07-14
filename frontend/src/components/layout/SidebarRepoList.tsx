import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'motion/react'
import { listRepositories, syncRepository } from '../../lib/endpoints'
import { useAuthStore } from '../../lib/authStore'
import { useActiveRepoStore } from '../../lib/activeRepoStore'
import { STATUS_META, repoName } from '../../lib/repoDisplay'

function RefreshIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 4v5h5M20 20v-5h-5M4.5 15a8 8 0 0 0 14.5 3M19.5 9A8 8 0 0 0 5 6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function SidebarRepoList() {
  const isAdmin = useAuthStore((s) => s.user?.role === 'admin')
  const queryClient = useQueryClient()
  const activeRepositoryId = useActiveRepoStore((s) => s.activeRepositoryId)
  const setActiveRepositoryId = useActiveRepoStore((s) => s.setActiveRepositoryId)
  const { data: repositories, isLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: listRepositories,
    refetchInterval: 5000,
  })

  async function handleSync(e: React.MouseEvent, repositoryId: string) {
    e.stopPropagation()
    await syncRepository(repositoryId)
    queryClient.invalidateQueries({ queryKey: ['repositories'] })
  }

  if (isLoading) {
    return (
      <div className="space-y-1.5 px-2">
        {[0, 1].map((i) => (
          <div key={i} className="h-11 animate-pulse rounded-md bg-neutral-900" />
        ))}
      </div>
    )
  }

  if (!repositories || repositories.length === 0) {
    return <p className="px-3 text-xs text-neutral-600">No repositories yet.</p>
  }

  return (
    <div className="space-y-1">
      {repositories.map((repo) => {
        const meta = STATUS_META[repo.status]
        const isActive = repo.id === activeRepositoryId
        return (
          <button
            key={repo.id}
            onClick={() =>
              setActiveRepositoryId(isActive ? null : repo.id)
            }
            className={`group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left transition-colors ${
              isActive ? 'bg-neutral-800' : 'hover:bg-neutral-900'
            }`}
          >
            <span className="relative flex h-1.5 w-1.5 shrink-0">
              {repo.status === 'syncing' && (
                <motion.span
                  className={`absolute inline-flex h-full w-full rounded-full ${meta.dot}`}
                  animate={{ scale: [1, 2], opacity: [0.7, 0] }}
                  transition={{ duration: 1.4, repeat: Infinity }}
                />
              )}
              <span className={`relative inline-flex h-1.5 w-1.5 rounded-full ${meta.dot}`} />
            </span>
            <span className="min-w-0 flex-1 truncate text-sm text-neutral-200">
              {repoName(repo.githubUrl)}
            </span>
            {isAdmin && (
              <span
                onClick={(e) => handleSync(e, repo.id)}
                className="shrink-0 rounded p-1 text-neutral-600 opacity-0 transition-opacity hover:text-neutral-300 group-hover:opacity-100"
                title="Re-sync"
              >
                <RefreshIcon />
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

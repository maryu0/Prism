import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'motion/react'
import { completeLearningModule, getMyLearningPath, listLearningModules } from '../lib/endpoints'
import { ModuleDetailPanel } from '../components/learning/ModuleDetailPanel'
import type { LearningModule } from '../lib/types'

function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest === 0 ? `${hours}h` : `${hours}h ${rest}m`
}

function fileLabel(targetEntityId: string): string {
  const path = targetEntityId.split(':').slice(1).join(':')
  return path || targetEntityId
}

const STATUS_META: Record<LearningModule['status'], { label: string; dot: string; text: string }> = {
  done: { label: 'Done', dot: 'bg-[var(--brand)]', text: 'text-[var(--brand-text)]' },
  available: { label: 'Available', dot: 'bg-neutral-400', text: 'text-neutral-300' },
  locked: { label: 'Locked', dot: 'bg-neutral-700', text: 'text-neutral-600' },
}

const PILL_CLASS =
  'rounded-md px-2 py-1 font-mono text-[11px] font-medium uppercase tracking-wide bg-white/5 text-neutral-400'

function ModuleRow({
  module,
  onComplete,
  onOpen,
}: {
  module: LearningModule
  onComplete: (id: string) => void
  onOpen: (module: LearningModule) => void
}) {
  const [submitting, setSubmitting] = useState(false)
  const meta = STATUS_META[module.status]
  const isLocked = module.status === 'locked'

  async function handleComplete(e: React.MouseEvent) {
    e.stopPropagation()
    setSubmitting(true)
    try {
      onComplete(module.id)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <motion.div
      layout
      onClick={() => !isLocked && onOpen(module)}
      className={`border-b border-neutral-800 px-5 py-4 transition-colors last:border-0 ${isLocked ? 'opacity-50' : 'cursor-pointer hover:bg-neutral-900/60'}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${meta.dot}`} />
            <p className="truncate text-sm font-medium text-white">{module.title}</p>
            <span className={PILL_CLASS}>{formatMinutes(module.estimatedMinutes)}</span>
            {module.targetEntityIds.length > 0 && (
              <span className={PILL_CLASS} title={module.targetEntityIds.map(fileLabel).join(', ')}>
                {module.targetEntityIds.length} file{module.targetEntityIds.length === 1 ? '' : 's'}
              </span>
            )}
          </div>
          <p className="mt-1.5 text-xs text-neutral-500">{module.description}</p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <span className={`text-xs font-medium ${meta.text}`}>{meta.label}</span>
          {module.status === 'available' && (
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.96 }}
              disabled={submitting}
              onClick={handleComplete}
              className="rounded-md bg-[var(--brand)] px-3 py-1.5 text-xs font-medium text-neutral-950 transition-colors hover:bg-[var(--brand-hover)] disabled:opacity-60"
            >
              {submitting ? 'Marking…' : 'Mark complete'}
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export function LearningPathPanel() {
  const queryClient = useQueryClient()
  const [selectedModule, setSelectedModule] = useState<LearningModule | null>(null)
  const { data: path, isLoading: isLoadingPath, error: pathError } = useQuery({
    queryKey: ['my-learning-path'],
    queryFn: getMyLearningPath,
    retry: false,
  })

  const { data: modules, isLoading: isLoadingModules } = useQuery({
    queryKey: ['learning-modules', path?.id],
    queryFn: () => listLearningModules(path!.id),
    enabled: !!path,
  })

  async function handleComplete(moduleId: string) {
    await completeLearningModule(moduleId)
    queryClient.invalidateQueries({ queryKey: ['learning-modules', path?.id] })
    queryClient.invalidateQueries({ queryKey: ['my-progress'] })
    queryClient.invalidateQueries({ queryKey: ['team-progress'] })
  }

  if (isLoadingPath || (path && isLoadingModules)) {
    return (
      <div className="space-y-2">
        <div className="h-16 animate-pulse rounded-xl border border-neutral-800 bg-neutral-900/40" />
        <div className="h-16 animate-pulse rounded-xl border border-neutral-800 bg-neutral-900/40" />
        <div className="h-16 animate-pulse rounded-xl border border-neutral-800 bg-neutral-900/40" />
      </div>
    )
  }

  if (pathError) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 py-16 text-center">
        <p className="text-sm text-neutral-500">
          No active learning path yet. One is generated automatically when you join via an invite.
        </p>
      </div>
    )
  }

  if (!modules || modules.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 py-16 text-center">
        <p className="text-sm text-neutral-500">Your learning path has no modules yet.</p>
      </div>
    )
  }

  const sorted = [...modules].sort((a, b) => a.order - b.order)

  return (
    <div className="flex gap-4">
      <div className="flex-1">
        <p className="mb-4 text-sm text-neutral-500">
          A dependency-ordered path through the codebase, tailored to your role and experience.
        </p>
        <div className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/40">
          <AnimatePresence initial={false}>
            {sorted.map((module) => (
              <ModuleRow
                key={module.id}
                module={module}
                onComplete={handleComplete}
                onOpen={setSelectedModule}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>
      <AnimatePresence>
        {selectedModule && (
          <ModuleDetailPanel module={selectedModule} onClose={() => setSelectedModule(null)} />
        )}
      </AnimatePresence>
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { getFileComponents } from '../../lib/endpoints'
import { useActiveRepoStore } from '../../lib/activeRepoStore'
import { useWorkspaceIntentStore } from '../../lib/workspaceIntentStore'
import type { LearningModule } from '../../lib/types'

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function ChatIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 4h16v12H8l-4 4V4Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function GraphIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="5" cy="6" r="2.2" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="19" cy="6" r="2.2" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="18" r="2.2" stroke="currentColor" strokeWidth="1.6" />
      <path d="M7 7.5L10.5 16M17 7.5L13.5 16" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  )
}

function complexityColor(score: number): string {
  if (score >= 40) return 'text-red-400'
  if (score >= 15) return 'text-amber-400'
  return 'text-[var(--brand-text)]'
}

function splitEntityId(targetEntityId: string): { repositoryId: string; path: string } {
  const [repositoryId, ...rest] = targetEntityId.split(':')
  return { repositoryId, path: rest.join(':') }
}

function FileComponents({
  targetEntityId,
  onAskAboutFile,
  onViewInGraph,
}: {
  targetEntityId: string
  onAskAboutFile: (path: string) => void
  onViewInGraph: (fileId: string) => void
}) {
  const { repositoryId, path } = splitEntityId(targetEntityId)
  const { data, isLoading } = useQuery({
    queryKey: ['file-components', repositoryId, targetEntityId],
    queryFn: () => getFileComponents(repositoryId, targetEntityId),
  })

  return (
    <div className="rounded-lg border border-neutral-800 px-4 py-3.5">
      <div className="flex items-center justify-between gap-3">
        <p className="truncate font-mono text-sm font-medium text-white">{path}</p>
        <div className="flex shrink-0 gap-1.5">
          <button
            onClick={() => onViewInGraph(targetEntityId)}
            title="View in Lineage Graph"
            className="rounded-md border border-neutral-800 p-1.5 text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-white"
          >
            <GraphIcon />
          </button>
          <button
            onClick={() => onAskAboutFile(path)}
            title="Ask AI about this file"
            className="rounded-md border border-neutral-800 p-1.5 text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-white"
          >
            <ChatIcon />
          </button>
        </div>
      </div>
      {isLoading && <p className="mt-2 text-xs text-neutral-600">Loading…</p>}
      {!isLoading && data && data.components.length === 0 && (
        <p className="mt-2 text-xs text-neutral-600">No components in this file.</p>
      )}
      {!isLoading && data && data.components.length > 0 && (
        <div className="mt-3 space-y-2">
          {data.components.map((comp, i) => (
            <div key={i} className="flex items-center justify-between gap-3 text-sm">
              <span className="truncate font-mono text-neutral-300">{comp.name}</span>
              <span className={`shrink-0 font-mono text-xs ${complexityColor(comp.complexityScore)}`}>
                {comp.complexityScore} LOC
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function ModuleDetailPanel({ module, onClose }: { module: LearningModule; onClose: () => void }) {
  const navigate = useNavigate()
  const setActiveRepositoryId = useActiveRepoStore((s) => s.setActiveRepositoryId)
  const setPrefillQuestion = useWorkspaceIntentStore((s) => s.setPrefillQuestion)
  const setFocusFileId = useWorkspaceIntentStore((s) => s.setFocusFileId)

  function handleAskAboutModule() {
    const files = module.targetEntityIds.map((id) => splitEntityId(id).path)
    const isFileModule = files.length === 1 && files[0] === module.title
    const question = isFileModule
      ? `Can you explain how ${module.title} works and what it's used for?`
      : files.length > 0
        ? `Can you explain ${files.join(', ')} and how they relate to "${module.title}"?`
        : `Can you explain: ${module.title}?`
    setPrefillQuestion(question)
    navigate('/?tab=chat')
  }

  function handleAskAboutFile(path: string) {
    setPrefillQuestion(`Can you explain how ${path} works?`)
    navigate('/?tab=chat')
  }

  function handleViewInGraph(fileId: string) {
    const repositoryId = splitEntityId(fileId).repositoryId
    setActiveRepositoryId(repositoryId)
    setFocusFileId(fileId)
    navigate('/?tab=graph')
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 16 }}
      transition={{ duration: 0.2 }}
      className="w-[460px] shrink-0 overflow-y-auto rounded-xl border border-neutral-800 bg-neutral-900 p-6"
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <h2 className="font-display text-lg font-semibold text-white">{module.title}</h2>
        <button
          onClick={onClose}
          className="shrink-0 rounded p-1 text-neutral-500 transition-colors hover:bg-neutral-800 hover:text-white"
        >
          <CloseIcon />
        </button>
      </div>

      <p className="mb-5 text-sm leading-relaxed text-neutral-400">{module.description}</p>

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleAskAboutModule}
        className="mb-5 flex w-full items-center justify-center gap-2 rounded-md bg-[var(--brand)] py-2.5 text-sm font-medium text-neutral-950 transition-colors hover:bg-[var(--brand-hover)]"
      >
        <ChatIcon />
        Ask AI about this module
      </motion.button>

      {module.targetEntityIds.length > 0 && (
        <div className="border-t border-neutral-800 pt-5">
          <p className="mb-3 text-xs font-medium uppercase tracking-wide text-neutral-600">
            Files to review
          </p>
          <div className="space-y-3">
            {module.targetEntityIds.map((id) => (
              <FileComponents
                key={id}
                targetEntityId={id}
                onAskAboutFile={handleAskAboutFile}
                onViewInGraph={handleViewInGraph}
              />
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}

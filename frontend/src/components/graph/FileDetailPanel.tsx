import { motion } from 'motion/react'
import type { FileComponent } from '../../lib/types'
import type { FileNodeData } from './FileNode'

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function complexityColor(score: number): string {
  if (score >= 40) return 'text-red-400'
  if (score >= 15) return 'text-amber-400'
  return 'text-[var(--brand-text)]'
}

type FileDetailPanelProps = {
  node: FileNodeData & { id: string }
  components: FileComponent[] | undefined
  isLoading: boolean
  onClose: () => void
}

export function FileDetailPanel({ node, components, isLoading, onClose }: FileDetailPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 16 }}
      transition={{ duration: 0.2 }}
      className="w-[320px] shrink-0 overflow-y-auto rounded-xl border border-neutral-800 bg-neutral-900 p-5"
    >
      <div className="mb-4 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-mono text-sm font-medium text-white">{node.label}</p>
          <p className="mt-1 break-all text-xs text-neutral-500">{node.path}</p>
        </div>
        <button
          onClick={onClose}
          className="shrink-0 rounded p-1 text-neutral-500 transition-colors hover:bg-neutral-800 hover:text-white"
        >
          <CloseIcon />
        </button>
      </div>

      <div className="mb-4 flex gap-4 text-xs text-neutral-500">
        <span>{node.language}</span>
        <span>{node.componentCount} components</span>
        <span>{node.avgComplexity.toFixed(0)} avg LOC</span>
      </div>

      <div className="border-t border-neutral-800 pt-4">
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-600">
          Components
        </p>
        {isLoading && <p className="text-xs text-neutral-500">Loading…</p>}
        {!isLoading && components && components.length === 0 && (
          <p className="text-xs text-neutral-500">No components in this file.</p>
        )}
        {!isLoading && components && components.length > 0 && (
          <div className="space-y-2">
            {components.map((comp, i) => (
              <div key={i} className="rounded-md border border-neutral-800 px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate font-mono text-xs font-medium text-white">
                    {comp.name}
                  </span>
                  <span className={`shrink-0 font-mono text-[11px] ${complexityColor(comp.complexityScore)}`}>
                    {comp.complexityScore} LOC
                  </span>
                </div>
                <p className="mt-0.5 text-[11px] text-neutral-500">
                  {comp.type} · lines {comp.startLine}-{comp.endLine}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

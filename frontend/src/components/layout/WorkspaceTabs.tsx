import { motion } from 'motion/react'

export type WorkspaceTab = 'search' | 'chat' | 'graph' | 'learning' | 'progress'

const TABS: { id: WorkspaceTab; label: string }[] = [
  { id: 'search', label: 'Search' },
  { id: 'chat', label: 'Ask AI' },
  { id: 'graph', label: 'Lineage Graph' },
  { id: 'learning', label: 'Learning Path' },
  { id: 'progress', label: 'Progress' },
]

type WorkspaceTabsProps = {
  active: WorkspaceTab
  onChange: (tab: WorkspaceTab) => void
}

export function WorkspaceTabs({ active, onChange }: WorkspaceTabsProps) {
  return (
    <div className="relative flex gap-1 border-b border-neutral-800 px-8">
      {TABS.map((tab) => {
        const isActive = tab.id === active
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className="relative px-3 py-3 text-sm transition-colors"
          >
            {isActive && (
              <motion.div
                layoutId="workspace-tab-underline"
                className="absolute inset-x-0 bottom-0 h-[2px] bg-[var(--brand)]"
                transition={{ type: 'spring', stiffness: 400, damping: 32 }}
              />
            )}
            <span className={isActive ? 'font-medium text-white' : 'text-neutral-400 hover:text-white'}>
              {tab.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}

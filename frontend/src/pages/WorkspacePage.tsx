import { useSearchParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import { WorkspaceTabs, type WorkspaceTab } from '../components/layout/WorkspaceTabs'
import { SearchPanel } from './SearchPanel'
import { ChatPanel } from './ChatPanel'
import { LineageGraphPanel } from './LineageGraphPanel'

const VALID_TABS: WorkspaceTab[] = ['search', 'chat', 'graph']

export function WorkspacePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = searchParams.get('tab')
  const activeTab: WorkspaceTab = VALID_TABS.includes(tabParam as WorkspaceTab)
    ? (tabParam as WorkspaceTab)
    : 'search'

  function handleTabChange(tab: WorkspaceTab) {
    setSearchParams({ tab })
  }

  return (
    <div className="flex h-screen flex-col">
      <WorkspaceTabs active={activeTab} onChange={handleTabChange} />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            {activeTab === 'search' && <SearchPanel />}
            {activeTab === 'chat' && <ChatPanel />}
            {activeTab === 'graph' && <LineageGraphPanel />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}

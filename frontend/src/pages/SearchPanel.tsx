import { useState, type FormEvent } from 'react'
import { motion, AnimatePresence, useMotionValue, useTransform, animate } from 'motion/react'
import { useEffect } from 'react'
import { searchCode } from '../lib/endpoints'
import type { SearchResult } from '../lib/types'

const TYPE_COLORS: Record<string, string> = {
  function: 'text-[var(--brand-text)] bg-[var(--brand)]/10',
  class: 'text-violet-300 bg-violet-500/10',
}

const listVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0 },
}

function SimilarityBadge({ similarity }: { similarity: number }) {
  const target = Math.round(similarity * 100)
  const count = useMotionValue(0)
  const rounded = useTransform(count, (v) => `${Math.round(v)}%`)
  const [display, setDisplay] = useState('0%')

  useEffect(() => {
    const controls = animate(count, target, { duration: 0.6, ease: 'easeOut' })
    const unsub = rounded.on('change', setDisplay)
    return () => {
      controls.stop()
      unsub()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target])

  return (
    <span className="shrink-0 font-mono text-xs tabular-nums text-neutral-500">{display} match</span>
  )
}

export function SearchPanel() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await searchCode(query)
      setResults(data)
    } catch {
      setError('Search failed. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <p className="mb-6 text-sm text-neutral-500">
        Search across connected repositories by meaning, not just keywords.
      </p>

      <form onSubmit={handleSubmit} className="mb-8 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. where do we validate JWT tokens?"
          className={`flex-1 rounded-lg border border-neutral-800 bg-neutral-900 px-3.5 py-2.5 text-sm text-white placeholder-neutral-600 outline-none transition-all focus:border-[var(--brand)] ${loading ? 'animate-pulse' : ''}`}
        />
        <motion.button
          type="submit"
          disabled={loading}
          whileHover={{ scale: loading ? 1 : 1.02 }}
          whileTap={{ scale: loading ? 1 : 0.97 }}
          className="flex shrink-0 items-center gap-2 rounded-lg bg-[var(--brand)] px-5 py-2.5 text-sm font-medium text-neutral-950 transition-colors hover:bg-[var(--brand-hover)] disabled:opacity-60"
        >
          {loading && (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-neutral-950/30 border-t-neutral-950" />
          )}
          {loading ? 'Searching…' : 'Search'}
        </motion.button>
      </form>

      <AnimatePresence mode="wait">
        {error && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mb-4 text-sm text-red-400"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      {results && results.length === 0 && (
        <div className="rounded-xl border border-dashed border-neutral-800 py-12 text-center">
          <p className="text-sm text-neutral-500">No matches found.</p>
        </div>
      )}

      {results && results.length > 0 && (
        <motion.div
          variants={listVariants}
          initial="hidden"
          animate="show"
          className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/40"
        >
          {results.map((result) => (
            <motion.div
              key={result.id}
              variants={itemVariants}
              className="flex items-center gap-4 border-b border-neutral-800 px-5 py-4 transition-colors last:border-0 hover:bg-neutral-900/40"
            >
              <span
                className={`shrink-0 rounded-md px-2 py-1 font-mono text-[11px] font-medium uppercase tracking-wide ${TYPE_COLORS[result.type] ?? 'bg-white/5 text-neutral-400'}`}
              >
                {result.type}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-mono text-sm font-medium text-white">{result.name}</p>
                <p className="mt-0.5 truncate font-mono text-xs text-neutral-500">
                  {result.filePath}:{result.startLine}-{result.endLine}
                </p>
              </div>
              <SimilarityBadge similarity={result.similarity} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  )
}

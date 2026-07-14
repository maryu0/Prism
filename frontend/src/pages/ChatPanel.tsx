import { useState, useRef, useEffect, type FormEvent, type MouseEvent } from 'react'
import { motion, AnimatePresence, useMotionValue, useTransform } from 'motion/react'
import { askQuestion } from '../lib/endpoints'
import type { Citation } from '../lib/types'
import { TypingIndicator } from '../components/TypingIndicator'

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const glowX = useMotionValue(0)
  const glowY = useMotionValue(0)
  const glowBackground = useTransform(
    [glowX, glowY],
    ([x, y]) => `radial-gradient(180px circle at ${x}px ${y}px, rgba(94,119,72,0.15), transparent 70%)`,
  )

  function handleInputAreaMouseMove(e: MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    glowX.set(e.clientX - rect.left)
    glowY.set(e.clientY - rect.top)
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const q = question.trim()
    if (!q) return
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content: q }])
    setQuestion('')
    setLoading(true)
    try {
      const res = await askQuestion(q)
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: res.answer,
          citations: res.citations,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Something went wrong answering that.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <p className="mb-6 text-sm text-neutral-500">
        Grounded answers with citations, drawn only from connected repositories.
      </p>

      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="rounded-xl border border-dashed border-neutral-800 py-12 text-center">
            <p className="text-sm text-neutral-500">
              Ask anything about the connected repositories — e.g. "How does auth work here?"
            </p>
          </div>
        )}
        <AnimatePresence mode="popLayout">
          {messages.map((msg) =>
            msg.role === 'user' ? (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, x: 24 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className="ml-auto max-w-lg rounded-lg bg-[var(--brand)]/10 p-4 text-[var(--brand-text)]"
              >
                <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
              </motion.div>
            ) : (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="max-w-2xl rounded-lg border border-neutral-800 bg-neutral-900 p-4 text-neutral-200"
              >
                <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                {msg.citations && msg.citations.length > 0 && (
                  <motion.div
                    initial="hidden"
                    animate="show"
                    variants={{ show: { transition: { staggerChildren: 0.05 } } }}
                    className="mt-3 flex flex-wrap gap-2 border-t border-neutral-800 pt-3"
                  >
                    {msg.citations.map((c, ci) => (
                      <motion.span
                        key={ci}
                        variants={{
                          hidden: { opacity: 0, y: 4 },
                          show: { opacity: 1, y: 0 },
                        }}
                        whileHover={{ y: -1, backgroundColor: 'rgba(255,255,255,0.1)' }}
                        className="rounded-md bg-white/5 px-2 py-1 font-mono text-xs text-neutral-400"
                      >
                        {c.filePath}:{c.startLine}
                      </motion.span>
                    ))}
                  </motion.div>
                )}
              </motion.div>
            ),
          )}
        </AnimatePresence>
        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <TypingIndicator />
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      <div
        onMouseMove={handleInputAreaMouseMove}
        className="relative mt-4 overflow-hidden rounded-md"
      >
        <motion.div
          className="pointer-events-none absolute inset-0"
          style={{ background: glowBackground }}
        />
        <form onSubmit={handleSubmit} className="relative flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question…"
            className="flex-1 rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2.5 text-sm text-white placeholder-neutral-500 outline-none transition-all focus:border-[var(--brand)]"
          />
          <motion.button
            type="submit"
            disabled={loading}
            whileHover={{ scale: loading ? 1 : 1.03, x: loading ? 0 : 2 }}
            whileTap={{ scale: loading ? 1 : 0.96 }}
            className="rounded-md bg-[var(--brand)] px-4 py-2.5 text-sm font-medium text-neutral-950 transition-colors hover:bg-[var(--brand-hover)] disabled:opacity-60"
          >
            Send
          </motion.button>
        </form>
      </div>
    </div>
  )
}

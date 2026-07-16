import type { ReactNode } from 'react'
import { motion } from 'motion/react'

function PrismMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2L22 20H2L12 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  )
}

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden bg-neutral-950 px-4">
      <svg
        className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.35]"
        viewBox="0 0 1600 900"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M120 60c80 120-60 180 40 280s220-40 260 80-100 200 20 300"
          stroke="#5e7748"
          strokeWidth="1.5"
        />
        <circle cx="120" cy="60" r="4" fill="#5e7748" />
        <circle cx="420" cy="420" r="4" fill="#5e7748" />
        <path
          d="M1500 80c-60 140 80 160-20 260s-200-20-240 100 120 180-10 280"
          stroke="#5e7748"
          strokeWidth="1.5"
        />
        <circle cx="1500" cy="80" r="4" fill="#5e7748" />
        <circle cx="1260" cy="440" r="4" fill="#5e7748" />
      </svg>

      <div className="absolute left-8 top-8 flex items-center gap-2 text-neutral-200">
        <PrismMark />
        <span className="font-display text-base font-medium">Prism</span>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-[440px] rounded-2xl border border-neutral-800 bg-neutral-900 p-10"
      >
        {children}
      </motion.div>
    </div>
  )
}

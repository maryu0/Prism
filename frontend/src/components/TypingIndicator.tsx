import { motion } from 'motion/react'

const dotVariants = {
  animate: (i: number) => ({
    y: [0, -5, 0],
    transition: {
      duration: 0.9,
      repeat: Infinity,
      delay: i * 0.15,
      ease: 'easeInOut' as const,
    },
  }),
}

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-neutral-900/40 px-4 py-3 backdrop-blur-md">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-[var(--brand)]"
          custom={i}
          variants={dotVariants}
          animate="animate"
        />
      ))}
    </div>
  )
}

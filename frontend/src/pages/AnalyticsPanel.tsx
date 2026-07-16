import { useQuery } from '@tanstack/react-query'
import { motion } from 'motion/react'
import { getKnowledgeGaps, getMyProgress, getTeamProgress } from '../lib/endpoints'
import { useAuthStore } from '../lib/authStore'
import type { TeamMemberProgress } from '../lib/types'

function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest === 0 ? `${hours}h` : `${hours}h ${rest}m`
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'No activity yet'
  const diffMs = Date.now() - new Date(iso).getTime()
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (days <= 0) return 'Today'
  if (days === 1) return 'Yesterday'
  return `${days} days ago`
}

function ProgressBar({ percent }: { percent: number }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-800">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${percent}%` }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="h-full rounded-full bg-[var(--brand)]"
      />
    </div>
  )
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-neutral-500">{label}</p>
      <p className="mt-1 font-mono text-2xl text-white">{value}</p>
    </div>
  )
}

function MyProgressSection() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['my-progress'],
    queryFn: getMyProgress,
    retry: false,
  })

  if (isLoading) {
    return <div className="h-40 animate-pulse rounded-xl border border-neutral-800 bg-neutral-900/40" />
  }

  if (error) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 py-12 text-center">
        <p className="text-sm text-neutral-500">No active learning path yet.</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-6">
      <div className="mb-6 grid grid-cols-3 gap-6">
        <StatRow label="Modules completed" value={`${data.modulesDone} / ${data.modulesTotal}`} />
        <StatRow label="Time invested" value={formatMinutes(data.minutesSpent)} />
        <StatRow label="Time remaining" value={formatMinutes(data.minutesRemaining)} />
      </div>
      <div className="mb-2 flex items-center justify-between text-xs text-neutral-500">
        <span>Overall progress</span>
        <span className="font-mono text-neutral-300">{data.percentComplete}%</span>
      </div>
      <ProgressBar percent={data.percentComplete} />
      <p className="mt-3 text-xs text-neutral-600">
        Last activity: {formatRelativeTime(data.lastCompletedAt)}
      </p>
    </div>
  )
}

function TeamRow({ member }: { member: TeamMemberProgress }) {
  return (
    <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr_1fr] items-center gap-4 border-b border-neutral-800 px-5 py-4 last:border-0">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-white">{member.name}</p>
        <p className="text-xs text-neutral-500">{member.role}</p>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-16">
          <ProgressBar percent={member.percentComplete} />
        </div>
        <span className="font-mono text-xs text-neutral-400">{member.percentComplete}%</span>
      </div>
      <p className="font-mono text-sm text-neutral-300">
        {member.modulesDone} / {member.modulesTotal}
      </p>
      <p className="text-xs text-neutral-500">{formatRelativeTime(member.lastCompletedAt)}</p>
      <div>
        {member.stalled ? (
          <span className="rounded-md bg-red-500/10 px-2 py-1 text-[11px] font-medium text-red-400">
            Stalled
          </span>
        ) : (
          <span className="rounded-md bg-[var(--brand)]/10 px-2 py-1 text-[11px] font-medium text-[var(--brand-text)]">
            On track
          </span>
        )}
      </div>
    </div>
  )
}

function TeamProgressSection() {
  const { data, isLoading } = useQuery({
    queryKey: ['team-progress'],
    queryFn: getTeamProgress,
  })

  if (isLoading) {
    return <div className="h-64 animate-pulse rounded-xl border border-neutral-800 bg-neutral-900/40" />
  }

  if (!data || data.members.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 py-12 text-center">
        <p className="text-sm text-neutral-500">No developers with active learning paths yet.</p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/40">
      <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr_1fr] gap-4 border-b border-neutral-800 px-5 py-3 text-xs uppercase tracking-wide text-neutral-600">
        <span>Developer</span>
        <span>Progress</span>
        <span>Modules</span>
        <span>Last activity</span>
        <span>Status</span>
      </div>
      {data.members.map((member) => (
        <TeamRow key={member.userId} member={member} />
      ))}
    </div>
  )
}

function KnowledgeGapsSection() {
  const { data, isLoading } = useQuery({
    queryKey: ['knowledge-gaps'],
    queryFn: getKnowledgeGaps,
  })

  if (isLoading) {
    return <div className="h-24 animate-pulse rounded-xl border border-neutral-800 bg-neutral-900/40" />
  }

  if (!data || data.gaps.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 py-8 text-center">
        <p className="text-sm text-neutral-500">No knowledge gaps detected.</p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/40">
      {data.gaps.map((gap, i) => (
        <div
          key={i}
          className="flex items-center justify-between gap-4 border-b border-neutral-800 px-5 py-3 last:border-0"
        >
          <div className="min-w-0">
            <p className="truncate font-mono text-sm text-white">{gap.moduleTitle}</p>
            <p className="text-xs text-neutral-500">
              {gap.stalledDeveloperCount} developers stalled, avg {gap.avgDaysStalled} days
            </p>
          </div>
          <span className="shrink-0 rounded-md bg-amber-500/10 px-2 py-1 text-[11px] font-medium text-amber-400">
            Possible gap
          </span>
        </div>
      ))}
    </div>
  )
}

export function AnalyticsPanel() {
  const role = useAuthStore((s) => s.user?.role)
  const isAdmin = role === 'admin'

  return (
    <div className="space-y-8">
      <div>
        <p className="mb-4 text-sm text-neutral-500">Your onboarding progress.</p>
        <MyProgressSection />
      </div>

      {isAdmin && (
        <div>
          <p className="mb-4 text-sm text-neutral-500">Team onboarding progress.</p>
          <TeamProgressSection />
        </div>
      )}

      {isAdmin && (
        <div>
          <p className="mb-4 text-sm text-neutral-500">
            Modules where multiple developers are stuck — worth reviewing docs or pairing.
          </p>
          <KnowledgeGapsSection />
        </div>
      )}
    </div>
  )
}

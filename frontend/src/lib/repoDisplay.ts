import type { RepositoryStatus } from './types'

export const STATUS_META: Record<RepositoryStatus, { label: string; dot: string; text: string }> = {
  pending: { label: 'Pending', dot: 'bg-neutral-500', text: 'text-neutral-400' },
  syncing: { label: 'Syncing', dot: 'bg-amber-400', text: 'text-amber-400' },
  ready: { label: 'Ready', dot: 'bg-[var(--brand)]', text: 'text-[var(--brand-text)]' },
  error: { label: 'Error', dot: 'bg-red-400', text: 'text-red-400' },
}

export function repoName(url: string) {
  const parts = url.replace(/\/+$/, '').split('/')
  return parts.slice(-2).join('/')
}

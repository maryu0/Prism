import { Handle, Position, type NodeProps } from '@xyflow/react'

export type FileNodeData = {
  label: string
  path: string
  language: string
  componentCount: number
  avgComplexity: number
  dimmed?: boolean
}

function complexityColor(avgComplexity: number): string {
  if (avgComplexity >= 40) return 'text-red-400'
  if (avgComplexity >= 15) return 'text-amber-400'
  return 'text-[var(--brand-text)]'
}

export function FileNode({ data }: NodeProps & { data: FileNodeData }) {
  return (
    <div
      className={`min-w-[160px] rounded-lg border border-neutral-800 bg-neutral-900 px-3.5 py-2.5 shadow-md shadow-black/20 transition-all hover:border-[var(--brand)]/50 ${data.dimmed ? 'opacity-30' : 'opacity-100'}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-neutral-700" />
      <p className="truncate font-mono text-xs font-medium text-white">{data.label}</p>
      <p className="mt-1 truncate text-[10px] text-neutral-500">{data.path}</p>
      <div className="mt-1.5 flex items-center gap-2 text-[10px]">
        <span className="text-neutral-600">{data.componentCount} components</span>
        <span className={complexityColor(data.avgComplexity)}>
          {data.avgComplexity.toFixed(0)} avg LOC
        </span>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-neutral-700" />
    </div>
  )
}

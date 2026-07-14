import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import dagre from 'dagre'
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  type NodeMouseHandler,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { getFileComponents, getRepositoryGraph } from '../lib/endpoints'
import { useActiveRepoStore } from '../lib/activeRepoStore'
import { FileNode, type FileNodeData } from '../components/graph/FileNode'
import { FileDetailPanel } from '../components/graph/FileDetailPanel'

const NODE_WIDTH = 180
const NODE_HEIGHT = 70

const nodeTypes = { file: FileNode }

function layoutGraph(nodes: Node<FileNodeData>[], edges: Edge[]) {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'LR', nodesep: 40, ranksep: 90 })
  g.setDefaultEdgeLabel(() => ({}))

  nodes.forEach((node) => g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT }))
  edges.forEach((edge) => g.setEdge(edge.source, edge.target))

  dagre.layout(g)

  return nodes.map((node) => {
    const { x, y } = g.node(node.id)
    return { ...node, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } }
  })
}

export function LineageGraphPanel() {
  const activeRepositoryId = useActiveRepoStore((s) => s.activeRepositoryId)
  const { data, isLoading, error } = useQuery({
    queryKey: ['repository-graph', activeRepositoryId],
    queryFn: () => getRepositoryGraph(activeRepositoryId as string),
    enabled: !!activeRepositoryId,
  })

  const [selectedNode, setSelectedNode] = useState<FileNodeData & { id: string } | null>(null)
  const { data: fileComponents, isLoading: isLoadingComponents } = useQuery({
    queryKey: ['file-components', activeRepositoryId, selectedNode?.id],
    queryFn: () => getFileComponents(activeRepositoryId as string, selectedNode!.id),
    enabled: !!activeRepositoryId && !!selectedNode,
  })

  const handleNodeClick: NodeMouseHandler<Node<FileNodeData>> = (_e, node) => {
    setSelectedNode({ id: node.id, ...node.data })
  }

  const [layoutedNodes, setLayoutedNodes] = useState<Node<FileNodeData>[]>([])
  const edges: Edge[] = useMemo(
    () =>
      (data?.edges ?? []).map((e, i) => ({
        id: `${e.source}-${e.target}-${i}`,
        source: e.source,
        target: e.target,
        animated: false,
        style: { stroke: '#404040' },
      })),
    [data],
  )

  useEffect(() => {
    if (!data) {
      setLayoutedNodes([])
      return
    }
    const rawNodes: Node<FileNodeData>[] = data.nodes.map((n) => ({
      id: n.id,
      type: 'file',
      position: { x: 0, y: 0 },
      data: {
        label: n.label,
        path: n.path,
        language: n.language,
        componentCount: n.componentCount,
        avgComplexity: n.avgComplexity,
      },
    }))
    setLayoutedNodes(layoutGraph(rawNodes, edges))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  if (!activeRepositoryId) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 py-16 text-center">
        <p className="text-sm text-neutral-500">
          Select a repository from the sidebar to view its lineage graph.
        </p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-12rem)] items-center justify-center">
        <p className="text-sm text-neutral-500">Loading graph…</p>
      </div>
    )
  }

  if (error) {
    return <p className="text-sm text-red-400">Could not load the lineage graph.</p>
  }

  if (data && data.nodes.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 py-16 text-center">
        <p className="text-sm text-neutral-500">No files indexed for this repository yet.</p>
      </div>
    )
  }

  return (
    <div className="relative flex h-[calc(100vh-12rem)] gap-4">
      <div className="flex-1 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-950">
        <ReactFlow
          nodes={layoutedNodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={handleNodeClick}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#262626" gap={20} />
          <Controls />
        </ReactFlow>
        {data?.truncated && (
          <p className="absolute bottom-3 right-3 text-[11px] text-neutral-600">
            Showing first {data.nodes.length} files
          </p>
        )}
      </div>
      {selectedNode && (
        <FileDetailPanel
          node={selectedNode}
          components={fileComponents?.components}
          isLoading={isLoadingComponents}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import dagre from 'dagre'
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  useReactFlow,
  type Node,
  type Edge,
  type NodeMouseHandler,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { getFileComponents, getRepositoryGraph } from '../lib/endpoints'
import { useActiveRepoStore } from '../lib/activeRepoStore'
import { useWorkspaceIntentStore } from '../lib/workspaceIntentStore'
import { FileNode, type FileNodeData } from '../components/graph/FileNode'
import { FileDetailPanel } from '../components/graph/FileDetailPanel'

const NODE_WIDTH = 180
const NODE_HEIGHT = 70
const GRID_GAP_X = 40
const GRID_GAP_Y = 24
const GRID_COLUMNS = 6

const nodeTypes = { file: FileNode }
const READABLE_ZOOM = 0.85

// A dense graph's dagre layout is often far larger than any viewport, so
// letting fitView shrink to fit everything makes labels unreadable. Instead
// we center on the graph's top-left cluster at a fixed, legible zoom — the
// minimap and pan/zoom controls handle reaching the rest.
function InitialViewport({ nodes }: { nodes: Node<FileNodeData>[] }) {
  const { setViewport } = useReactFlow()

  useEffect(() => {
    if (nodes.length === 0) return
    const minX = Math.min(...nodes.map((n) => n.position.x))
    const minY = Math.min(...nodes.map((n) => n.position.y))
    setViewport({ x: -minX * READABLE_ZOOM + 40, y: -minY * READABLE_ZOOM + 40, zoom: READABLE_ZOOM })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes])

  return null
}

function layoutGraph(nodes: Node<FileNodeData>[], edges: Edge[]) {
  const connectedIds = new Set(edges.flatMap((e) => [e.source, e.target]))
  const connectedNodes = nodes.filter((n) => connectedIds.has(n.id))
  const isolatedNodes = nodes.filter((n) => !connectedIds.has(n.id))

  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'LR', nodesep: 40, ranksep: 90 })
  g.setDefaultEdgeLabel(() => ({}))

  connectedNodes.forEach((node) => g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT }))
  edges.forEach((edge) => g.setEdge(edge.source, edge.target))
  dagre.layout(g)

  const laidOutConnected = connectedNodes.map((node) => {
    const { x, y } = g.node(node.id)
    return { ...node, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } }
  })

  // Nodes with no import edges (common for repos indexed before import
  // resolution existed, or that genuinely have few cross-file imports) are
  // placed in a grid below the dependency graph rather than stacked in a
  // single dagre column, which for dozens of isolated files produces a
  // column far taller than any viewport can fit even at minimum zoom.
  const connectedBottom = laidOutConnected.length
    ? Math.max(...laidOutConnected.map((n) => n.position.y)) + NODE_HEIGHT + 60
    : 0
  const laidOutIsolated = isolatedNodes.map((node, i) => ({
    ...node,
    position: {
      x: (i % GRID_COLUMNS) * (NODE_WIDTH + GRID_GAP_X),
      y: connectedBottom + Math.floor(i / GRID_COLUMNS) * (NODE_HEIGHT + GRID_GAP_Y),
    },
  }))

  return [...laidOutConnected, ...laidOutIsolated]
}

export function LineageGraphPanel() {
  return (
    <ReactFlowProvider>
      <LineageGraphPanelInner />
    </ReactFlowProvider>
  )
}

function LineageGraphPanelInner() {
  const activeRepositoryId = useActiveRepoStore((s) => s.activeRepositoryId)
  const { data, isLoading, error } = useQuery({
    queryKey: ['repository-graph', activeRepositoryId],
    queryFn: () => getRepositoryGraph(activeRepositoryId as string),
    enabled: !!activeRepositoryId,
  })

  const [selectedNode, setSelectedNode] = useState<FileNodeData & { id: string } | null>(null)
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)
  const { data: fileComponents, isLoading: isLoadingComponents } = useQuery({
    queryKey: ['file-components', activeRepositoryId, selectedNode?.id],
    queryFn: () => getFileComponents(activeRepositoryId as string, selectedNode!.id),
    enabled: !!activeRepositoryId && !!selectedNode,
  })

  const handleNodeClick: NodeMouseHandler<Node<FileNodeData>> = (_e, node) => {
    setSelectedNode({ id: node.id, ...node.data })
  }

  // Highlighting on hover/selection rather than showing every edge at full
  // opacity all the time — with 100+ files, a dense unhighlighted edge mesh
  // reads as noise rather than structure.
  const focusedNodeId = hoveredNodeId ?? selectedNode?.id ?? null

  const [layoutedNodes, setLayoutedNodes] = useState<Node<FileNodeData>[]>([])
  const rawEdges: Edge[] = useMemo(
    () =>
      (data?.edges ?? []).map((e, i) => ({
        id: `${e.source}-${e.target}-${i}`,
        source: e.source,
        target: e.target,
        animated: false,
      })),
    [data],
  )

  const edges: Edge[] = useMemo(() => {
    if (!focusedNodeId) {
      return rawEdges.map((e) => ({ ...e, style: { stroke: '#333333', strokeWidth: 1 }, zIndex: 0 }))
    }
    return rawEdges.map((e) => {
      const isFocused = e.source === focusedNodeId || e.target === focusedNodeId
      return {
        ...e,
        style: isFocused
          ? { stroke: '#a8c283', strokeWidth: 1.75 }
          : { stroke: '#232323', strokeWidth: 1 },
        zIndex: isFocused ? 10 : 0,
      }
    })
  }, [rawEdges, focusedNodeId])

  const nodesWithFocusState: Node<FileNodeData>[] = useMemo(
    () =>
      layoutedNodes.map((n) => ({
        ...n,
        data: { ...n.data, dimmed: focusedNodeId != null && n.id !== focusedNodeId },
      })),
    [layoutedNodes, focusedNodeId],
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
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      data: {
        label: n.label,
        path: n.path,
        language: n.language,
        componentCount: n.componentCount,
        avgComplexity: n.avgComplexity,
      },
    }))
    setLayoutedNodes(layoutGraph(rawNodes, rawEdges))

    const focusFileId = useWorkspaceIntentStore.getState().consumeFocusFileId()
    if (focusFileId) {
      const focusNode = data.nodes.find((n) => n.id === focusFileId)
      if (focusNode) {
        setSelectedNode({
          id: focusNode.id,
          label: focusNode.label,
          path: focusNode.path,
          language: focusNode.language,
          componentCount: focusNode.componentCount,
          avgComplexity: focusNode.avgComplexity,
        })
      }
    }
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
          nodes={nodesWithFocusState}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={handleNodeClick}
          onNodeMouseEnter={(_e, node) => setHoveredNodeId(node.id)}
          onNodeMouseLeave={() => setHoveredNodeId(null)}
          minZoom={0.05}
          maxZoom={1.5}
          proOptions={{ hideAttribution: true }}
        >
          <InitialViewport nodes={layoutedNodes} />
          <Background color="#262626" gap={20} />
          <Controls />
          <MiniMap
            pannable
            zoomable
            bgColor="#0a0a0a"
            maskColor="rgba(255,255,255,0.06)"
            nodeColor="#6d8955"
            nodeStrokeWidth={0}
          />
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

import type { Role } from './authStore'

export type MeResponse = {
  id: string
  email: string
  name: string
  role: Role
  workspaceId: string
}

export type RepositoryStatus = 'pending' | 'syncing' | 'ready' | 'error'

export type Repository = {
  id: string
  githubUrl: string
  defaultBranch: string
  status: RepositoryStatus
  lastSyncedAt: string | null
  languageStats: Record<string, number>
  locCount: number
}

export type RepositoryStatusResponse = {
  status: RepositoryStatus
  jobStatus: string | null
  stats: Record<string, unknown>
  error: string | null
}

export type SearchResult = {
  id: string
  repositoryId: string
  filePath: string
  name: string
  type: string
  startLine: number
  endLine: number
  similarity: number
}

export type Citation = {
  name: string
  type: string
  filePath: string
  startLine: number
  endLine: number
}

export type AskResponse = {
  answer: string
  citations: Citation[]
}

export type GraphNode = {
  id: string
  label: string
  path: string
  language: string
  componentCount: number
  avgComplexity: number
}

export type GraphEdge = {
  source: string
  target: string
  type: string
}

export type RepositoryGraphResponse = {
  repositoryId: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  truncated: boolean
}

export type FileComponent = {
  name: string
  type: string
  startLine: number
  endLine: number
  complexityScore: number
}

export type FileComponentsResponse = {
  fileId: string
  components: FileComponent[]
}

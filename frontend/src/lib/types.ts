import type { Role } from './authStore'

export type MeResponse = {
  id: string
  email: string
  name: string
  role: Role
  workspaceId: string
  assignedRepositoryId: string | null
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

export type MyProgress = {
  pathId: string
  modulesDone: number
  modulesTotal: number
  percentComplete: number
  minutesSpent: number
  minutesRemaining: number
  lastCompletedAt: string | null
}

export type TeamMemberProgress = {
  userId: string
  name: string
  role: string
  repositoryId: string
  modulesDone: number
  modulesTotal: number
  percentComplete: number
  lastCompletedAt: string | null
  stalled: boolean
}

export type TeamProgressResponse = {
  members: TeamMemberProgress[]
}

export type InviteResponse = {
  inviteUrl: string
  expiresAt: string
}

export type LearningPathStatus = 'active' | 'completed' | 'abandoned'

export type LearningPath = {
  id: string
  developerProfileId: string
  repositoryId: string
  status: LearningPathStatus
  estimatedDurationMinutes: number
  adaptedCount: number
  generatedAt: string
}

export type LearningModuleStatus = 'locked' | 'available' | 'done'

export type LearningModule = {
  id: string
  pathId: string
  title: string
  description: string
  type: string
  targetEntityIds: string[]
  order: number
  prerequisites: string[]
  status: LearningModuleStatus
  estimatedMinutes: number
  completedAt: string | null
  unlockedAt: string | null
}

export type CompleteModuleResponse = {
  module: LearningModule
  unlockedModuleIds: string[]
}

export type AuditLogEntry = {
  actorId: string
  action: string
  targetType: string
  targetId: string
  timestamp: string
}

export type AuditLogResponse = {
  entries: AuditLogEntry[]
}

export type KnowledgeGap = {
  repositoryId: string
  moduleTitle: string
  stalledDeveloperCount: number
  avgDaysStalled: number
}

export type KnowledgeGapsResponse = {
  gaps: KnowledgeGap[]
}

export type NotificationType = 'module_completed' | 'path_completed' | 'knowledge_gap'

export type Notification = {
  id: string
  type: NotificationType
  message: string
  read: boolean
  createdAt: string
}

export type NotificationListResponse = {
  notifications: Notification[]
  unreadCount: number
}

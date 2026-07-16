import { api } from './api'
import type {
  AskResponse,
  AuditLogResponse,
  CompleteModuleResponse,
  FileComponentsResponse,
  InviteResponse,
  KnowledgeGapsResponse,
  LearningModule,
  LearningPath,
  MeResponse,
  MyProgress,
  Notification,
  NotificationListResponse,
  Repository,
  RepositoryGraphResponse,
  RepositoryStatusResponse,
  SearchResult,
  TeamProgressResponse,
} from './types'
import type { Role } from './authStore'

export async function login(email: string, password: string) {
  const res = await api.post<{ accessToken: string }>('/auth/login', {
    email,
    password,
  })
  return res.data.accessToken
}

export async function register(params: {
  email: string
  password: string
  name: string
  inviteToken?: string
  experienceLevel?: 'junior' | 'mid' | 'senior'
}) {
  await api.post('/auth/register', {
    email: params.email,
    password: params.password,
    name: params.name,
    inviteToken: params.inviteToken,
    experienceLevel: params.experienceLevel,
  })
}

export async function logout() {
  await api.post('/auth/logout')
}

export async function fetchMe() {
  const res = await api.get<MeResponse>('/auth/me')
  return res.data
}

export async function listRepositories() {
  const res = await api.get<Repository[]>('/repositories')
  return res.data
}

export async function connectRepository(params: {
  githubUrl: string
  accessToken?: string
  defaultBranch?: string
}) {
  const res = await api.post<Repository>('/repositories', {
    githubUrl: params.githubUrl,
    accessToken: params.accessToken,
    defaultBranch: params.defaultBranch ?? 'main',
  })
  return res.data
}

export async function getRepositoryStatus(repositoryId: string) {
  const res = await api.get<RepositoryStatusResponse>(
    `/repositories/${repositoryId}/status`,
  )
  return res.data
}

export async function syncRepository(repositoryId: string) {
  await api.post(`/repositories/${repositoryId}/sync`)
}

export async function getRepositoryGraph(repositoryId: string) {
  const res = await api.get<RepositoryGraphResponse>(`/repositories/${repositoryId}/graph`)
  return res.data
}

export async function getFileComponents(repositoryId: string, fileId: string) {
  const res = await api.get<FileComponentsResponse>(
    `/repositories/${repositoryId}/graph/file-components`,
    { params: { file_id: fileId } },
  )
  return res.data
}

export async function searchCode(query: string, limit = 10) {
  const res = await api.get<SearchResult[]>('/search', {
    params: { q: query, limit },
  })
  return res.data
}

export async function askQuestion(question: string) {
  const res = await api.post<AskResponse>('/chat/ask', { question })
  return res.data
}

export async function getMyProgress() {
  const res = await api.get<MyProgress>('/analytics/me')
  return res.data
}

export async function getTeamProgress() {
  const res = await api.get<TeamProgressResponse>('/analytics/team')
  return res.data
}

export async function inviteDeveloper(params: {
  workspaceId: string
  email: string
  role: Role
  assignedRepositoryId: string
}) {
  const res = await api.post<InviteResponse>(`/workspaces/${params.workspaceId}/invite`, {
    email: params.email,
    role: params.role,
    assignedRepositoryId: params.assignedRepositoryId,
  })
  return res.data
}

export async function generateLearningPath(developerProfileId: string) {
  const res = await api.post<LearningPath>('/learning-paths/generate', {
    developerProfileId,
  })
  return res.data
}

export async function getMyLearningPath() {
  const res = await api.get<LearningPath>('/learning-paths/me')
  return res.data
}

export async function listLearningModules(pathId: string) {
  const res = await api.get<LearningModule[]>(`/learning-paths/${pathId}/modules`)
  return res.data
}

export async function completeLearningModule(moduleId: string) {
  const res = await api.post<CompleteModuleResponse>(
    `/learning-paths/modules/${moduleId}/complete`,
  )
  return res.data
}

export async function getAuditLog() {
  const res = await api.get<AuditLogResponse>('/audit-log')
  return res.data
}

export async function getKnowledgeGaps() {
  const res = await api.get<KnowledgeGapsResponse>('/analytics/knowledge-gaps')
  return res.data
}

export async function listNotifications() {
  const res = await api.get<NotificationListResponse>('/notifications')
  return res.data
}

export async function markNotificationRead(notificationId: string) {
  const res = await api.post<Notification>(`/notifications/${notificationId}/read`)
  return res.data
}

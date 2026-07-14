import { api } from './api'
import type {
  AskResponse,
  FileComponentsResponse,
  MeResponse,
  Repository,
  RepositoryGraphResponse,
  RepositoryStatusResponse,
  SearchResult,
} from './types'

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
}) {
  await api.post('/auth/register', {
    email: params.email,
    password: params.password,
    name: params.name,
    inviteToken: params.inviteToken,
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

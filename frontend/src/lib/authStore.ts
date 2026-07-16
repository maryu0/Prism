import { create } from 'zustand'
import { useActiveRepoStore } from './activeRepoStore'

export type Role = 'admin' | 'senior' | 'developer'

export type CurrentUser = {
  id: string
  email: string
  name: string
  role: Role
  workspaceId: string
  assignedRepositoryId: string | null
}

type AuthState = {
  accessToken: string | null
  user: CurrentUser | null
  setAccessToken: (token: string) => void
  setUser: (user: CurrentUser) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setAccessToken: (accessToken) => set({ accessToken }),
  setUser: (user) => set({ user }),
  clear: () => set({ accessToken: null, user: null }),
}))

/** Single entry point for "we just learned who the user is" — called from
 * LoginPage, SignupPage, and ProtectedRoute's session-restore path, so a
 * developer's assigned repository auto-scopes the workspace regardless of
 * which of those three ways they arrived at a valid session. */
export function applyUser(me: CurrentUser): void {
  useAuthStore.getState().setUser(me)
  if (me.role === 'developer' && me.assignedRepositoryId) {
    useActiveRepoStore.getState().setActiveRepositoryId(me.assignedRepositoryId)
  }
}

import { create } from 'zustand'

export type Role = 'admin' | 'senior' | 'developer'

export type CurrentUser = {
  id: string
  email: string
  name: string
  role: Role
  workspaceId: string
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

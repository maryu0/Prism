import { create } from 'zustand'

type ActiveRepoState = {
  activeRepositoryId: string | null
  setActiveRepositoryId: (id: string | null) => void
}

export const useActiveRepoStore = create<ActiveRepoState>((set) => ({
  activeRepositoryId: null,
  setActiveRepositoryId: (activeRepositoryId) => set({ activeRepositoryId }),
}))

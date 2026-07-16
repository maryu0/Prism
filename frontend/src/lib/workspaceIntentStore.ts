import { create } from 'zustand'

/** One-shot cross-tab intents: "open Chat with this question pre-filled",
 * "open Lineage Graph focused on this file". Consumed once by the target
 * tab and cleared, so revisiting the tab later doesn't reapply stale intent. */
type WorkspaceIntentState = {
  prefillQuestion: string | null
  focusFileId: string | null
  setPrefillQuestion: (question: string) => void
  consumePrefillQuestion: () => string | null
  setFocusFileId: (fileId: string) => void
  consumeFocusFileId: () => string | null
}

export const useWorkspaceIntentStore = create<WorkspaceIntentState>((set, get) => ({
  prefillQuestion: null,
  focusFileId: null,
  setPrefillQuestion: (prefillQuestion) => set({ prefillQuestion }),
  consumePrefillQuestion: () => {
    const value = get().prefillQuestion
    set({ prefillQuestion: null })
    return value
  },
  setFocusFileId: (focusFileId) => set({ focusFileId }),
  consumeFocusFileId: () => {
    const value = get().focusFileId
    set({ focusFileId: null })
    return value
  },
}))

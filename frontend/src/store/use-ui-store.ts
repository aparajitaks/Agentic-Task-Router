/**
 * frontend/src/store/use-ui-store.ts
 *
 * WHY IT EXISTS:
 * Global UI state (like whether the sidebar is collapsed or expanded) needs to be
 * accessible across different disconnected components (e.g., Sidebar, Header, Page Layout).
 *
 * WHAT IT DOES:
 * Uses Zustand to create a tiny, fast, and scalable global state store.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Purely frontend state; does not interact with the backend API.
 */

import { create } from "zustand";

interface UiState {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (isOpen: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  isSidebarOpen: true,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (isOpen: boolean) => set({ isSidebarOpen: isOpen }),
}));

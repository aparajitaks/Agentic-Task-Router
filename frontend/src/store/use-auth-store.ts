/**
 * frontend/src/store/use-auth-store.ts
 *
 * WHY IT EXISTS:
 * To track the user's authentication status and Gmail integration state
 * across the entire application. This prevents unnecessary API calls
 * and allows for conditional rendering of the onboarding experience.
 *
 * WHAT IT DOES:
 * - Stores user information (mocked).
 * - Stores Gmail connection status.
 * - Stores "Demo Mode" toggle state.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthState {
  user: User | null;
  isGmailConnected: boolean;
  isDemoMode: boolean;
  isOnboardingComplete: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  setGmailConnected: (connected: boolean) => void;
  setDemoMode: (isDemo: boolean) => void;
  setOnboardingComplete: (complete: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: {
        id: "demo_user_123",
        email: "demo@example.com",
        name: "Demo User",
      },
      isGmailConnected: false,
      isDemoMode: false,
      isOnboardingComplete: false,

      setUser: (user) => set({ user }),
      setGmailConnected: (connected) => set({ isGmailConnected: connected }),
      setDemoMode: (isDemo) => set({ isDemoMode: isDemo }),
      setOnboardingComplete: (complete) => set({ isOnboardingComplete: complete }),
      
      logout: () => set({ 
        user: null, 
        isGmailConnected: false, 
        isDemoMode: false, 
        isOnboardingComplete: false 
      }),
    }),
    {
      name: "auth-storage", // local storage key
    }
  )
);

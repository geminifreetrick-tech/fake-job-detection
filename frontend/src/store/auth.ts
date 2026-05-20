import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setTokens: (a: string, r: string) => void
  setUser: (u: User | null) => void
  logout: () => void
}

export const authStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setTokens: (a, r) => set({ accessToken: a, refreshToken: r }),
      setUser: (u) => set({ user: u }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: 'fjd-auth' },
  ),
)

export const useAuth = authStore

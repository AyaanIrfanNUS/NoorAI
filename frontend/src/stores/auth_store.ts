/**
 * Global authentication state store.
 *
 * Holds the current user, access token, and authentication status. Tokens
 * are kept in memory only, never persisted to localStorage, since
 * localStorage is readable by any script on the page and would be exposed
 * in the event of an XSS vulnerability.
 */
import { create } from "zustand";
import { api } from "../services/api";
import type { User, AuthTokens } from "../types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshTokenValue: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshTokenValue: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const { data } = await api.post<AuthTokens>("/auth/login", {
        email,
        password,
      });

      set({
        accessToken: data.access_token,
        refreshTokenValue: data.refresh_token,
      });

      const { data: user } = await api.get<User>("/auth/me");

      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // Logout proceeds regardless of whether the server call succeeds -
      // the client-side session is cleared either way.
    } finally {
      set({
        user: null,
        accessToken: null,
        refreshTokenValue: null,
        isAuthenticated: false,
      });
      window.location.href = "/login";
    }
  },

  refreshToken: async () => {
    const currentRefreshToken = get().refreshTokenValue;
    if (!currentRefreshToken) {
      return null;
    }

    const { data } = await api.post<AuthTokens>("/auth/refresh", {
      refresh_token: currentRefreshToken,
    });

    set({
      accessToken: data.access_token,
      refreshTokenValue: data.refresh_token,
    });

    return data.access_token;
  },

  setUser: (user) => set({ user }),
}));
/**
 * Global authentication state store.
 *
 * Holds the current user, access token, and authentication status.
 * Tokens are kept in memory by default. If remember_me was set at
 * login, the refresh token is additionally persisted to localStorage
 * so the session can be silently restored after a page reload -
 * accepting the tradeoff that a token in localStorage is readable by
 * any script on the page in the event of an XSS vulnerability.
 */
import { create } from "zustand";
import * as authService from "../services/auth_service";
import type { AuthTokens, User } from "../types";

const REMEMBER_ME_KEY = "noorai_refresh_token";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshTokenValue: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitializing: boolean;
  rememberMe: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
  setUser: (user: User) => void;
  setSession: (user: User, tokens: AuthTokens, rememberMe?: boolean) => void;
  restoreSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshTokenValue: null,
  isAuthenticated: false,
  isLoading: false,
  isInitializing: true,
  rememberMe: false,

  login: async (email, password, rememberMe = false) => {
    set({ isLoading: true });
    try {
      const tokens = await authService.login(email, password);

      // Store tokens immediately, before fetching the user - the
      // request interceptor needs an access token already in the
      // store to attach a valid Authorization header to /auth/me.
      set({ accessToken: tokens.access_token, refreshTokenValue: tokens.refresh_token });

      const user = await authService.getMe();
      get().setSession(user, tokens, rememberMe);
      set({ isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await authService.logout();
    } catch {
      // Logout proceeds regardless of whether the server call succeeds -
      // the client-side session is cleared either way.
    } finally {
      localStorage.removeItem(REMEMBER_ME_KEY);
      set({
        user: null,
        accessToken: null,
        refreshTokenValue: null,
        isAuthenticated: false,
        rememberMe: false,
      });
      window.location.href = "/login";
    }
  },

  refreshToken: async () => {
    const currentRefreshToken = get().refreshTokenValue;
    if (!currentRefreshToken) {
      return null;
    }

    const tokens = await authService.refreshAccessToken(currentRefreshToken);

    if (get().rememberMe) {
      localStorage.setItem(REMEMBER_ME_KEY, tokens.refresh_token);
    }

    set({
      accessToken: tokens.access_token,
      refreshTokenValue: tokens.refresh_token,
    });

    return tokens.access_token;
  },

  setUser: (user) => set({ user }),

  // Writes a user and token pair into the store directly, without a
  // login network call - used by registration (which already returns
  // both in one response) and by session restoration on app startup.
  setSession: (user, tokens, rememberMe) => {
    const remember = rememberMe ?? get().rememberMe;

    if (remember) {
      localStorage.setItem(REMEMBER_ME_KEY, tokens.refresh_token);
    } else {
      localStorage.removeItem(REMEMBER_ME_KEY);
    }

    set({
      user,
      accessToken: tokens.access_token,
      refreshTokenValue: tokens.refresh_token,
      isAuthenticated: true,
      rememberMe: remember,
    });
  },

  // Called once on app startup. If a remembered refresh token exists,
  // silently exchanges it for a fresh session; clears it if it's no
  // longer valid. Always resolves - never throws - so app startup is
  // never blocked by a failed restore attempt.
  restoreSession: async () => {
    const savedRefreshToken = localStorage.getItem(REMEMBER_ME_KEY);

    if (!savedRefreshToken) {
      set({ isInitializing: false });
      return;
    }

    try {
      const tokens = await authService.refreshAccessToken(savedRefreshToken);

      // Same ordering fix as login() - store the token before using
      // it to call /auth/me.
      set({ accessToken: tokens.access_token, refreshTokenValue: tokens.refresh_token });

      const user = await authService.getMe();
      get().setSession(user, tokens, true);
    } catch {
      localStorage.removeItem(REMEMBER_ME_KEY);
    } finally {
      set({ isInitializing: false });
    }
  },
}));
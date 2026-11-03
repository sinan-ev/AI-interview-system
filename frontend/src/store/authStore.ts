import { create } from 'zustand';
import { UserResponse, TokenResponse } from '../types';

interface AuthState {
  user: UserResponse | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (tokenData: TokenResponse) => void;
  setUser: (user: UserResponse) => void;
  setTokens: (access: string, refresh: string) => void;
  logout: () => void;
  initializeAuth: () => void;
}

const ACCESS_TOKEN_KEY = 'ai_interview_access_token';
const REFRESH_TOKEN_KEY = 'ai_interview_refresh_token';
const USER_KEY = 'ai_interview_user';

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (tokenData: TokenResponse) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokenData.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokenData.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(tokenData.user));

    set({
      user: tokenData.user,
      accessToken: tokenData.access_token,
      refreshToken: tokenData.refresh_token,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  setUser: (user: UserResponse) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ user });
  },

  setTokens: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    set({
      accessToken: access,
      refreshToken: refresh,
      isAuthenticated: true,
    });
  },

  logout: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  initializeAuth: () => {
    try {
      const access = localStorage.getItem(ACCESS_TOKEN_KEY);
      const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
      const userJson = localStorage.getItem(USER_KEY);

      if (access && refresh && userJson) {
        const user = JSON.parse(userJson) as UserResponse;
        set({
          user,
          accessToken: access,
          refreshToken: refresh,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    } catch {
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },
}));

import { apiClient } from './client';
import {
  APIResponse,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  RefreshTokenRequest,
} from '../types';

export const authApi = {
  register: async (payload: RegisterRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<APIResponse<TokenResponse>>('/auth/register', payload);
    return response.data.data;
  },

  login: async (payload: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<APIResponse<TokenResponse>>('/auth/login', payload);
    return response.data.data;
  },

  refreshToken: async (payload: RefreshTokenRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<APIResponse<TokenResponse>>('/auth/refresh', payload);
    return response.data.data;
  },

  logout: async (refreshToken?: string): Promise<void> => {
    await apiClient.post('/auth/logout', { refresh_token: refreshToken });
  },
};

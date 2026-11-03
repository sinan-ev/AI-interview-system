import { apiClient } from './client';
import { APIResponse, UserResponse, UserUpdate } from '../types';

export const usersApi = {
  getProfile: async (): Promise<UserResponse> => {
    const response = await apiClient.get<APIResponse<UserResponse>>('/users/me');
    return response.data.data;
  },

  updateProfile: async (payload: UserUpdate): Promise<UserResponse> => {
    const response = await apiClient.put<APIResponse<UserResponse>>('/users/me', payload);
    return response.data.data;
  },
};

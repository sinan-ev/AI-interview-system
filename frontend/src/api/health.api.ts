import { apiClient } from './client';
import { APIResponse, HealthStatus } from '../types';

export const healthApi = {
  checkHealth: async (): Promise<HealthStatus> => {
    const response = await apiClient.get<APIResponse<HealthStatus>>('/health');
    return response.data.data;
  },
};

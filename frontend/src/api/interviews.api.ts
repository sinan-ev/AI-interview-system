import { apiClient } from './client';
import {
  APIResponse,
  InterviewCreateRequest,
  InterviewDetailResponse,
  InterviewListResponse,
  InterviewResponse,
  QuestionResponse,
} from '../types';

export const interviewsApi = {
  createInterview: async (payload: InterviewCreateRequest): Promise<InterviewResponse> => {
    const response = await apiClient.post<APIResponse<InterviewResponse>>('/interviews', payload);
    return response.data.data;
  },

  listInterviews: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<InterviewListResponse> => {
    const response = await apiClient.get<APIResponse<InterviewListResponse>>('/interviews', {
      params: {
        page: params?.page ?? 1,
        page_size: params?.page_size ?? 20,
        status: params?.status,
      },
    });
    return response.data.data;
  },

  getInterviewDetail: async (interviewId: string): Promise<InterviewDetailResponse> => {
    const response = await apiClient.get<APIResponse<InterviewDetailResponse>>(
      `/interviews/${interviewId}`
    );
    return response.data.data;
  },

  startInterview: async (interviewId: string): Promise<InterviewResponse> => {
    const response = await apiClient.post<APIResponse<InterviewResponse>>(
      `/interviews/${interviewId}/start`
    );
    return response.data.data;
  },

  getCurrentQuestion: async (interviewId: string): Promise<QuestionResponse> => {
    const response = await apiClient.get<APIResponse<QuestionResponse>>(
      `/interviews/${interviewId}/current-question`
    );
    return response.data.data;
  },

  completeInterview: async (interviewId: string): Promise<InterviewResponse> => {
    const response = await apiClient.post<APIResponse<InterviewResponse>>(
      `/interviews/${interviewId}/complete`
    );
    return response.data.data;
  },
};

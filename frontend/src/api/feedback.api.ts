import { apiClient } from './client';
import {
  APIResponse,
  EvaluationResponse,
  InterviewFeedbackResponse,
  UserPerformanceProfile,
} from '../types';

export const feedbackApi = {
  getInterviewFeedback: async (interviewId: string): Promise<InterviewFeedbackResponse> => {
    const response = await apiClient.get<APIResponse<InterviewFeedbackResponse>>(
      `/feedback/interview/${interviewId}`
    );
    return response.data.data;
  },

  getAnswerEvaluation: async (answerId: string): Promise<EvaluationResponse> => {
    const response = await apiClient.get<APIResponse<EvaluationResponse>>(
      `/feedback/answer/${answerId}`
    );
    return response.data.data;
  },

  getUserPerformanceProfile: async (userId: string): Promise<UserPerformanceProfile> => {
    const response = await apiClient.get<APIResponse<UserPerformanceProfile>>(
      `/feedback/profile/${userId}`
    );
    return response.data.data;
  },
};

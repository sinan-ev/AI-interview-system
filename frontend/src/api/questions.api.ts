import { apiClient } from './client';
import { APIResponse, QuestionResponse } from '../types';

export const questionsApi = {
  getQuestion: async (questionId: string): Promise<QuestionResponse> => {
    const response = await apiClient.get<APIResponse<QuestionResponse>>(`/questions/${questionId}`);
    return response.data.data;
  },
};

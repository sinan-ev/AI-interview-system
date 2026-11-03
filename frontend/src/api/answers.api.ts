import { apiClient } from './client';
import { APIResponse, AnswerResponse, TextAnswerSubmission } from '../types';

export const answersApi = {
  submitTextAnswer: async (
    interviewId: string,
    payload: TextAnswerSubmission
  ): Promise<AnswerResponse> => {
    const response = await apiClient.post<APIResponse<AnswerResponse>>(
      `/interviews/${interviewId}/answers`,
      payload
    );
    return response.data.data;
  },

  submitVoiceAnswer: async (
    interviewId: string,
    data: {
      questionId: string;
      audioBlob: Blob;
      filename?: string;
      durationSeconds?: number;
      transcript?: string;
    }
  ): Promise<AnswerResponse> => {
    const formData = new FormData();
    formData.append('question_id', data.questionId);
    formData.append(
      'audio_file',
      data.audioBlob,
      data.filename || 'recording.webm'
    );
    if (data.durationSeconds !== undefined) {
      formData.append('duration_seconds', data.durationSeconds.toString());
    }
    if (data.transcript) {
      formData.append('transcript', data.transcript);
    }

    const response = await apiClient.post<APIResponse<AnswerResponse>>(
      `/interviews/${interviewId}/answers/voice`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data;
  },
};

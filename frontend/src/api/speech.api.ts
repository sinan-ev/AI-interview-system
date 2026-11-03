import { apiClient } from './client';
import {
  APIResponse,
  SpeechFeaturesResponse,
  SpeechTranscriptionResponse,
} from '../types';

export const speechApi = {
  transcribeAudio: async (
    audioBlob: Blob,
    filename = 'audio.webm',
    language?: string
  ): Promise<SpeechTranscriptionResponse> => {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, filename);
    if (language) {
      formData.append('language', language);
    }

    const response = await apiClient.post<APIResponse<SpeechTranscriptionResponse>>(
      '/speech/transcribe',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data;
  },

  analyzeSpeechFeatures: async (
    transcript: string,
    durationSeconds = 60.0
  ): Promise<SpeechFeaturesResponse> => {
    const formData = new FormData();
    formData.append('transcript', transcript);
    formData.append('duration_seconds', durationSeconds.toString());

    const response = await apiClient.post<APIResponse<SpeechFeaturesResponse>>(
      '/speech/analyze',
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

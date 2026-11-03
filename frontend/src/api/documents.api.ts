import { apiClient } from './client';
import {
  APIResponse,
  DocumentItem,
  DocumentListResponse,
  DocumentUploadResponse,
} from '../types';

export const documentsApi = {
  uploadDocument: async (
    file: File,
    title: string,
    description?: string
  ): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) {
      formData.append('description', description);
    }

    const response = await apiClient.post<APIResponse<DocumentUploadResponse>>(
      '/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data;
  },

  listDocuments: async (): Promise<DocumentListResponse> => {
    const response = await apiClient.get<APIResponse<DocumentListResponse>>('/documents');
    return response.data.data;
  },

  getDocument: async (documentId: string): Promise<DocumentItem> => {
    const response = await apiClient.get<APIResponse<DocumentItem>>(`/documents/${documentId}`);
    return response.data.data;
  },

  deleteDocument: async (documentId: string): Promise<{ document_id: string; deleted: boolean }> => {
    const response = await apiClient.delete<
      APIResponse<{ document_id: string; deleted: boolean }>
    >(`/documents/${documentId}`);
    return response.data.data;
  },
};

import { apiClient } from '../client';
import { ApplicationData, DocumentData, ScheduleData, StatementData } from '../types';

// 志望校管理API
export const applicationApi = {
  getApplications: async () => {
    return apiClient.get('/api/v1/applications/');
  },
  getApplication: async (id: string) => {
    return apiClient.get(`/api/v1/applications/${id}/`);
  },
  createApplication: async (data: ApplicationData) => {
    return apiClient.post('/api/v1/applications/', data);
  },
  updateApplication: async (id: string, data: ApplicationData) => {
    return apiClient.put(`/api/v1/applications/${id}/`, data);
  },
  deleteApplication: async (id: string) => {
    return apiClient.delete(`/api/v1/applications/${id}/`);
  },
  addDocument: async (applicationId: string, data: DocumentData) => {
    return apiClient.post(`/api/v1/applications/${applicationId}/documents/`, data);
  },
  updateDocument: async (applicationId: string, documentId: string, data: DocumentData) => {
    return apiClient.put(`/api/v1/applications/${applicationId}/documents/${documentId}/`, data);
  },
  deleteDocument: async (applicationId: string, documentId: string) => {
    return apiClient.delete(`/api/v1/applications/${applicationId}/documents/${documentId}/`);
  },
  addSchedule: async (applicationId: string, data: ScheduleData) => {
    return apiClient.post(`/api/v1/applications/${applicationId}/schedules/`, data);
  },
  updateSchedule: async (applicationId: string, scheduleId: string, data: ScheduleData) => {
    return apiClient.put(`/api/v1/applications/${applicationId}/schedules/${scheduleId}/`, data);
  },
  deleteSchedule: async (applicationId: string, scheduleId: string) => {
    return apiClient.delete(`/api/v1/applications/${applicationId}/schedules/${scheduleId}/`);
  },
  reorderApplications: async (data: { application_order: Record<string, number> }) => {
    return apiClient.put('/api/v1/applications/reorder/', data);
  },
  getStatistics: async () => {
    return apiClient.get('/api/v1/applications/statistics/');
  },
  getDeadlines: async () => {
    return apiClient.get('/api/v1/applications/deadlines/');
  }
};

// 志望理由書管理API
export const statementApi = {
  getStatements: async () => {
    return apiClient.get('/api/v1/statements/');
  },
  getStatement: async (id: string) => {
    return apiClient.get(`/api/v1/statements/${id}/`);
  },
  createStatement: async (data: StatementData) => {
    return apiClient.post('/api/v1/statements/', data);
  },
  updateStatement: async (id: string, data: StatementData) => {
    return apiClient.put(`/api/v1/statements/${id}/`, data);
  },
  deleteStatement: async (id: string) => {
    return apiClient.delete(`/api/v1/statements/${id}/`);
  },
  requestFeedback: async (id: string, data: { message?: string }) => {
    return apiClient.post(`/api/v1/statements/${id}/feedback/request/`, data);
  },
  getFeedback: async (id: string) => {
    return apiClient.get(`/api/v1/statements/${id}/feedback/`);
  },
  provideFeedback: async (id: string, data: { content: string }) => {
    return apiClient.post(`/api/v1/statements/${id}/feedback/`, data);
  },
  improveWithAI: async (id: string) => {
    return apiClient.post(`/api/v1/statements/${id}/ai-improve/`, {});
  },
  getTemplates: async () => {
    return apiClient.get('/api/v1/statements/templates/');
  },
  getExamples: async () => {
    return apiClient.get('/api/v1/statements/examples/');
  }
}; 
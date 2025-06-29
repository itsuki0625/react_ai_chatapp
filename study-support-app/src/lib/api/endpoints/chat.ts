import { AxiosResponse } from 'axios';
import { apiClient } from '../client';
import { ApiResponse, StreamChatMessage, ChatSession } from '../types';
import { ChatTypeValue, ChatSubmitRequest, ChatSession as ChatSessionType } from '@/types/chat';

// チャットAPI
export const chatApi = {
  // チャットメッセージ送信 (ストリーミングなしの通常のPOSTリクエスト)
  sendChatMessage: async (token: string, data: ChatSubmitRequest): Promise<AxiosResponse<any>> => {
    return apiClient.post("/api/v1/chat/", data, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // チャットセッションリスト取得 (アクティブなもの)
  getActiveSessions: async (token: string, chatType: ChatTypeValue): Promise<AxiosResponse<ChatSessionType[]>> => {
    return apiClient.get<ChatSessionType[]>("/api/v1/chat/sessions/", {
      headers: { Authorization: `Bearer ${token}` },
      params: { chat_type: chatType, status: 'ACTIVE' },
    });
  },

  // 特定のチャットセッションのメッセージ履歴取得
  getSessionMessages: async (token: string, sessionId: string): Promise<AxiosResponse<any[]>> => {
    return apiClient.get<any[]>(`/api/v1/chat/sessions/${sessionId}/messages/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // チャットセッションをアーカイブする
  archiveSession: async (token: string, sessionId: string): Promise<AxiosResponse<ChatSessionType>> => {
    return apiClient.patch<ChatSessionType>(`/api/v1/chat/sessions/${sessionId}/archive/`, {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // アーカイブ済みチャットセッションリスト取得
  getArchivedSessions: async (token: string, chatType: ChatTypeValue): Promise<AxiosResponse<ChatSessionType[]>> => {
    return apiClient.get<ChatSessionType[]>("/api/v1/chat/sessions/archived/", {
      headers: { Authorization: `Bearer ${token}` },
      params: { chat_type: chatType },
    });
  },

  // チャットセッションをアーカイブ解除する
  unarchiveSession: async (token: string, sessionId: string): Promise<AxiosResponse<ChatSessionType>> => {
    return apiClient.patch<ChatSessionType>(`/api/v1/chat/sessions/${sessionId}/unarchive/`, {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // セッションタイトル生成 (services/api.tsから統合)
  generateSessionTitle: async (sessionId: string): Promise<{ title: string; session_id: string }> => {
    try {
      const response = await apiClient.patch(`/api/v1/chat/sessions/${sessionId}/generate-title`);
      return response.data;
    } catch (error) {
      console.error(`セッションID: ${sessionId} のタイトル生成に失敗しました:`, error);
      throw error;
    }
  },
}; 
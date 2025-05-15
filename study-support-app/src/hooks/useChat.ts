import { chatApi } from '@/lib/api-client';
import { ChatSubmitRequest, ChatTypeValue } from '@/types/chat';
import { getSession } from 'next-auth/react';

export const useChat = () => {
  const sendMessage = async (message: string, chat_type: ChatTypeValue) => {
    try {
      const session = await getSession();
      if (!session?.user?.accessToken) throw new Error('認証が必要です');
      
      const data: ChatSubmitRequest = {
        message,
        chat_type,
        session_id: null // 新規セッションの場合
      };
      
      const response = await chatApi.sendChatMessage(session.user.accessToken, data);
      return response;
    } catch (error) {
      console.error('チャットメッセージの送信に失敗しました:', error);
      throw error;
    }
  };

  const getChatSessions = async (chat_type: ChatTypeValue) => {
    try {
      const session = await getSession();
      if (!session?.user?.accessToken) throw new Error('認証が必要です');
      
      const response = await chatApi.getActiveSessions(session.user.accessToken, chat_type);
      return response.data;
    } catch (error) {
      console.error('チャットセッション一覧の取得に失敗しました:', error);
      throw error;
    }
  };

  const getSessionMessages = async (sessionId: string) => {
    try {
      const session = await getSession();
      if (!session?.user?.accessToken) throw new Error('認証が必要です');
      
      const response = await chatApi.getSessionMessages(session.user.accessToken, sessionId);
      return response.data;
    } catch (error) {
      console.error('セッションメッセージの取得に失敗しました:', error);
      throw error;
    }
  };

  const archiveSession = async (sessionId: string) => {
    try {
      const session = await getSession();
      if (!session?.user?.accessToken) throw new Error('認証が必要です');
      
      await chatApi.archiveSession(session.user.accessToken, sessionId);
    } catch (error) {
      console.error('セッションのアーカイブに失敗しました:', error);
      throw error;
    }
  };

  const getArchivedSessions = async (chat_type: ChatTypeValue) => {
    try {
      const session = await getSession();
      if (!session?.user?.accessToken) throw new Error('認証が必要です');
      
      const response = await chatApi.getArchivedSessions(session.user.accessToken, chat_type);
      return response.data;
    } catch (error) {
      console.error('アーカイブされたセッション一覧の取得に失敗しました:', error);
      throw error;
    }
  };

  return { 
    sendMessage, 
    getChatSessions,
    getSessionMessages,
    archiveSession,
    getArchivedSessions
  };
};
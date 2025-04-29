import { chatApi } from '@/lib/api-client';

interface StreamResponse {
  newSessionId: string;
}

export const useChat = () => {
  const sendMessage = async (message: string) => {
    try {
      const response = await chatApi.sendMessage(message);
      return response;
    } catch (error) {
      console.error('チャットメッセージの送信に失敗しました:', error);
      throw error;
    }
  };

  const sendStreamMessage = async (
    message: string,
    sessionId: string | undefined,
    type: string,
    onChunk: (content: string) => void,
    onError: (error: unknown) => void
  ): Promise<StreamResponse> => {
    try {
      const response = await chatApi.sendStreamMessage(message, sessionId, type);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is null');
      }

      let sessionIdFromResponse = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.slice(6);
            if (content === '[DONE]') continue;
            
            if (content.includes('session_id:')) {
              const match = content.match(/session_id:([a-zA-Z0-9-]+)/);
              if (match && match[1]) {
                sessionIdFromResponse = match[1];
              }
              continue;
            }
            
            onChunk(content);
          }
        }
      }

      return { newSessionId: sessionIdFromResponse };
    } catch (error) {
      onError(error);
      return { newSessionId: '' };
    }
  };

  const getChatSessions = async () => {
    try {
      const response = await chatApi.getSessions();
      return response.data;
    } catch (error) {
      console.error('チャットセッション一覧の取得に失敗しました:', error);
      throw error;
    }
  };

  const getSessionMessages = async (sessionId: string) => {
    try {
      const response = await chatApi.getSessionMessages(sessionId);
      return response.data;
    } catch (error) {
      console.error('セッションメッセージの取得に失敗しました:', error);
      throw error;
    }
  };

  const archiveSession = async (sessionId: string) => {
    try {
      await chatApi.archiveSession(sessionId);
    } catch (error) {
      console.error('セッションのアーカイブに失敗しました:', error);
      throw error;
    }
  };

  const getArchivedSessions = async () => {
    try {
      const response = await chatApi.getArchivedSessions();
      return response.data;
    } catch (error) {
      console.error('アーカイブされたセッション一覧の取得に失敗しました:', error);
      throw error;
    }
  };

  const getChecklist = async (chatId: string) => {
    try {
      const response = await chatApi.getChecklist(chatId);
      return response.data;
    } catch (error) {
      console.error('チェックリストの取得に失敗しました:', error);
      throw error;
    }
  };

  return { 
    sendMessage, 
    sendStreamMessage,
    getChatSessions,
    getSessionMessages,
    archiveSession,
    getArchivedSessions,
    getChecklist
  };
};
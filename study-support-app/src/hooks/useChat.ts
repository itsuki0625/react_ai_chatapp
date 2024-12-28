import { apiClient } from '@/lib/api-client';

interface ChatResponse {
  response: string;
}

interface Message {
  id?: string;
  content: string;
  sender_type?: 'user' | 'ai' | 'system';
  sender?: string;
  timestamp?: string | Date;
  created_at?: string;
}


interface ChatRequest {
  message: string;
  history?: Message[];
  session_id?: string | null;
}

interface StreamResponse {
  newSessionId: string;
}

const getToken = () => {
  return localStorage.getItem('token');
};

export const useChat = () => {
  const sendMessage = async (message: string) => {
    try {
      const response = await apiClient.post<ChatResponse>('/api/v1/chat', {
        message,
      });
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
    onError: (error: any) => void
  ): Promise<StreamResponse> => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId || undefined,
          session_type: type
        }),
        credentials: 'include'
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is null');
      }

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.slice(6);
            if (content === '[DONE]') continue;
            
            onChunk(content);
          }
        }
      }
    } catch (error) {
      onError(error);
    }
    return { newSessionId: "新しいセッションID" };
  };

  return { sendMessage, sendStreamMessage };
};
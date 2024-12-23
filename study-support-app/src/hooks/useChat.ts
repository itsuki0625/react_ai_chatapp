import { apiClient } from '@/lib/api-client';

interface ChatResponse {
  response: string;
}

interface Message {
  sender: string;
  text: string;
}

interface ChatRequest {
  message: string;
  history?: Message[];
}

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
    history: Message[] = [],
    onMessage: (text: string) => void,
    onError: (error: any) => void
  ) => {
    try {
      const response = await fetch(`http://localhost:5000/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          message,
          history,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'ストリーミングリクエストに失敗しました');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('レスポンスボディを読み取れません');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          if (!line.startsWith('data: ')) continue;

          const data = line.replace('data: ', '');
          if (data === '[DONE]') return;

          try {
            onMessage(data);
          } catch (e) {
            console.error('メッセージの処理中にエラーが発生しました:', e);
          }
        }
      }

      if (buffer.trim() && buffer.startsWith('data: ')) {
        const data = buffer.replace('data: ', '');
        if (data !== '[DONE]') {
          onMessage(data);
        }
      }

    } catch (error) {
      console.error('ストリーミングチャットでエラーが発生しました:', error);
      onError(error);
    }
  };

  return { sendMessage, sendStreamMessage };
};
import { useState, useEffect } from 'react';
import api from '../services/api';

interface Message {
  sender: string;
  text: string;
  timestamp: string;
  isStreaming?: boolean;
}

interface StreamResponse {
  content: string;
  sender: string;
  timestamp: string;
}

const useChat = () => {
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem('chatHistory');
    return saved ? JSON.parse(saved) as Message[] : [];
  });
  const [input, setInput] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    const filteredMessages = messages.filter(msg => !msg.isStreaming);
    localStorage.setItem('chatHistory', JSON.stringify(filteredMessages));
  }, [messages]);

  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await api.get('/session');
        setSessionId(response.data.session_id);
      } catch (error) {
        console.error('セッション初期化エラー:', error);
      }
    };
    initSession();
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;
    console.log('送信メッセージ:', input);

    const userMessage: Message = {
      sender: 'ユーザー',
      text: input,
      timestamp: new Date().toLocaleString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // 空のAIメッセージを追加
    setMessages(prev => [
      ...prev,
      {
        sender: 'AI',
        text: '',
        timestamp: new Date().toLocaleString(),
        isStreaming: true,
      },
    ]);
    setIsStreaming(true);

    try {
      console.log('リクエスト開始');
      const response = await fetch(`${api.defaults.baseURL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          history: messages.filter(msg => !msg.isStreaming),
        }),
      });

      console.log('レスポンス受信:', response.status); 
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('ストリームリーダーを作成できません');
      }

      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('ストリーム終了');
          break;
        }

        const chunk = decoder.decode(value);
        console.log('受信チャンク:', chunk);

        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const rawData = line.slice(6);
              console.log('解析前データ:', rawData);

              const data: StreamResponse = JSON.parse(line.slice(6));
              console.log('解析後データ:', data);

              if (data.content) {
                accumulatedText += data.content;
                console.log('蓄積テキスト:', accumulatedText);

                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (lastMessage && lastMessage.isStreaming) {
                    lastMessage.text = accumulatedText;
                    console.log('メッセージ更新:', lastMessage.text); 
                  }
                  return newMessages;
                });
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }

      // ストリーミング完了後にフラグを更新
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.isStreaming) {
          lastMessage.isStreaming = false;
          console.log('ストリーミング完了:', lastMessage.text);
        }
        return newMessages;
      });
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        if (newMessages[newMessages.length - 1]?.isStreaming) {
          newMessages.pop();
        }
        newMessages.push({
          sender: 'AI',
          text: 'エラーが発生しました。もう一度お試しください。',
          timestamp: new Date().toLocaleString(),
        });
        return newMessages;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const clearHistory = async () => {
    if (window.confirm('会話履歴を削除してもよろしいですか？')) {
      try {
        await api.delete('/session');
        setMessages([]);
        localStorage.removeItem('chatHistory');
        const response = await api.get('/session');
        setSessionId(response.data.session_id);
      } catch (error) {
        console.error('履歴削除エラー:', error);
      }
    }
  };

  return {
    messages,
    input,
    setInput,
    sendMessage,
    clearHistory,
    isStreaming,
    sessionId,
  };
};

export default useChat;

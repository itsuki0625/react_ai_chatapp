"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot } from 'lucide-react';
import { useChat } from '@/hooks/useChat';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'こんにちは！自己分析のお手伝いをさせていただきます。あなたの経験や目標について教えてください。',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sendStreamMessage } = useChat();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: newMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsLoading(true);

    // ボットの応答用の仮メッセージを作成
    const botMessageId = (Date.now() + 1).toString();
    const botMessage: Message = {
      id: botMessageId,
      content: '',
      sender: 'bot',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, botMessage]);

    try {
      // チャット履歴の形式を変換
      const history = messages.map(msg => ({
        sender: msg.sender === 'user' ? 'user' : 'assistant',
        text: msg.content
      }));

      await sendStreamMessage(
        newMessage,
        history,
        (text) => {
          // ストリーミングで受け取ったテキストを既存のメッセージに追加
          setMessages(prev => prev.map(msg => 
            msg.id === botMessageId
              ? { ...msg, content: msg.content + text }
              : msg
          ));
        },
        (error) => {
          console.error('エラーが発生しました:', error);
          setMessages(prev => prev.map(msg =>
            msg.id === botMessageId
              ? { ...msg, content: 'メッセージの送信中にエラーが発生しました。もう一度お試しください。' }
              : msg
          ));
        }
      );
    } catch (error) {
      console.error('エラーが発生しました:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  return (
    <div className="h-[calc(100vh-32px)] flex flex-col">
      {/* チャットヘッダー */}
      <header className="flex-none bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-800">AIチャット</h1>
        <p className="text-sm text-gray-500">自己分析や志望理由書作成のサポートをします</p>
      </header>

      {/* メッセージエリア */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="p-6 space-y-4">
          {messages.map(message => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className="flex items-start max-w-xl">
                {message.sender === 'bot' && (
                  <div className="flex-shrink-0 mr-3">
                    <div className="bg-gray-200 rounded-full p-2">
                      <Bot className="h-5 w-5 text-gray-500" />
                    </div>
                  </div>
                )}
                <div
                  className={`rounded-lg px-4 py-2 ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <span className="text-xs text-gray-400 mt-1 block">
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>
                {message.sender === 'user' && (
                  <div className="flex-shrink-0 ml-3">
                    <div className="bg-gray-200 rounded-full p-2">
                      <User className="h-5 w-5 text-gray-500" />
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* メッセージ入力エリア */}
      <footer className="flex-none bg-white border-t border-gray-200 px-4 py-4">
        <form onSubmit={handleSendMessage} className="flex space-x-4">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="メッセージを入力..."
            disabled={isLoading}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!newMessage.trim() || isLoading}
            className="bg-blue-600 text-white rounded-lg px-6 py-2 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </footer>
    </div>
  );
};

export default ChatPage;
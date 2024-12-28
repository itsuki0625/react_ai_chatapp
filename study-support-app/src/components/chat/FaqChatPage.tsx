"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, MoreVertical, Archive, RotateCcw } from 'lucide-react';
import { useChat } from '@/hooks/useChat';
import { Menu } from '@headlessui/react';

interface Message {
  id?: string;
  content: string;
  sender_type?: 'user' | 'ai' | 'system';
  sender?: string;
  timestamp?: string | Date;
  created_at?: string;
}

interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
}

const getToken = () => {
  return localStorage.getItem('token');
};

export default function FaqChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'こんにちは！総合型選抜に関するよくある質問にお答えします！',
      sender_type: 'system',
      timestamp: new Date()
    }
  ]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sendStreamMessage } = useChat();
  const [archivedSessions, setArchivedSessions] = useState<ChatSession[]>([]);
  const [showArchived, setShowArchived] = useState(false);

  const fetchChatSessions = async () => {
    try {
      const token = getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions?session_type=FAQ`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch sessions');
      }

      const data = await response.json();
      
      if (Array.isArray(data)) {
        setSessions(data);
        if (data.length > 0) {
          setActiveSession(data[0]);
        }
      } else {
        console.error('Expected array of sessions but got:', data);
        setSessions([]);
      }
    } catch (error) {
      console.error('Failed to fetch chat sessions:', error);
      setSessions([]);
    }
  };

  const fetchSessionMessages = async (sessionId: string) => {
    try {
      const token = getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/${sessionId}/messages?session_type=FAQ`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          credentials: 'include'
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch messages');
      }

      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
      if (error instanceof Error) {
        console.error('Error details:', error.message);
      }
    }
  };

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
      sender_type: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsLoading(true);

    try {
      const currentSessionId = sessionId || undefined;
      const messageHistory = messages.map(msg => ({
        sender: msg.sender_type === 'user' ? 'user' : 'ai',
        content: msg.content
      }));

      let aiResponse = '';
      const { newSessionId } = await sendStreamMessage(
        newMessage,
        currentSessionId,
        'FAQ',
        (content: string) => {
          aiResponse += content;
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.sender_type === 'ai') {
              lastMessage.content = aiResponse;
              return [...newMessages];
            } else {
              return [
                ...newMessages,
                {
                  id: Date.now().toString(),
                  content: aiResponse,
                  sender: 'ai',
                  sender_type: 'ai',
                  timestamp: new Date()
                }
              ];
            }
          });
        },
        (error: any) => {
          console.error('エラーが発生しました:', error);
        }
      );

      if (newSessionId && !sessionId) {
        setSessionId(newSessionId);
        fetchChatSessions();
      }
    } catch (error: any) {
      console.error('エラーが発生しました:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string | Date | undefined) => {
    if (!timestamp) return '';
    
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    
    try {
      return date.toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch (e) {
      console.error('タイムスタンプのフォーマットエラー:', e);
      return '';
    }
  };

  const createNewChat = () => {
    setMessages([{
      id: '1',
      content: 'こんにちは！総合型選抜に関するよくある質問にお答えします！',
      sender_type: 'system',
      timestamp: new Date()
    }]);
    setActiveSession(null);
    setSessionId(null);
  };

  const archiveSession = async (sessionId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/${sessionId}/archive?session_type=FAQ`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to archive session');
      }

      fetchChatSessions();
      
      if (activeSession?.id === sessionId) {
        createNewChat();
      }
    } catch (error) {
      console.error('Error archiving session:', error);
    }
  };

  const fetchArchivedSessions = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/archived?session_type=FAQ`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        }
      );
      if (!response.ok) throw new Error('Failed to fetch archived sessions');
      const data = await response.json();
      setArchivedSessions(data);
    } catch (error) {
      console.error('Error fetching archived sessions:', error);
    }
  };

  const restoreSession = async (sessionId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/${sessionId}/restore?session_type=FAQ`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to restore session');
      }

      fetchChatSessions();
      fetchArchivedSessions();
    } catch (error) {
      console.error('Error restoring session:', error);
    }
  };

  useEffect(() => {
    fetchChatSessions();
  }, []);

  useEffect(() => {
    if (activeSession) {
      fetchSessionMessages(activeSession.id);
    }
  }, [activeSession]);

  useEffect(() => {
    fetchArchivedSessions();
  }, []);

  return (
    <div className="h-[calc(100vh-32px)] flex">
      {/* セッション一覧サイドバー */}
      <div className="w-64 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4">
          <button
            onClick={createNewChat}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            新しい質問を始める
          </button>
        </div>

        {/* アクティブなセッション */}
        <div className="flex-1 overflow-y-auto">
          {Array.isArray(sessions) && sessions.map(session => (
            <div
              key={session.id}
              className={`group flex items-center justify-between px-4 py-2 hover:bg-gray-100 ${
                activeSession?.id === session.id ? 'bg-gray-100' : ''
              }`}
            >
              <button
                onClick={() => setActiveSession(session)}
                className="flex-1 text-left"
              >
                <p className="text-sm font-medium truncate">
                  {session.title || '新しい質問'}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(session.created_at).toLocaleDateString()}
                </p>
              </button>
              
              <Menu as="div" className="relative">
                <Menu.Button className="invisible group-hover:visible p-1 rounded-full hover:bg-gray-200">
                  <MoreVertical className="h-4 w-4 text-gray-500" />
                </Menu.Button>
                <Menu.Items className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 focus:outline-none">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={() => archiveSession(session.id)}
                        className={`${
                          active ? 'bg-gray-100' : ''
                        } flex w-full items-center px-4 py-2 text-sm text-gray-700`}
                      >
                        <Archive className="h-4 w-4 mr-2" />
                        非表示にする
                      </button>
                    )}
                  </Menu.Item>
                </Menu.Items>
              </Menu>
            </div>
          ))}
        </div>

        {/* アーカイブされたセッション */}
        <div className="border-t border-gray-200">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className="w-full px-4 py-2 text-left text-sm text-gray-600 hover:bg-gray-50 flex items-center"
          >
            <Archive className="h-4 w-4 mr-2" />
            アーカイブ済み
            <span className="ml-auto">
              {showArchived ? '▼' : '▶'}
            </span>
          </button>
          
          {showArchived && (
            <div className="bg-gray-50">
              {archivedSessions.map(session => (
                <div
                  key={session.id}
                  className="group flex items-center justify-between px-4 py-2 hover:bg-gray-100"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-500 truncate">
                      {session.title || '新しい質問'}
                    </p>
                    <p className="text-xs text-gray-400">
                      {new Date(session.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  
                  <button
                    onClick={() => restoreSession(session.id)}
                    className="invisible group-hover:visible p-1 rounded-full hover:bg-gray-200"
                    title="復元"
                  >
                    <RotateCcw className="h-4 w-4 text-gray-500" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* チャット本体 */}
      <div className="flex-1 flex flex-col">
        {/* チャットヘッダー */}
        <header className="flex-none bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-xl font-semibold text-gray-800">FAQ チャット</h1>
          <p className="text-sm text-gray-500">総合型選抜に関する質問にお答えします</p>
        </header>

        {/* メッセージエリア */}
        <main className="flex-1 overflow-y-auto bg-gray-50">
          <div className="p-6 space-y-4">
            {messages.map((message, index) => {
              const isUserMessage = message.sender_type === 'user' || message.sender === 'user';
              
              return (
                <div
                  key={message.id || index}
                  className={`flex ${
                    isUserMessage ? 'justify-end' : 'justify-start'
                  } mb-4`}
                >
                  <div className="flex items-start max-w-xl">
                    {!isUserMessage && (
                      <div className="flex-shrink-0 mr-3">
                        <div className="bg-gray-200 rounded-full p-2">
                          <Bot className="h-5 w-5 text-gray-500" />
                        </div>
                      </div>
                    )}
                    <div
                      className={`rounded-lg px-4 py-2 ${
                        isUserMessage
                          ? 'bg-blue-600 text-white'
                          : 'bg-white border border-gray-200'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <span className="text-xs text-gray-400 mt-1 block">
                        {formatTimestamp(message.created_at || message.timestamp)}
                      </span>
                    </div>
                    {isUserMessage && (
                      <div className="flex-shrink-0 ml-3">
                        <div className="bg-gray-200 rounded-full p-2">
                          <User className="h-5 w-5 text-gray-500" />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
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
              placeholder="質問を入力してください..."
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
    </div>
  );
}
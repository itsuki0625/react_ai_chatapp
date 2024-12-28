"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, MoreVertical, Archive, RotateCcw } from 'lucide-react';
import { useChat } from '@/hooks/useChat';
import { Menu } from '@headlessui/react';
import { ChecklistEvaluation } from './ChecklistEvaluation';

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

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sendStreamMessage } = useChat();
  const [archivedSessions, setArchivedSessions] = useState<ChatSession[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const checklistRef = useRef<{ triggerUpdate: () => void }>(null);

  useEffect(() => {
    // セッション一覧を取得
    fetchChatSessions();
  }, []);

  useEffect(() => {
    // アクティブなセッションが変更されたらメッセージを取得
    if (activeSession) {
      fetchSessionMessages(activeSession.id);
    }
  }, [activeSession]);

  const fetchChatSessions = async () => {
    try {
      const token = getToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to fetch sessions');
      }

      const data = await response.json();
      
      // データが配列であることを確認
      if (Array.isArray(data)) {
        setSessions(data);
        
        // 最新のセッションをアクティブにする
        if (data.length > 0) {
          setActiveSession(data[0]);
        }
      } else {
        console.error('Expected array of sessions but got:', data);
        setSessions([]); // エラー時は空配列をセット
      }
    } catch (error) {
      console.error('Failed to fetch chat sessions:', error);
      setSessions([]); // エラー時は空配列をセット
    }
  };

  const fetchSessionMessages = async (sessionId: string) => {
    try {
      const token = getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/${sessionId}/messages`,
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
      console.log("response data : ", data);
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

      // ストリーミングレスポンスを処理
      let aiResponse = '';
      const { newSessionId } = await sendStreamMessage(
        newMessage,
        currentSessionId,
        'CONSULTATION',
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

      // レスポンスから返されたセッションIDを保存
      if (!sessionId) {
        // セッション一覧を更新
        fetchChatSessions();
      }

      // メッセージ送信後にチェックリストの更新をトリガー
      if (checklistRef.current) {
        checklistRef.current.triggerUpdate();
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

  // 新しいチャットを作成する関数
  const createNewChat = () => {
    // メッセージをクリア
    setMessages([]);
    // アクティブセッションをnullに設定
    setActiveSession(null);
    // セッションIDをクリア
    setSessionId(null);
  };

  // アクティブセッションが変更されたときの処理
  useEffect(() => {
    if (activeSession) {
      setSessionId(activeSession.id);
      fetchSessionMessages(activeSession.id);
    }
  }, [activeSession]);

  // セッションをアーカイブする関数
  const archiveSession = async (sessionId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/${sessionId}/archive`,
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

      // セッション一覧を更新
      fetchChatSessions();
      
      // アーカイブしたセッションが現在アクティブな場合、新しいチャットを作成
      if (activeSession?.id === sessionId) {
        createNewChat();
      }
    } catch (error) {
      console.error('Error archiving session:', error);
    }
  };

  // アーカイブされたセッションを取得
  const fetchArchivedSessions = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/archived`,
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

  // セッションを復元する関数
  const restoreSession = async (sessionId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/${sessionId}/restore`,
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

      // セッション一覧を更新
      fetchChatSessions();
      fetchArchivedSessions();
    } catch (error) {
      console.error('Error restoring session:', error);
    }
  };

  // アーカイブ済みセッションの表示を初期化
  useEffect(() => {
    fetchArchivedSessions();
  }, []);

  const handleTextAreaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target;
    setNewMessage(textarea.value);
    
    // テキストエリアの高さを自動調整
    textarea.style.height = 'auto';  // 一度リセット
    textarea.style.height = `${textarea.scrollHeight}px`;
  };

  return (
    <div className="flex h-screen">
      {/* セッション一覧サイドバー */}
      <div className="w-64 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4">
          <button
            onClick={createNewChat}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            新しいチャット
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
                  {session.title || '新しいチャット'}
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
                      {session.title || '新しいチャット'}
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
          <h1 className="text-xl font-semibold text-gray-800">AIチャット</h1>
          <p className="text-sm text-gray-500">自己分析や志望理由書作成のサポートをします</p>
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
                      <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
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
          <form onSubmit={handleSendMessage} className="flex space-x-4 items-start">
            <textarea
              value={newMessage}
              onChange={handleTextAreaInput}
              placeholder="メッセージを入力..."
              rows={1}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[40px] max-h-[200px] overflow-y-auto"
            />
            <button
              type="submit"
              disabled={!newMessage.trim() || isLoading}
              className="h-[40px] w-[40px] flex items-center justify-center bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-600"
            >
              {isLoading ? (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </form>
        </footer>
      </div>

      {/* チェックリスト部分 (FAQチャット以外の場合のみ表示) */}
      {activeSession && activeSession.title !== 'FAQ' && (
        <div className="w-80 border-l bg-gray-50 p-4 overflow-y-auto">
          <ChecklistEvaluation 
            ref={checklistRef}
            chatId={activeSession.id} 
            sessionType="CONSULTATION"
          />
        </div>
      )}
    </div>
  );
}
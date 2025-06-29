'use client';

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { 
  ChatMessage, 
  ChatSession, 
  ChatTypeValue, 
  ChatSessionStatus,
  MessageSender,
  ChatSubmitRequest 
} from '@/types/chat';
import { apiClient, chatApi } from '@/lib/api-client';
import { useChatWebSocket, WebSocketMessage } from '@/hooks/useChatWebSocket';
import { v4 as uuidv4 } from 'uuid';
import { useSession } from 'next-auth/react';
import { useEffect, useCallback } from 'react';

// ストアの状態型定義
interface ChatState {
  // 基本状態
  sessionId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | Error | null;
  currentChatType: ChatTypeValue | null;
  
  // セッション管理
  sessions: ChatSession[];
  isLoadingSessions: boolean;
  errorSessions: string | Error | null;
  archivedSessions: ChatSession[];
  isLoadingArchivedSessions: boolean;
  errorArchivedSessions: string | Error | null;
  
  // WebSocket接続
  isWebSocketConnected: boolean;
  
  // 認証
  authToken: string | null;
  
  // UI状態
  justStartedNewChat: boolean;
  viewingSessionStatus: ChatSessionStatus | null;
  sessionStatus: ChatSessionStatus | 'PENDING' | 'INACTIVE';
  traceLogs: string[];
}

// アクション型定義
interface ChatActions {
  // メッセージ関連
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  clearMessages: () => void;
  
  // セッション関連
  setSessionId: (id: string | null, status?: ChatSessionStatus) => void;
  setCurrentChatType: (chatType: ChatTypeValue | null) => void;
  startNewChat: (chatType: ChatTypeValue, title?: string) => Promise<string | null>;
  
  // セッション一覧管理
  setSessions: (sessions: ChatSession[]) => void;
  setArchivedSessions: (sessions: ChatSession[]) => void;
  fetchSessions: (chatType: ChatTypeValue) => Promise<void>;
  fetchArchivedSessions: (chatType: ChatTypeValue) => Promise<void>;
  archiveSession: (sessionId: string) => Promise<void>;
  unarchiveSession: (sessionId: string) => Promise<void>;
  
  // メッセージ履歴
  fetchMessages: (sessionId: string) => Promise<void>;
  
  // メッセージ送信（WebSocket用）
  sendMessage: (messageContent: string) => void;
  
  // WebSocket関連
  setWebSocketConnected: (connected: boolean) => void;
  
  // 認証
  setAuthToken: (token: string | null) => void;
  
  // ローディング状態
  setLoading: (loading: boolean) => void;
  setLoadingSessions: (loading: boolean) => void;
  setLoadingArchivedSessions: (loading: boolean) => void;
  
  // エラー管理
  setError: (error: string | Error | null) => void;
  setErrorSessions: (error: string | Error | null) => void;
  setErrorArchivedSessions: (error: string | Error | null) => void;
  
  // UI状態
  setJustStartedNewChat: (started: boolean) => void;
  setViewingSessionStatus: (status: ChatSessionStatus | null) => void;
  setSessionStatus: (status: ChatSessionStatus | 'PENDING' | 'INACTIVE') => void;
  
  // トレースログ
  addTrace: (log: string) => void;
  clearTrace: () => void;
  
  // ユーティリティ
  clearChat: (chatType?: ChatTypeValue) => void;
  changeChatType: (chatType: ChatTypeValue) => void;
  reset: () => void;
}

type ChatStore = ChatState & ChatActions;

// 初期状態
const initialState: ChatState = {
  sessionId: null,
  messages: [],
  isLoading: false,
  error: null,
  currentChatType: null,
  sessions: [],
  isLoadingSessions: false,
  errorSessions: null,
  archivedSessions: [],
  isLoadingArchivedSessions: false,
  errorArchivedSessions: null,
  isWebSocketConnected: false,
  authToken: null,
  justStartedNewChat: false,
  viewingSessionStatus: null,
  sessionStatus: 'INACTIVE',
  traceLogs: [],
};

// Zustandストア作成
export const useChatStore = create<ChatStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,
      
      // メッセージ関連
      addMessage: (message) => {
        set((state) => {
          const existingIndex = state.messages.findIndex(m => m.id === message.id);
          if (existingIndex !== -1) {
            const newMessages = [...state.messages];
            newMessages[existingIndex] = message;
            return { messages: newMessages, justStartedNewChat: false };
          }
          return { 
            messages: [...state.messages, message], 
            justStartedNewChat: false 
          };
        });
      },
      
      setMessages: (messages) => set({ messages, justStartedNewChat: false }),
      clearMessages: () => set({ messages: [] }),
      
      // セッション関連
      setSessionId: (id, status) => {
        const currentState = get();
        const sessionActuallyChanged = id !== currentState.sessionId;
        let newStatus: ChatSessionStatus | null = null;
        
        if (status && Object.values(ChatSessionStatus).includes(status as ChatSessionStatus)) {
          newStatus = status as ChatSessionStatus;
        } else if (id) {
          newStatus = ChatSessionStatus.ACTIVE;
        }
        
        set({
          sessionId: id,
          viewingSessionStatus: newStatus,
          sessionStatus: newStatus || 'INACTIVE',
          messages: sessionActuallyChanged ? [] : currentState.messages,
          justStartedNewChat: !id,
        });
      },
      
      setCurrentChatType: (chatType) => set({ 
        currentChatType: chatType, 
        messages: [], 
        sessionId: null, 
        justStartedNewChat: false, 
        viewingSessionStatus: null 
      }),
      
      startNewChat: async (chatType, title) => {
        try {
          set({ isLoading: true, error: null });
          const currentState = get();
          
          if (!currentState.authToken) {
            throw new Error('認証が必要です');
          }
          
          // 正しいAPI呼び出し（React Contextと同じ）
          const response = await apiClient.post<ChatSession>(
            '/api/v1/chat/sessions',
            { chat_type: chatType },
            { headers: { Authorization: `Bearer ${currentState.authToken}` } }
          );
          
          const newSession = response.data;
          const sessionStatus = Object.values(ChatSessionStatus).includes((newSession.status || '').toUpperCase() as ChatSessionStatus) 
                                ? (newSession.status || '').toUpperCase() as ChatSessionStatus 
                                : ChatSessionStatus.ACTIVE;
          
          if (newSession?.id) {
            set({
              sessionId: newSession.id,
              currentChatType: chatType,
              messages: [],
              isLoading: false,
              error: null,
              justStartedNewChat: false,
              sessionStatus,
              viewingSessionStatus: sessionStatus,
            });
            
            // セッション一覧も更新
            get().fetchSessions(chatType);
            
            return newSession.id;
          } else {
            throw new Error('セッションの作成に失敗しました');
          }
        } catch (error) {
          console.error('新しいチャットセッションの作成に失敗:', error);
          set({ 
            isLoading: false, 
            error: error instanceof Error ? error : new Error('セッション作成に失敗しました') 
          });
          return null;
        }
      },
      
      // セッション一覧管理
      setSessions: (sessions) => set({ sessions }),
      setArchivedSessions: (sessions) => set({ archivedSessions: sessions }),
      
      fetchSessions: async (chatType) => {
        try {
          set({ isLoadingSessions: true, errorSessions: null });
          const currentState = get();
          
          if (!currentState.authToken) {
            throw new Error('認証トークンがありません');
          }
          
          const response = await chatApi.getActiveSessions(currentState.authToken, chatType);
          set({ 
            sessions: response.data || [], 
            isLoadingSessions: false 
          });
        } catch (error) {
          console.error('セッション一覧の取得に失敗:', error);
          set({
            isLoadingSessions: false,
            errorSessions: error instanceof Error ? error : new Error('セッション取得に失敗しました')
          });
        }
      },
      
      fetchArchivedSessions: async (chatType) => {
        try {
          set({ isLoadingArchivedSessions: true, errorArchivedSessions: null });
          const currentState = get();
          
          if (!currentState.authToken) {
            throw new Error('認証トークンがありません');
          }
          
          const response = await chatApi.getArchivedSessions(currentState.authToken, chatType);
          set({ 
            archivedSessions: response.data || [], 
            isLoadingArchivedSessions: false 
          });
        } catch (error) {
          console.error('アーカイブセッション一覧の取得に失敗:', error);
          set({
            isLoadingArchivedSessions: false,
            errorArchivedSessions: error instanceof Error ? error : new Error('アーカイブセッション取得に失敗しました')
          });
        }
      },
      
      archiveSession: async (sessionId) => {
        try {
          const currentState = get();
          
          if (!currentState.authToken) {
            throw new Error('認証トークンがありません');
          }
          
          await chatApi.archiveSession(currentState.authToken, sessionId);
          set({
            sessions: currentState.sessions.filter(session => session.id !== sessionId),
            sessionId: currentState.sessionId === sessionId ? null : currentState.sessionId,
          });
        } catch (error) {
          console.error('セッションのアーカイブに失敗:', error);
          set({ 
            error: error instanceof Error ? error : new Error('セッションのアーカイブに失敗しました') 
          });
        }
      },
      
      unarchiveSession: async (sessionId) => {
        try {
          const currentState = get();
          
          if (!currentState.authToken) {
            throw new Error('認証トークンがありません');
          }
          
          await chatApi.unarchiveSession(currentState.authToken, sessionId);
          set({
            archivedSessions: currentState.archivedSessions.filter(session => session.id !== sessionId),
          });
        } catch (error) {
          console.error('セッションの復元に失敗:', error);
          set({ 
            error: error instanceof Error ? error : new Error('セッションの復元に失敗しました') 
          });
        }
      },
      
      // メッセージ履歴
      fetchMessages: async (sessionId) => {
        try {
          set({ isLoading: true, error: null });
          const currentState = get();
          
          if (!currentState.authToken) {
            throw new Error('認証トークンがありません');
          }
          
          const response = await chatApi.getSessionMessages(currentState.authToken, sessionId);
          
          if (response.data && Array.isArray(response.data)) {
            // 空白メッセージをフィルタリング
            const filteredMessages = response.data
              .filter((msg: any) => msg.content && msg.content.trim().length > 0)
              .map((msg: any) => ({
                id: msg.id || uuidv4(),
                session_id: sessionId,
                sender: msg.sender === 'AI' ? 'AI' : 'USER' as MessageSender,
                content: msg.content,
                timestamp: msg.created_at || new Date().toISOString(),
                isStreaming: false,
                isLoading: false,
                isError: false,
              }));
            
            set({ messages: filteredMessages, isLoading: false });
          } else {
            set({ messages: [], isLoading: false });
          }
        } catch (error) {
          console.error('メッセージ履歴の取得に失敗:', error);
          set({
            isLoading: false,
            error: error instanceof Error ? error : new Error('メッセージ履歴の取得に失敗しました')
          });
        }
      },
      
      // メッセージ送信（WebSocketベース、React Contextと同様）
      sendMessage: (messageContent) => {
        const currentState = get();
        const { sessionId, currentChatType, authToken } = currentState;
        
        if (!authToken) {
          console.error('送信失敗: 認証トークンがありません');
          set({ error: new Error('認証が必要です') });
          return;
        }
        
        if (!sessionId) {
          console.error('送信失敗: セッションIDがありません');
          set({ error: new Error('セッションを開始してください') });
          return;
        }
        
        if (!currentChatType) {
          console.error('送信失敗: チャットタイプが設定されていません');
          set({ error: new Error('チャットタイプを選択してください') });
          return;
        }
        
        // ユーザーメッセージを即座に追加
        const userMessage: ChatMessage = {
          id: uuidv4(),
          session_id: sessionId,
          sender: 'USER',
          content: messageContent,
          timestamp: new Date().toISOString(),
          isLoading: true,
          isStreaming: false,
          isError: false,
        };
        
        get().addMessage(userMessage);
        set({ isLoading: true, error: null });
        
        // WebSocketメッセージは外部のuseChatWebSocketフックが処理
        // この関数はWebSocketのsendMessage関数に依存
      },
      
      // WebSocket関連
      setWebSocketConnected: (connected) => set({ isWebSocketConnected: connected }),
      
      // 認証
      setAuthToken: (token) => {
        set({ authToken: token });
        // トークンがクリアされた場合、セッション情報もクリア
        if (!token) {
          set({
            sessions: [],
            archivedSessions: [],
            sessionId: null,
            messages: [],
            currentChatType: null,
          });
        }
      },
      
      // ローディング状態
      setLoading: (loading) => set({ isLoading: loading }),
      setLoadingSessions: (loading) => set({ isLoadingSessions: loading }),
      setLoadingArchivedSessions: (loading) => set({ isLoadingArchivedSessions: loading }),
      
      // エラー管理
      setError: (error) => set({ error }),
      setErrorSessions: (error) => set({ errorSessions: error }),
      setErrorArchivedSessions: (error) => set({ errorArchivedSessions: error }),
      
      // UI状態
      setJustStartedNewChat: (started) => set({ justStartedNewChat: started }),
      setViewingSessionStatus: (status) => set({ viewingSessionStatus: status }),
      setSessionStatus: (status) => set({ sessionStatus: status }),
      
      // トレースログ
      addTrace: (log) => set((state) => ({ traceLogs: [...state.traceLogs, log] })),
      clearTrace: () => set({ traceLogs: [] }),
      
      // ユーティリティ
      clearChat: (chatType) => set({ 
        sessionId: null, 
        messages: [], 
        justStartedNewChat: false, 
        viewingSessionStatus: null 
      }),
      
      changeChatType: (chatType) => {
        get().setCurrentChatType(chatType);
      },
      
      reset: () => set(initialState),
    })),
    {
      name: 'chat-store',
    }
  )
);

// WebSocketメッセージハンドラー
export const createWebSocketHandlers = (store: ChatStore) => {
  const handleWebSocketMessage = (wsMessage: WebSocketMessage) => {
    console.log('WebSocket Message Received:', wsMessage);
    const currentState = store;
    
    switch (wsMessage.type) {
      case 'chunk':
        if (wsMessage.content && wsMessage.content.trim().length > 0) {
          const streamingAiMsgIndex = currentState.messages.findIndex(
            (m: ChatMessage) => m.sender === 'AI' && m.isStreaming
          );
          
          if (streamingAiMsgIndex !== -1) {
            // 既存のストリーミングメッセージに追加
            const existingMessage = currentState.messages[streamingAiMsgIndex];
            const updatedMessage: ChatMessage = {
              ...existingMessage,
              content: existingMessage.content + wsMessage.content,
              timestamp: new Date().toISOString(),
            };
            store.addMessage(updatedMessage);
          } else {
            // 新しいAIメッセージを作成
            const aiMessage: ChatMessage = {
              id: (wsMessage as any).id || uuidv4(),
              sender: 'AI',
              content: wsMessage.content,
              timestamp: new Date().toISOString(),
              isStreaming: true,
              session_id: (wsMessage as any).session_id,
            };
            store.addMessage(aiMessage);
          }
        }
        break;
        
      case 'done':
        // ストリーミング完了
        const messages = currentState.messages.map(m =>
          m.sender === 'AI' && m.isStreaming 
            ? { ...m, isStreaming: false, isLoading: false }
            : m.isLoading && m.sender === 'USER'
            ? { ...m, isLoading: false, isError: false }
            : m
        );
        store.setMessages(messages);
        store.setLoading(false);
        store.clearTrace();
        
        // セッションIDの更新
        if ((wsMessage as any).session_id && currentState.sessionId !== (wsMessage as any).session_id) {
          store.setSessionId((wsMessage as any).session_id, ChatSessionStatus.ACTIVE);
        }
        break;
        
      case 'error':
        console.error("WebSocketエラー:", (wsMessage as any).detail);
        store.setError(new Error((wsMessage as any).detail || 'WebSocketエラーが発生しました'));
        store.setLoading(false);
        break;
        
      case 'info':
        console.info("サーバーからの情報:", (wsMessage as any).message);
        if ((wsMessage as any).session_id && currentState.sessionId !== (wsMessage as any).session_id) {
          store.setSessionId((wsMessage as any).session_id, ChatSessionStatus.ACTIVE);
        }
        break;
        
      case 'trace':
        if (wsMessage.content) {
          store.addTrace(wsMessage.content);
        }
        break;
        
      default:
        console.warn('未知のWebSocketメッセージタイプ:', wsMessage);
    }
  };

  const handleWebSocketError = (error: Event | Error) => {
    console.error("WebSocketエラー:", error);
    store.setError(error instanceof Error ? error : new Error('WebSocket接続エラー'));
  };

  const handleWebSocketOpen = () => {
    console.log("WebSocket接続が開かれました");
    store.setWebSocketConnected(true);
  };

  const handleWebSocketClose = (event: CloseEvent) => {
    console.log("WebSocket接続が閉じられました:", event.reason, event.code);
    store.setWebSocketConnected(false);
  };

  return {
    handleWebSocketMessage,
    handleWebSocketError,
    handleWebSocketOpen,
    handleWebSocketClose,
  };
};

// React Context互換のフック（段階的移行用 + 認証トークン自動管理）
export const useChat = () => {
  const store = useChatStore();
  const { data: session } = useSession();
  
  // 認証トークンの自動管理（React Contextと同様）
  useEffect(() => {
    const newToken = session?.user?.accessToken || null;
    if (store.authToken !== newToken) {
      store.setAuthToken(newToken);
    }
  }, [session, store]);
  
  // WebSocketハンドラーの設定
  const handlers = createWebSocketHandlers(store);
  const socketUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:5050/api/v1/chat/ws/chat';
  
  const { 
    sendMessage: wsSendMessage, 
    isConnected: wsIsConnected 
  } = useChatWebSocket({
    socketUrl,
    token: store.authToken,
    onMessageReceived: handlers.handleWebSocketMessage,
    onError: handlers.handleWebSocketError,
    onOpen: handlers.handleWebSocketOpen,
    onClose: handlers.handleWebSocketClose,
  });
  
  // WebSocket接続状態を同期
  useEffect(() => {
    store.setWebSocketConnected(wsIsConnected);
  }, [wsIsConnected, store]);
  
  // sendMessage関数を拡張（WebSocket経由で実際に送信）
  const sendMessage = useCallback((messageContent: string) => {
    // Zustandストアでメッセージ状態を管理
    store.sendMessage(messageContent);
    
    // WebSocket経由で送信
    if (wsIsConnected && store.sessionId && store.currentChatType) {
      const request: ChatSubmitRequest = {
        message: messageContent,
        chat_type: store.currentChatType,
        session_id: store.sessionId,
      };
      wsSendMessage(request);
    } else {
      console.error('WebSocket送信失敗: 接続またはセッション情報が不足');
      store.setError(new Error('WebSocket接続またはセッション情報が不足しています'));
    }
  }, [store, wsIsConnected, wsSendMessage]);
  
  return {
    // 状態
    sessionId: store.sessionId,
    messages: store.messages,
    isLoading: store.isLoading,
    error: store.error,
    currentChatType: store.currentChatType,
    sessions: store.sessions,
    isLoadingSessions: store.isLoadingSessions,
    errorSessions: store.errorSessions,
    archivedSessions: store.archivedSessions,
    isLoadingArchivedSessions: store.isLoadingArchivedSessions,
    errorArchivedSessions: store.errorArchivedSessions,
    isWebSocketConnected: store.isWebSocketConnected,
    authToken: store.authToken,
    justStartedNewChat: store.justStartedNewChat,
    viewingSessionStatus: store.viewingSessionStatus,
    sessionStatus: store.sessionStatus,
    traceLogs: store.traceLogs,
    
    // アクション（React Context互換）
    sendMessage,
    clearChat: store.clearChat,
    changeChatType: store.changeChatType,
    isConnected: store.isWebSocketConnected,
    connectWebSocket: () => console.log('WebSocket接続は自動管理されます'),
    disconnectWebSocket: () => console.log('WebSocket切断は自動管理されます'),
    startNewChat: store.startNewChat,
    fetchSessions: store.fetchSessions,
    fetchMessages: store.fetchMessages,
    archiveSession: store.archiveSession,
    fetchArchivedSessions: store.fetchArchivedSessions,
    unarchiveSession: store.unarchiveSession,
    
    // dispatch互換（必要に応じて）
    dispatch: (action: any) => {
      console.warn('dispatch は非推奨です。直接アクションを呼び出してください。', action);
    },
  };
};

// エクスポート
export default useChatStore;
export type { ChatStore, ChatState, ChatActions };

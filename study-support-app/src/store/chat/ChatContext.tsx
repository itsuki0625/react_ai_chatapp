import React, { createContext, useReducer, useContext, ReactNode, useCallback, useEffect, useMemo, useState, useRef } from 'react';
import { ChatState, ChatAction as OriginalChatAction, ChatMessage, ChatSubmitRequest, ChatTypeValue, ChatTypeEnum, ChatSession, MessageSender } from '@/types/chat'; // ChatActionをOriginalChatActionとしてインポート
import { useChatWebSocket, WebSocketMessage } from '@/hooks/useChatWebSocket';
import { v4 as uuidv4 } from 'uuid';
import { apiClient } from '@/lib/api-client';
import { chatApi } from '@/lib/api-client';

// ChatAction 型を拡張
export type ChatAction = 
  | OriginalChatAction
  | { type: 'PREPARE_NEW_CHAT'; payload: { chatType: ChatTypeValue } };

const initialState: ChatState = {
  sessionId: undefined,
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
  justStartedNewChat: false,
  viewingSessionStatus: null,
  isWebSocketConnected: false,
  sessionStatus: 'INACTIVE',
};

export const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  console.log('[DEBUG] ChatReducer - Action:', action.type, 'Payload:', ('payload' in action ? action.payload : 'N/A'));
  switch (action.type) {
    case 'SET_SESSION_ID':
      const newSessionId = action.payload.id;
      const currentSessionId = state.sessionId;
      const sessionActuallyChanged = newSessionId !== currentSessionId;
      const newStatus = action.payload.status || (newSessionId ? 'ACTIVE' : null);

      if (state.viewingSessionStatus !== newStatus || sessionActuallyChanged) {
        console.log(`[DEBUG] ChatReducer - SET_SESSION_ID: newId=${newSessionId}, newStatus=${newStatus}, sessionActuallyChanged=${sessionActuallyChanged}`);
      }

      return { 
        ...state, 
        sessionId: newSessionId, 
        viewingSessionStatus: newStatus, 
        messages: sessionActuallyChanged ? [] : state.messages, 
        justStartedNewChat: sessionActuallyChanged && newSessionId !== null ? false : state.justStartedNewChat,
        sessionStatus: newStatus,
      };
    case 'SET_CURRENT_CHAT_TYPE':
      return { ...state, currentChatType: action.payload, messages: [], sessionId: null, justStartedNewChat: false, viewingSessionStatus: null };
    case 'ADD_MESSAGE':
      const existingMessageIndex = state.messages.findIndex(m => m.id === action.payload.id);
      if (existingMessageIndex !== -1) {
        const newMessages = [...state.messages];
        newMessages[existingMessageIndex] = action.payload;
        return { ...state, messages: newMessages, justStartedNewChat: false };
      }
      return { ...state, messages: [...state.messages, action.payload], justStartedNewChat: false };
    case 'FETCH_HISTORY_START':
      return { ...state, isLoading: true, error: null, justStartedNewChat: false };
    case 'FETCH_HISTORY_SUCCESS':
      return { ...state, isLoading: false, messages: action.payload, justStartedNewChat: false };
    case 'FETCH_HISTORY_FAILURE':
      return { ...state, isLoading: false, error: action.payload, justStartedNewChat: false };
    case 'SEND_MESSAGE_START':
      return { ...state, isLoading: true, error: null };
    case 'SEND_MESSAGE_SUCCESS':
      return {
        ...state,
        isLoading: false,
        messages: state.messages.map(m =>
          m.isLoading && m.sender === 'USER' ? { ...m, isLoading: false, isError: false } : m
        )
      };
    case 'SEND_MESSAGE_FAILURE':
      return {
        ...state,
        isLoading: false,
        error: action.payload,
        messages: state.messages.map(m =>
          m.isLoading && m.sender === 'USER' ? { ...m, isLoading: false, isError: true } : m
        )
      };
    case 'FETCH_SESSIONS_START':
      return { ...state, isLoadingSessions: true, errorSessions: null };
    case 'FETCH_SESSIONS_SUCCESS':
      return { ...state, isLoadingSessions: false, sessions: action.payload };
    case 'FETCH_SESSIONS_FAILURE':
      return { ...state, isLoadingSessions: false, errorSessions: action.payload };
    case 'START_NEW_CHAT_SESSION':
      console.log('[chatReducer] START_NEW_CHAT_SESSION, payload:', action.payload);
      return {
        ...state,
        messages: [],
        sessionId: action.payload.sessionId === null ? undefined : action.payload.sessionId,
        isLoading: false,
        error: null,
        currentChatType: action.payload.chatType,
        justStartedNewChat: true,
        sessionStatus: action.payload.sessionId ? 'ACTIVE' : 'PENDING',
      };
    case 'ARCHIVE_SESSION_SUCCESS':
      return {
        ...state,
        sessions: state.sessions.filter(session => session.id !== action.payload.sessionId),
        sessionId: state.sessionId === action.payload.sessionId ? null : state.sessionId,
      };
    case 'FETCH_ARCHIVED_SESSIONS_START':
      return { ...state, isLoadingArchivedSessions: true, errorArchivedSessions: null };
    case 'FETCH_ARCHIVED_SESSIONS_SUCCESS':
      return { ...state, isLoadingArchivedSessions: false, archivedSessions: action.payload };
    case 'FETCH_ARCHIVED_SESSIONS_FAILURE':
      return { ...state, isLoadingArchivedSessions: false, errorArchivedSessions: action.payload };
    case 'UNARCHIVE_SESSION_SUCCESS':
      return {
        ...state,
        archivedSessions: state.archivedSessions.filter(session => session.id !== action.payload.sessionId),
      };
    case 'SET_VIEWING_SESSION_STATUS':
      if (state.viewingSessionStatus !== action.payload) {
        console.log(`[DEBUG] ChatReducer - SET_VIEWING_SESSION_STATUS: newStatus=${action.payload}`);
      }
      return { ...state, viewingSessionStatus: action.payload };
    case 'PREPARE_NEW_CHAT':
      console.log('[chatReducer] PREPARE_NEW_CHAT, current state before:', state);
      console.log('[chatReducer] PREPARE_NEW_CHAT, payload to use:', action.payload);
      const newStateAfterPrepare = {
        ...initialState,
        currentChatType: action.payload.chatType,
        justStartedNewChat: true,
        sessionStatus: 'PENDING' as const, // 型を明示
        sessionId: undefined,
        messages: [],
      };
      console.log('[chatReducer] PREPARE_NEW_CHAT, new state after:', newStateAfterPrepare);
      return newStateAfterPrepare;
    case 'SET_CHAT_TYPE':
      return { ...state, currentChatType: action.payload };
    case 'CLEAR_CHAT':
      return { ...state, sessionId: null, messages: [], justStartedNewChat: false, viewingSessionStatus: null };
    case 'SET_WEBSOCKET_CONNECTED':
      return { ...state, isWebSocketConnected: action.payload };
    default:
      return state;
  }
};

interface ChatContextType extends ChatState {
  dispatch: React.Dispatch<ChatAction>;
  sendMessage: (messageContent: string) => void;
  clearChat: (chatType?: ChatTypeValue) => void;
  changeChatType: (chatType: ChatTypeValue) => void;
  authToken: string | null;
  isConnected: boolean;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  startNewChat: (chatType: ChatTypeValue) => Promise<string | null>;
  fetchSessions: (chatType: ChatTypeValue) => Promise<void>;
  fetchMessages: (sessionId: string) => Promise<void>;
  archiveSession: (sessionId: string) => Promise<void>;
  fetchArchivedSessions: (chatType: ChatTypeValue) => Promise<void>;
  unarchiveSession: (sessionId: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children, initialAuthToken }: { children: ReactNode; initialAuthToken: string | null }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const [authToken, setAuthToken] = useState(initialAuthToken);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const socketUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:5050/api/v1/chat/ws/chat';

  const handleWebSocketMessage = useCallback((wsMessage: WebSocketMessage) => {
    console.log('WebSocket Message Received:', wsMessage);
    let aiMessage: ChatMessage | null = null;
    const now = new Date().toISOString();

    switch (wsMessage.type) {
      case 'chunk':
        if (wsMessage.content) {
          const streamingAiMsgIndex = state.messages.findIndex(m => m.sender === 'AI' && m.isStreaming);
          if (streamingAiMsgIndex !== -1) {
            aiMessage = {
              ...state.messages[streamingAiMsgIndex],
              content: state.messages[streamingAiMsgIndex].content + wsMessage.content,
              timestamp: now,
            };
          } else {
            aiMessage = {
              id: (wsMessage as any).id || (wsMessage as any).message?.id || uuidv4(), 
              sender: 'AI',
              content: wsMessage.content,
              timestamp: now,
              isStreaming: true,
              session_id: (wsMessage as any).session_id 
            };
          }
          if (aiMessage) dispatch({ type: 'ADD_MESSAGE', payload: aiMessage });
        }
        break;
      case 'done':
        const finalAiMsgIndex = state.messages.findIndex(m => m.sender === 'AI' && m.isStreaming && ((wsMessage as any).id ? m.id === (wsMessage as any).id : (wsMessage as any).message?.id ? m.id === (wsMessage as any).message.id : true) ); 
        if (finalAiMsgIndex !== -1) {
          aiMessage = {
            ...state.messages[finalAiMsgIndex],
            isStreaming: false,
            isLoading: false,
            isError: (wsMessage as any).error,
            timestamp: now,
          };
          if (aiMessage) dispatch({ type: 'ADD_MESSAGE', payload: aiMessage });
        }
        if ((wsMessage as any).session_id && state.sessionId !== (wsMessage as any).session_id) {
             console.log(`[WS DONE] WebSocket provided sessionId ${(wsMessage as any).session_id}, context has ${state.sessionId}. Updating context.`);
             dispatch({ type: 'SET_SESSION_ID', payload: { id: (wsMessage as any).session_id, status: 'ACTIVE' } });
        }
        dispatch({ type: 'SEND_MESSAGE_SUCCESS' });
        break;
      case 'error':
        console.error("Error from WebSocket:", (wsMessage as any).detail);
        dispatch({ type: 'SEND_MESSAGE_FAILURE', payload: (wsMessage as any).detail || 'WebSocket error' });
        break;
      case 'info':
        console.info("Info from server:", (wsMessage as any).message);
        if ((wsMessage as any).session_id && state.sessionId !== (wsMessage as any).session_id) {
            console.log(`[WS INFO] WebSocket provided sessionId ${(wsMessage as any).session_id}, context has ${state.sessionId}. Updating context for info.`);
            dispatch({ type: 'SET_SESSION_ID', payload: { id: (wsMessage as any).session_id, status: 'ACTIVE' } });
        }
        break;
      default:
        console.warn('Received unknown WebSocket message type:', wsMessage);
    }
  }, [state.sessionId, state.messages, dispatch]);

  const handleWebSocketError = useCallback((error: Event | Error) => {
    console.error("WebSocket Provider Error:", error);
  }, []); 
  
  const handleWebSocketOpen = useCallback(() => {
    console.log("WebSocket Provider: Connection Opened");
    setIsConnected(true);
  }, []);

  const handleWebSocketClose = useCallback((event: CloseEvent) => {
    console.log("WebSocket Provider: Connection Closed", event.reason, event.code);
    setIsConnected(false);
  }, []);

  const { sendMessage: wsSendMessage, isConnected: wsIsConnected, webSocketRef: actualWebSocketRef } = useChatWebSocket({
    socketUrl: socketUrl,
    token: authToken,
    onMessageReceived: handleWebSocketMessage,
    onError: handleWebSocketError,
    onOpen: handleWebSocketOpen,
    onClose: handleWebSocketClose,
  });

  useEffect(() => {
      setIsConnected(wsIsConnected);
      dispatch({ type: 'SET_WEBSOCKET_CONNECTED', payload: wsIsConnected });
  }, [wsIsConnected, dispatch]);

  // useEffect for managing WebSocket connection based on authToken and component lifecycle
  useEffect(() => {
    if (authToken) {
      console.log(`[ChatContext Auth Effect - Token Based] AuthToken is present. WebSocket connection should be managed by useChatWebSocket based on token presence.`);
      // ここでは connectWebSocket() や useChatWebSocket への明示的な指示は行わない
      // useChatWebSocket が authToken の変更を検知して接続/切断を行うことを期待
    } else {
      console.log(`[ChatContext Auth Effect - Token Based] AuthToken is NOT present. WebSocket should be disconnected by useChatWebSocket.`);
      // 同様に、ここでは disconnectWebSocket() は呼ばない
    }

    // Cleanup on ChatProvider unmount ONLY
    return () => {
      console.log("[ChatContext Auth Effect - Token Based] ChatProvider is unmounting. Closing WebSocket.");
      actualWebSocketRef.current?.close(1000, 'ChatProvider unmounted by ChatContext cleanup');
    };
  }, [authToken, actualWebSocketRef]); // 依存配列から state.currentChatType を削除
                                      // actualWebSocketRef はクリーンアップで最新のrefを使うために必要

  const connectWebSocket = useCallback(() => {
    if (authToken && state.currentChatType) {
        console.log("[ChatProvider] Attempting to connect WebSocket (implicitly by useChatWebSocket dependencies)");
    } else {
        console.log("[ChatProvider] Cannot connect WebSocket: authToken or currentChatType missing.");
    }
  }, [authToken, state.currentChatType]);

  const disconnectWebSocket = useCallback(() => {
    console.log("[ChatProvider] Attempting to disconnect WebSocket");
    actualWebSocketRef.current?.close(1000, 'User explicitly disconnected');
  }, [actualWebSocketRef]);

  const sendMessage = useCallback(async (messageContent: string) => {
    if (!authToken) {
        console.error('Cannot send message, authToken is missing.');
        dispatch({ type: 'SEND_MESSAGE_FAILURE', payload: 'Authentication token is missing.' });
        return;
    }
    if (!isConnected || actualWebSocketRef.current?.readyState !== WebSocket.OPEN) {
      console.error('Cannot send message, WebSocket is not connected or not open.');
      dispatch({ type: 'SEND_MESSAGE_FAILURE', payload: 'WebSocket not connected. Please try again.' });
      return;
    }

    let sessionIdForRequest: string | undefined = state.sessionId ?? undefined;
    const chatTypeForRequest = state.currentChatType;

    if (!chatTypeForRequest) {
        console.error("[sendMessage] chatType is not set. Cannot send message.");
        dispatch({ type: 'SEND_MESSAGE_FAILURE', payload: 'Chat type is not selected.' });
        return;
    }

    if (state.justStartedNewChat || !sessionIdForRequest) {
      const newFrontendSessionId = uuidv4(); 
      console.log(`[sendMessage] This is the first message for a new chat. Frontend temp sessionId: ${newFrontendSessionId}`);
      const userMessage: ChatMessage = {
        id: uuidv4(), 
        session_id: newFrontendSessionId, 
        content: messageContent,
        sender: 'USER',
        timestamp: new Date().toISOString(),
        isLoading: true,
      };
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      dispatch({ type: 'SEND_MESSAGE_START' });
      dispatch({ type: 'START_NEW_CHAT_SESSION', payload: { sessionId: undefined, chatType: chatTypeForRequest } }); 
      sessionIdForRequest = undefined; 
    } else {
      const userMessage: ChatMessage = {
        id: uuidv4(),
        session_id: sessionIdForRequest as string,
        content: messageContent,
        sender: 'USER',
        timestamp: new Date().toISOString(),
        isLoading: true,
      };
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      dispatch({ type: 'SEND_MESSAGE_START' });
    }

    const request: Omit<ChatSubmitRequest, 'session_id'> & { session_id?: string } = {
      message: messageContent,
      chat_type: chatTypeForRequest!,
    };
    if (sessionIdForRequest !== undefined) {
        request.session_id = sessionIdForRequest;
    }
    console.log('[sendMessage] Sending request to WebSocket:', request);
    wsSendMessage(request as ChatSubmitRequest);
  }, [authToken, isConnected, state.sessionId, state.currentChatType, state.justStartedNewChat, dispatch, wsSendMessage, actualWebSocketRef]);

  const clearChat = useCallback((chatType?: ChatTypeValue) => {
    dispatch({ type: 'CLEAR_CHAT', payload: { chatType: chatType ?? state.currentChatType } });
  }, [dispatch, state.currentChatType]);

  const changeChatType = useCallback((chatType: ChatTypeValue) => {
    if (state.currentChatType !== chatType) {
        console.log(`Changing chat type to: ${chatType}`);
        dispatch({ type: 'SET_CURRENT_CHAT_TYPE', payload: chatType });
    }
  }, [state.currentChatType, dispatch]);
  
  const startNewChat = useCallback(async (chatType: ChatTypeValue): Promise<string | null> => {
    console.warn("[ChatContext.startNewChat] This function's behavior has changed. It no longer guarantees returning a new session ID immediately.");
    dispatch({ type: 'PREPARE_NEW_CHAT', payload: { chatType } });
    return null; 
  }, [dispatch]);

  const fetchSessions = useCallback(async (chatType: ChatTypeValue) => {
    if (!authToken) {
      console.log("fetchSessions: No auth token, skipping fetch.");
      dispatch({ type: 'FETCH_SESSIONS_FAILURE', payload: "認証されていません。セッションを読み込めません。" });
      return;
    }
    console.log(`Fetching sessions for type: ${chatType} with token: ${authToken ? authToken.substring(0,10) + "..." : "N/A"}`);
    dispatch({ type: 'FETCH_SESSIONS_START' });
    try {
      const response = await apiClient.get<ChatSession[]>('/api/v1/chat/sessions', {
        headers: { Authorization: `Bearer ${authToken}` },
        params: { chat_type: chatType, status: 'ACTIVE' }
      });
      console.log("Sessions fetched successfully:", response.data);
      dispatch({ type: 'FETCH_SESSIONS_SUCCESS', payload: response.data });
    } catch (err) {
      console.error("Error fetching sessions:", err);
      let errorMessage = "セッションの読み込みに失敗しました。";
      if (err instanceof Error) {
        errorMessage = err.message;
      }
      dispatch({ type: 'FETCH_SESSIONS_FAILURE', payload: errorMessage });
    }
  }, [authToken, dispatch]);

  const fetchMessages = useCallback(async (sessionId: string) => {
    if (!authToken || !sessionId) {
      dispatch({ type: 'FETCH_HISTORY_FAILURE', payload: "Auth token or session ID missing." });
      return;
    }
    console.log(`[ChatContext] fetchMessages: Attempting to fetch messages for sessionId: ${sessionId}`);
    dispatch({ type: 'FETCH_HISTORY_START' });
    try {
      const response = await apiClient.get<any[]>(`/api/v1/chat/sessions/${sessionId}/messages`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      console.log(`[ChatContext] fetchMessages: API response received for ${sessionId}`, response.data);
      const messages: ChatMessage[] = response.data.map((apiMsg: any) => ({
        id: apiMsg.id || uuidv4(),
        content: apiMsg.content,
        sender: apiMsg.role === 'user' ? 'USER' : 'AI',
        timestamp: apiMsg.timestamp || apiMsg.created_at || new Date().toISOString(),
        session_id: sessionId // Ensure messages fetched for a session have that session ID
      }));
      console.log(`[ChatContext] fetchMessages: Parsed messages for ${sessionId}`, messages);
      dispatch({ type: 'FETCH_HISTORY_SUCCESS', payload: messages });
    } catch (err) { 
      console.error(`[ChatContext] fetchMessages: Error fetching messages for ${sessionId}`, err);
      dispatch({ type: 'FETCH_HISTORY_FAILURE', payload: (err as Error).message }); 
    }
  }, [authToken, dispatch]);

  const archiveSession = useCallback(async (sessionId: string): Promise<void> => {
    if (!authToken) { 
      console.error("Archive: No auth token provided.");
      return Promise.reject(new Error("Authentication token not available.")); 
    }
    try {
      await chatApi.archiveSession(authToken, sessionId);
      dispatch({ type: 'ARCHIVE_SESSION_SUCCESS', payload: { sessionId } });
    } catch (error) {
      console.error("Error archiving session in provider:", error);
      throw error; 
    }
  }, [authToken, dispatch]);

  const fetchArchivedSessions = useCallback(async (chatType: ChatTypeValue) => {
    if (!authToken) { 
      dispatch({ type: 'FETCH_ARCHIVED_SESSIONS_FAILURE', payload: "Authentication token not found." });
      return;
    }
    dispatch({ type: 'FETCH_ARCHIVED_SESSIONS_START' });
    try {
      const response = await chatApi.getArchivedSessions(authToken, chatType);
      dispatch({ type: 'FETCH_ARCHIVED_SESSIONS_SUCCESS', payload: response.data });
    } catch (error) {
      console.error("Error fetching archived sessions:", error);
      dispatch({ type: 'FETCH_ARCHIVED_SESSIONS_FAILURE', payload: error instanceof Error ? error.message : String(error) });
    }
  }, [authToken, dispatch]);

  const unarchiveSession = useCallback(async (sessionId: string): Promise<void> => {
    if (!authToken) { 
      console.error("Unarchive: No auth token provided.");
      return Promise.reject(new Error("Authentication token not available."));
    }
    try {
      await chatApi.unarchiveSession(authToken, sessionId);
      dispatch({ type: 'UNARCHIVE_SESSION_SUCCESS', payload: { sessionId } });
      if (state.currentChatType) {
        fetchSessions(state.currentChatType);
      }
    } catch (error) {
      console.error("Error unarchiving session in provider:", error);
      throw error;
    }
  }, [authToken, dispatch, state.currentChatType, fetchSessions]);

  useEffect(() => {
    setAuthToken(initialAuthToken);
  }, [initialAuthToken]);

  useEffect(() => {
    if (state.currentChatType && authToken) {
      fetchSessions(state.currentChatType);
    } else if (!authToken) {
      dispatch({ type: 'FETCH_SESSIONS_SUCCESS', payload: [] });
    }
  }, [state.currentChatType, authToken, fetchSessions]);

  // }, [state.sessionId, authToken, fetchMessages, state.justStartedNewChat, dispatch]);

  /*  // WebSocketの接続試行とクリーンアップを行うuseEffectをコメントアウト
  useEffect(() => {
    if (authToken && state.currentChatType) {
        console.log("Attempting to connect WebSocket...");
        connectWebSocket();
    } else {
        console.log("WebSocket not connecting: authToken or currentChatType missing.");
        disconnectWebSocket();
    }
    return () => {
        console.log("Cleaning up WebSocket connection...");
        disconnectWebSocket();
    };
  }, [authToken, state.currentChatType, connectWebSocket, disconnectWebSocket]);
  */

  const contextValue = useMemo(() => ({
    ...state,
    dispatch,
    connectWebSocket,
    disconnectWebSocket,
    sendMessage,
    clearChat,
    changeChatType,
    startNewChat, 
    fetchMessages,
    fetchSessions,
    archiveSession,
    fetchArchivedSessions,
    unarchiveSession,
    authToken,
    isConnected,
  }), [
    state, dispatch, connectWebSocket, disconnectWebSocket, sendMessage, 
    clearChat, changeChatType, startNewChat, 
    fetchMessages, fetchSessions, archiveSession, 
    fetchArchivedSessions, unarchiveSession,
    authToken, isConnected
  ]);

  return <ChatContext.Provider value={contextValue}>{children}</ChatContext.Provider>;
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}; 
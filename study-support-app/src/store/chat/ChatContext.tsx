import React, { createContext, useReducer, useContext, ReactNode, useCallback, useEffect, useMemo, useState, useRef } from 'react';
import { ChatState, ChatAction, ChatMessage, ChatSubmitRequest, ChatTypeValue, ChatTypeEnum, ChatSession, MessageSender } from '@/types/chat'; // ChatSessionSummary を ChatSession に変更し、MessageSender を追加
import { useChatWebSocket, WebSocketMessage } from '@/hooks/useChatWebSocket'; // パスを修正
import { v4 as uuidv4 } from 'uuid';
import { apiClient } from '@/lib/api-client'; // apiClient をインポート
import { chatApi } from '@/lib/api-client'; // chatApiをインポート

const initialState: ChatState = {
  sessionId: null,
  messages: [],
  isLoading: false,
  error: null,
  currentChatType: ChatTypeEnum.GENERAL,
  sessions: [],
  isLoadingSessions: false,
  errorSessions: null,
  archivedSessions: [],
  isLoadingArchivedSessions: false,
  errorArchivedSessions: null,
  justStartedNewChat: false,
  viewingSessionStatus: null,
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
        justStartedNewChat: sessionActuallyChanged ? false : state.justStartedNewChat,
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
      return {
        ...state,
        sessionId: action.payload.sessionId,
        currentChatType: action.payload.chatType,
        messages: [],
        isLoading: false,
        error: null,
        justStartedNewChat: true,
        viewingSessionStatus: 'ACTIVE',
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
  startNewChat: (chatType: ChatTypeValue) => void;
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
    if (wsMessage.session_id && state.sessionId !== wsMessage.session_id && !state.sessionId) {
        dispatch({ type: 'SET_SESSION_ID', payload: { id: wsMessage.session_id || null, status: 'ACTIVE' } });
    }

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
              id: wsMessage.session_id || uuidv4(),
              sender: 'AI',
              content: wsMessage.content,
              timestamp: now,
              isStreaming: true
            };
          }
          if (aiMessage) dispatch({ type: 'ADD_MESSAGE', payload: aiMessage });
        }
        break;
      case 'done':
        const finalAiMsgIndex = state.messages.findIndex(m => m.sender === 'AI' && m.isStreaming);
        if (finalAiMsgIndex !== -1) {
          aiMessage = {
            ...state.messages[finalAiMsgIndex],
            isStreaming: false,
            isLoading: false,
            isError: wsMessage.error,
            timestamp: now,
          };
          if (aiMessage) dispatch({ type: 'ADD_MESSAGE', payload: aiMessage });
        }
        if (wsMessage.session_id && !state.sessionId) {
          dispatch({ type: 'SET_SESSION_ID', payload: { id: wsMessage.session_id || null, status: 'ACTIVE' } });
        }
        dispatch({ type: 'SEND_MESSAGE_SUCCESS' });
        break;
      case 'error':
        console.error("Error from WebSocket:", wsMessage.detail);
        dispatch({ type: 'SEND_MESSAGE_FAILURE', payload: wsMessage.detail || 'WebSocket error' });
        break;
      case 'info':
        console.info("Info from server:", wsMessage.message);
        break;
      default:
        console.warn('Received unknown WebSocket message type:', wsMessage);
    }
  }, [state.sessionId, state.messages, dispatch]);

  const handleWebSocketError = useCallback((error: Event | Error) => {
    console.error("WebSocket Provider Error:", error);
    // const errorMessage = error instanceof Error ? error.message : "WebSocket connection error";
    // dispatch({ type: 'SET_ERROR', payload: errorMessage }); // SET_ERROR is not in ChatAction
  }, []); // Removed dispatch from dependencies as it's not used
  
  const handleWebSocketOpen = useCallback(() => {
    console.log("WebSocket Provider: Connection Opened");
    // dispatch({ type: 'SET_ERROR', payload: null }); // SET_ERROR is not in ChatAction
    setIsConnected(true);
  }, []); // Removed dispatch from dependencies

  const handleWebSocketClose = useCallback((event: CloseEvent) => {
    console.log("WebSocket Provider: Connection Closed", event.reason, event.code);
    setIsConnected(false);
    // if (event.code !== 1000 && event.code !== 1005) {
    //     dispatch({ type: 'SET_ERROR', payload: `WebSocket disconnected: ${event.reason || 'Connection lost'}` }); // SET_ERROR is not in ChatAction
    // }
  }, []); // Removed dispatch from dependencies

  const { sendMessage: wsSendMessage, isConnected: wsIsConnected, webSocketRef } = useChatWebSocket({
    socketUrl: socketUrl,
    token: authToken,
    onMessageReceived: handleWebSocketMessage,
    onError: handleWebSocketError,
    onOpen: handleWebSocketOpen,
    onClose: handleWebSocketClose,
  });

  useEffect(() => {
      setIsConnected(wsIsConnected);
  }, [wsIsConnected]);

  const connectWebSocket = useCallback(() => {
    if (webSocketRef.current?.readyState !== WebSocket.OPEN && webSocketRef.current?.readyState !== WebSocket.CONNECTING) {
      console.log("Attempting to trigger re-connection for WebSocket.");
    }
  }, [webSocketRef]);

  const disconnectWebSocket = useCallback(() => {
    webSocketRef.current?.close(1000, 'User disconnected');
    setIsConnected(false);
  }, [webSocketRef]);

  const sendMessage = useCallback((messageContent: string) => {
    if (!isConnected || webSocketRef.current?.readyState !== WebSocket.OPEN) {
      console.error('Cannot send message, WebSocket is not connected or not open.');
      dispatch({ type: 'SEND_MESSAGE_FAILURE', payload: 'WebSocket not connected' });
      return;
    }
    const userMessage: ChatMessage = {
      id: uuidv4(),
      content: messageContent,
      sender: 'USER',
      timestamp: new Date().toISOString(),
      isLoading: true,
    };
    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    dispatch({ type: 'SEND_MESSAGE_START' });

    const request: ChatSubmitRequest = {
      message: messageContent,
      session_id: state.sessionId,
      chat_type: state.currentChatType,
    };
    wsSendMessage(request);
  }, [isConnected, state.sessionId, state.currentChatType, dispatch, wsSendMessage, webSocketRef]);

  const clearChat = useCallback((chatType?: ChatTypeValue) => {
    dispatch({ type: 'SET_SESSION_ID', payload: { id: null, status: null } });
    dispatch({ type: 'FETCH_HISTORY_SUCCESS', payload: [] });
    dispatch({ type: 'SET_CURRENT_CHAT_TYPE', payload: chatType || initialState.currentChatType });
  }, [dispatch]);

  const changeChatType = useCallback((chatType: ChatTypeValue) => {
    if (state.currentChatType !== chatType) {
        console.log(`Changing chat type to: ${chatType}`);
        dispatch({ type: 'SET_CURRENT_CHAT_TYPE', payload: chatType });
    }
  }, [state.currentChatType, dispatch]);
  
  const startNewChat = useCallback(async (chatType: ChatTypeValue): Promise<string | null> => {
    const newSessionId = uuidv4();
    console.log(`Starting new chat for type ${chatType} with session ID: ${newSessionId}`);
    dispatch({ type: 'START_NEW_CHAT_SESSION', payload: { sessionId: newSessionId, chatType } });
    return newSessionId;
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
  }, [authToken]);

  const fetchMessages = useCallback(async (sessionId: string) => {
    if (!authToken || !sessionId) {
      // dispatch({ type: 'SET_ERROR', payload: "Auth token or session ID missing." }); // SET_ERROR is not in ChatAction
      dispatch({ type: 'FETCH_HISTORY_FAILURE', payload: "Auth token or session ID missing." });
      return;
    }
    dispatch({ type: 'FETCH_HISTORY_START' });
    try {
      const response = await apiClient.get<any[]>(`/api/v1/chat/sessions/${sessionId}/messages`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      const messages: ChatMessage[] = response.data.map((apiMsg: any) => ({
        id: apiMsg.id || uuidv4(),
        content: apiMsg.content,
        sender: apiMsg.role === 'user' ? 'USER' : 'AI',
        timestamp: apiMsg.timestamp || apiMsg.created_at || new Date().toISOString(),
      }));
      dispatch({ type: 'FETCH_HISTORY_SUCCESS', payload: messages });
    } catch (err) { 
      // dispatch({ type: 'SET_ERROR', payload: (err as Error).message }); // SET_ERROR is not in ChatAction
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
      dispatch({ type: 'FETCH_ARCHIVED_SESSIONS_FAILURE', payload: error instanceof Error ? error : String(error) });
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

  useEffect(() => {
    if (state.sessionId && authToken) {
      if (state.justStartedNewChat) {
        console.log(`[CONTEXT_EFFECT] New chat session ${state.sessionId} just started. Skipping initial fetchMessages.`);
      } else {
        console.log(`[CONTEXT_EFFECT] Session ID ${state.sessionId} detected. Not a new chat start or already acknowledged. Fetching messages.`);
        fetchMessages(state.sessionId);
      }
    } else if (!state.sessionId) {
      console.log("[CONTEXT_EFFECT] Session ID is null, clearing messages.");
      dispatch({ type: 'FETCH_HISTORY_SUCCESS', payload: [] });
    }
  }, [state.sessionId, authToken, fetchMessages, state.justStartedNewChat, dispatch]);

  useEffect(() => {
    if (initialAuthToken) {
      setAuthToken(initialAuthToken);
    }
  }, [initialAuthToken]);

  useEffect(() => {
    if (authToken && state.currentChatType) {
        console.log("Attempting to connect WebSocket...");
        connectWebSocket();
    }
    return () => {
        console.log("Cleaning up WebSocket connection...");
        disconnectWebSocket();
    };
  }, [authToken, state.currentChatType, connectWebSocket, disconnectWebSocket]);

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
    clearChat, changeChatType,
    startNewChat, fetchMessages, fetchSessions, archiveSession, 
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
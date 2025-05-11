"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Loader2, SendHorizontal } from 'lucide-react';
import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChecklistEvaluation } from './ChecklistEvaluation';
import { ChatTypeValue, ChatTypeEnum, ChatMessage as FrontendChatMessage, type SessionStatusValue } from '@/types/chat'; // ChatMessage を FrontendChatMessageとしてインポート, SessionStatusValue を追加インポート
import { useAuthHelpers } from '@/lib/authUtils';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useRouter, usePathname } from 'next/navigation';
import { useChat } from '@/store/chat/ChatContext';

interface ChatPageProps {
  initialChatType?: ChatTypeValue;
  initialSessionId?: string;
}

const ChatPage: React.FC<ChatPageProps> = ({ initialChatType, initialSessionId }) => {
  const router = useRouter();
  const pathname = usePathname();

  const {
    messages,
    isLoading: chatIsLoading,
    error: chatError,
    isConnected,
    sendMessage: sendChatMessage,
    changeChatType,
    currentChatType: contextChatType,
    sessionId: contextSessionId,
    sessions,
    archivedSessions,
    viewingSessionStatus,
    justStartedNewChat,
    dispatch,
  } = useChat();

  const [newMessage, setNewMessage] = useState('');
  const checklistRef = useRef<{ triggerUpdate: () => void }>(null);
  const { hasPermission, isLoading: isAuthLoading } = useAuthHelpers();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const prevContextSessionIdRef = useRef<string | null | undefined>(contextSessionId);

  // Derived state from URL
  const getChatInfoFromPath = () => {
    const pathSegments = pathname.split('/').filter(Boolean);
    const chatSegmentIndex = pathSegments.findIndex(segment => segment === 'chat');
    // Ensure chatSegmentIndex is found and there's a segment after 'chat' for type
    const typeFromUrl = chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 1 ? pathSegments[chatSegmentIndex + 1].toUpperCase() as ChatTypeValue : undefined;
    // Ensure there's a segment after type for session ID
    const sessionIdFromUrl = chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 2 ? pathSegments[chatSegmentIndex + 2] : undefined;
    return { typeFromUrl, sessionIdFromUrl };
  };

  useEffect(() => {
    const { typeFromUrl, sessionIdFromUrl } = getChatInfoFromPath();
    const previousContextSessionId = prevContextSessionIdRef.current;

    console.log(`[DEBUG ChatPage UnifiedEffect] Start. Path: ${pathname}, PrevCtxSessID: ${previousContextSessionId}, Ctx: CType=${contextChatType} CSessID=${contextSessionId} JustNew=${justStartedNewChat}, URL: UType=${typeFromUrl} USessID=${sessionIdFromUrl}`);

    // Priority 1: New Chat URL Update
    if (contextChatType && contextSessionId && !sessionIdFromUrl && 
        (previousContextSessionId === null || previousContextSessionId === undefined)) {
      const newChatPath = `/chat/${contextChatType.toLowerCase()}/${contextSessionId}`;
      console.log(`[DEBUG ChatPage UnifiedEffect Priority 1] ContextSessionId changed from ${previousContextSessionId} to ${contextSessionId}. URL has no session. Updating URL to: ${newChatPath}`);
      router.replace(newChatPath);
      // prevContextSessionIdRef.current is updated at the end of the effect
      return; 
    }

    // Priority 2: Synchronize Context from URL and other cases
    if (typeFromUrl && typeFromUrl !== contextChatType) {
      console.log(`[DEBUG ChatPage UnifiedEffect] URL chat type (${typeFromUrl}) differs from context (${contextChatType}). Changing context chat type.`);
      changeChatType(typeFromUrl);
      // prevContextSessionIdRef.current is updated at the end
      return;
    }

    if (typeFromUrl && typeFromUrl === contextChatType) {
      if (sessionIdFromUrl && sessionIdFromUrl !== contextSessionId) {
        const foundSession = sessions.find(s => s.id === sessionIdFromUrl) || archivedSessions.find(s => s.id === sessionIdFromUrl);
        const sessionStatus = foundSession?.status;
        console.log(`[DEBUG ChatPage UnifiedEffect] URL session ID (${sessionIdFromUrl}) differs from context (${contextSessionId}). Setting context session ID. Status: ${sessionStatus}`);
        dispatch({ type: 'SET_SESSION_ID', payload: { id: sessionIdFromUrl, status: sessionStatus } });
        // prevContextSessionIdRef.current is updated at the end
        return;
      } else if (!sessionIdFromUrl && contextSessionId && !justStartedNewChat) {
        if (previousContextSessionId !== null && previousContextSessionId !== undefined) {
            console.log(`[DEBUG ChatPage UnifiedEffect] URL has no session, context has ${contextSessionId} (was ${previousContextSessionId}). Clearing context session.`);
            dispatch({ type: 'SET_SESSION_ID', payload: { id: null, status: null } });
            // prevContextSessionIdRef.current is updated at the end
            return;
        } else {
            console.log(`[DEBUG ChatPage UnifiedEffect] URL has no session, context has ${contextSessionId}, prev was ${previousContextSessionId}. Not clearing, likely new session flow or waiting for URL update.`);
        }
      } else if (sessionIdFromUrl && !contextSessionId && !justStartedNewChat && typeFromUrl === contextChatType) {
        const foundSession = sessions.find(s => s.id === sessionIdFromUrl) || archivedSessions.find(s => s.id === sessionIdFromUrl);
        const sessionStatus = foundSession?.status;
        console.log(`[DEBUG ChatPage UnifiedEffect] URL has session ${sessionIdFromUrl}, context has no session (not new chat). Setting context session ID. Status: ${sessionStatus}`);
        dispatch({ type: 'SET_SESSION_ID', payload: { id: sessionIdFromUrl, status: sessionStatus } });
        // prevContextSessionIdRef.current is updated at the end
        return;
      }
    }
    
    if (!typeFromUrl && initialChatType && initialChatType !== contextChatType && !contextChatType) {
        console.log(`[DEBUG ChatPage UnifiedEffect] No URL type, initialChatType (${initialChatType}) provided. Setting context chat type.`);
        changeChatType(initialChatType);
        // prevContextSessionIdRef.current is updated at the end
        return;
    }
    
    if (justStartedNewChat && typeFromUrl && !sessionIdFromUrl && !contextSessionId) {
        console.log(`[DEBUG ChatPage UnifiedEffect] New chat state: URL is /chat/${typeFromUrl}, context session is null. Waiting for backend session ID.`);
    }

    console.log(`[DEBUG ChatPage UnifiedEffect] End. Path: ${pathname}, PrevCtxSessID: ${previousContextSessionId}, Ctx: CType=${contextChatType} CSessID=${contextSessionId} JustNew=${justStartedNewChat}, URL: UType=${typeFromUrl} USessID=${sessionIdFromUrl}`);
    
    prevContextSessionIdRef.current = contextSessionId;

  }, [
    pathname, 
    contextChatType, 
    contextSessionId, 
    justStartedNewChat, 
    initialChatType,
    sessions, 
    archivedSessions, 
    changeChatType, 
    dispatch, 
    router
    // prevContextSessionIdRef should not be in dependencies
  ]);

  const canSendMessagePermission = hasPermission('chat_message_send');

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || chatIsLoading || isAuthLoading || !canSendMessagePermission || !isConnected) return;

    sendChatMessage(newMessage);
    setNewMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };
  
  const activeChatType = contextChatType; // Use the renamed context variable

  return (
    <div className="flex h-screen min-h-[500px] w-full overflow-hidden bg-gray-100">
      <ChatSidebar />
      <div className="flex-1 flex flex-col h-full min-h-0 border-l border-gray-300">
        <ChatWindow
        />
        <footer className="flex-none bg-white border-t border-gray-200 px-6 py-3 shadow-sm">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto w-full">
            <div className="relative flex items-center">
              <Textarea
                ref={textareaRef}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder={
                  !isConnected 
                    ? "接続していません..." 
                    : (!canSendMessagePermission 
                      ? "メッセージ送信権限がありません" 
                      : (viewingSessionStatus === 'ARCHIVED' 
                        ? "アーカイブされたチャットです (読み取り専用)" 
                        : "メッセージを入力... (Shift+Enterで改行)"))
                }
                rows={1}
                className="flex-1 py-3 px-4 pr-12 bg-gray-50 border-0 rounded-full focus:ring-2 focus:ring-indigo-500 focus:bg-white resize-none min-h-[48px] max-h-[150px] overflow-y-auto shadow-sm transition-all duration-200 disabled:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-70"
                disabled={!isConnected || chatIsLoading || isAuthLoading || !canSendMessagePermission || viewingSessionStatus === 'ARCHIVED'}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
              />
              <Button
                type="submit"
                disabled={!isConnected || !newMessage.trim() || chatIsLoading || isAuthLoading || !canSendMessagePermission || viewingSessionStatus === 'ARCHIVED'}
                className="absolute right-2 h-10 w-10 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center transition-all duration-200 disabled:opacity-60 disabled:bg-gray-400 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                size="icon"
              >
                {chatIsLoading && !messages.find(m=>m.isStreaming) ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <SendHorizontal className="h-5 w-5" />
                )}
              </Button>
            </div>
            
            {/* 接続状態とパーミッション情報 */}
            <div className="flex justify-between items-center mt-2 px-1 text-xs text-gray-500">
              <div className="flex items-center">
                {isConnected ? (
                  <span className="flex items-center text-green-600">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-500 mr-1.5 animate-pulse"></span>
                    接続中
                  </span>
                ) : (
                  <span className="flex items-center text-red-600">
                    <span className="h-1.5 w-1.5 rounded-full bg-red-500 mr-1.5"></span>
                    未接続
                  </span>
                )}
              </div>
              
              {/* チャットタイプ表示 */}
              {activeChatType && (
                <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-medium">
                  {activeChatType === ChatTypeEnum.STUDY_SUPPORT ? '学習支援' :
                   activeChatType === ChatTypeEnum.SELF_ANALYSIS ? '自己分析' :
                   activeChatType === ChatTypeEnum.ADMISSION ? '総合型選抜' : 
                   activeChatType === ChatTypeEnum.FAQ ? 'FAQ' : activeChatType}
                </span>
              )}
            </div>
          </form>
        </footer>
      </div>
      {/* {currentSessionIdFromContext && currentChatType === ChatTypeEnum.SELF_ANALYSIS && (
        <div className="w-80 border-l border-gray-300 bg-gray-50 p-4 overflow-y-auto hidden lg:block">
          <ChecklistEvaluation
            ref={checklistRef}
            chatId={contextSessionId} // Use renamed context variable
            sessionType={contextChatType as ChatTypeEnum} // Use renamed context variable
          />
        </div>
      )} */}
    </div>
  );
};

export default ChatPage;
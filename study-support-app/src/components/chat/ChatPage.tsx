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
    currentChatType,
    sessionId: currentSessionIdFromContext,
    sessions,
    archivedSessions,
    viewingSessionStatus,
    dispatch,
  } = useChat();

  const [newMessage, setNewMessage] = useState('');
  const checklistRef = useRef<{ triggerUpdate: () => void }>(null);
  const { hasPermission, isLoading: isAuthLoading } = useAuthHelpers();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const typeToSet = initialChatType || ChatTypeEnum.GENERAL;
    console.log("[DEBUG] ChatPage Initial Effect - Props:", { initialChatType, initialSessionId }, "Context:", { currentChatTypeCtx: currentChatType, currentSessionIdCtx: currentSessionIdFromContext }, "Pathname:", pathname);

    if (typeToSet !== currentChatType) {
      console.log(`[DEBUG] ChatPage Initial Effect - Dispatching changeChatType. Type to set: ${typeToSet}, Context type: ${currentChatType}`);
      changeChatType(typeToSet);
    }

    const pathSegments = pathname.split('/').filter(Boolean);
    const chatSegmentIndex = pathSegments.findIndex(segment => segment === 'chat');
    let sessionIdFromUrl: string | undefined = undefined;
    if (chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 2) {
        sessionIdFromUrl = pathSegments[chatSegmentIndex + 2];
    }
    console.log("[DEBUG] ChatPage Initial Effect - Parsed from URL:", { sessionIdFromUrl });

    let sessionToSetId: string | null = null;
    let sessionToSetStatus: SessionStatusValue | undefined = undefined;

    if (sessionIdFromUrl) {
      sessionToSetId = sessionIdFromUrl;
      const foundSession = sessions.find(s => s.id === sessionIdFromUrl) || archivedSessions.find(s => s.id === sessionIdFromUrl);
      sessionToSetStatus = foundSession?.status;
    } else if (initialSessionId) {
      sessionToSetId = initialSessionId;
      const foundSession = sessions.find(s => s.id === initialSessionId) || archivedSessions.find(s => s.id === initialSessionId);
      sessionToSetStatus = foundSession?.status;
    }

    if (sessionToSetId && sessionToSetId !== currentSessionIdFromContext) {
      console.log(`[DEBUG] ChatPage Initial Effect - Dispatching SET_SESSION_ID. Target ID: ${sessionToSetId}, Target Status: ${sessionToSetStatus || 'default ACTIVE'}`);
      dispatch({ type: 'SET_SESSION_ID', payload: { id: sessionToSetId, status: sessionToSetStatus } });
    } else if (!sessionToSetId && currentSessionIdFromContext) {
      console.log(`[DEBUG] ChatPage Initial Effect - No session ID from URL or props. Context ID ${currentSessionIdFromContext} is kept or should be cleared by other effects.`);
    }
  }, [pathname, initialChatType, initialSessionId, currentChatType, changeChatType, dispatch, sessions, archivedSessions]);

  useEffect(() => {
    const pathSegments = pathname.split('/').filter(Boolean);
    const chatSegmentIndex = pathSegments.findIndex(segment => segment === 'chat');
    let typeInUrl = chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 1 ? pathSegments[chatSegmentIndex + 1] : null;
    let sessionIdInUrl = chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 2 ? pathSegments[chatSegmentIndex + 2] : null;

    console.log("[DEBUG] ChatPage Context Sync Effect - Current Context:", { currentChatType, currentSessionIdFromContext }, "Current URL:", { typeInUrl: typeInUrl?.toUpperCase(), sessionIdInUrl, pathname });

    if (currentChatType && currentSessionIdFromContext) {
      if (typeInUrl?.toUpperCase() !== currentChatType || sessionIdInUrl !== currentSessionIdFromContext) {
        const newPath = `/chat/${currentChatType.toLowerCase()}/${currentSessionIdFromContext}`;
        console.log(`[DEBUG] ChatPage Context Sync Effect (with sessionID) - Updating URL to: ${newPath} from ${pathname}`);
        router.replace(newPath);
      }
    } else if (currentChatType && !currentSessionIdFromContext) {
      if (typeInUrl?.toUpperCase() !== currentChatType || sessionIdInUrl) { 
        const newPath = `/chat/${currentChatType.toLowerCase()}`;
        console.log(`[DEBUG] ChatPage Context Sync Effect (no sessionID) - Updating URL to: ${newPath} from ${pathname}`);
        router.replace(newPath);
      }
    }
  }, [currentSessionIdFromContext, currentChatType, router, pathname]);

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
  
  const activeChatType = currentChatType;

  return (
    <div className="flex h-full bg-gray-100">
      <ChatSidebar />
      <div className="flex-1 flex flex-col border-l border-gray-300">
        <ChatWindow
        />
        <footer className="flex-none bg-white border-t border-gray-200 px-4 py-3">
          <form onSubmit={handleSendMessage} className="flex space-x-3 items-center">
            <Textarea
              ref={textareaRef}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={!isConnected ? "接続していません..." : (!canSendMessagePermission ? "メッセージ送信権限がありません" : (viewingSessionStatus === 'ARCHIVED' ? "アーカイブされたチャットです (読み取り専用)" : "メッセージを入力... (Shift+Enterで改行)"))}
              rows={1}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[44px] max-h-[150px] overflow-y-auto disabled:cursor-not-allowed disabled:opacity-60"
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
              className="h-[44px] w-[44px] flex-shrink-0 flex items-center justify-center bg-blue-600 text-white rounded-full hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:bg-blue-400 transition-colors duration-150"
              size="icon"
            >
              {chatIsLoading && !messages.find(m=>m.isStreaming) ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <SendHorizontal className="h-5 w-5" />
              )}
            </Button>
          </form>
        </footer>
      </div>
      {/* {currentSessionIdFromContext && currentChatType === ChatTypeEnum.SELF_ANALYSIS && (
        <div className="w-80 border-l border-gray-300 bg-gray-50 p-4 overflow-y-auto hidden lg:block">
          <ChecklistEvaluation
            ref={checklistRef}
            chatId={currentSessionIdFromContext}
            sessionType={currentChatType as ChatTypeEnum} 
          />
        </div>
      )} */}
    </div>
  );
};

export default ChatPage;
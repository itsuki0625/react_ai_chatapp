"use client";

import React, { useRef, useEffect, useCallback } from 'react';
import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatTypeValue, ChatTypeEnum } from '@/types/chat';
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
    isLoading: chatIsLoading,
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

  const checklistRef = useRef<{ triggerUpdate: () => void }>(null);
  const prevContextSessionIdRef = useRef<string | null | undefined>(contextSessionId);

  // Derived state from URL
  const getChatInfoFromPath = useCallback(() => {
    const pathSegments = pathname.split('/').filter(Boolean);
    const chatSegmentIndex = pathSegments.findIndex(segment => segment === 'chat');
    
    // Ensure chatSegmentIndex is found and there's a segment after 'chat' for type
    let typeFromUrl = undefined;
    if (chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 1) {
      const rawType = pathSegments[chatSegmentIndex + 1];
      // URLの形式（ハイフン）をEnum値（アンダースコア）に変換
      typeFromUrl = rawType.replace('-', '_').toUpperCase() as ChatTypeValue;
      console.log('[DEBUG] Path parsing:', rawType, '->', typeFromUrl);
    }
    
    // Ensure there's a segment after type for session ID
    const sessionIdFromUrl = chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 2 ? pathSegments[chatSegmentIndex + 2] : undefined;
    
    return { typeFromUrl, sessionIdFromUrl };
  }, [pathname]);

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
    router,
    getChatInfoFromPath
  ]);
  
  const activeChatType = contextChatType;

  return (
    <div className="flex h-full w-full overflow-hidden bg-slate-50 rounded-lg shadow-sm border border-slate-200">
      <ChatSidebar />
      <div className="flex-1 flex flex-col h-full border-l border-slate-200">
        <div className="bg-white py-4 px-6 border-b border-slate-200 hidden sm:block shadow-sm sticky top-0 z-10">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-lg font-semibold text-slate-800">
              {contextChatType === ChatTypeEnum.SELF_ANALYSIS ? '自己分析AI' :
               contextChatType === ChatTypeEnum.ADMISSION ? '総合型選抜AI' :
               contextChatType === ChatTypeEnum.STUDY_SUPPORT ? '学習サポートAI' :
               contextChatType === ChatTypeEnum.FAQ ? 'FAQヘルプAI' : 'AIチャット'}
            </h1>
            <p className="text-sm text-slate-500">
              {contextChatType === ChatTypeEnum.SELF_ANALYSIS ? '自己分析を深め、自分の強みを見つけましょう' :
               contextChatType === ChatTypeEnum.ADMISSION ? '総合型選抜に関する相談や志望理由書の添削を行います' :
               contextChatType === ChatTypeEnum.STUDY_SUPPORT ? '学習に関する質問や課題の解決をサポートします' :
               contextChatType === ChatTypeEnum.FAQ ? 'よくある質問に回答します' : 'AIとチャットして情報を得ましょう'}
            </p>
          </div>
        </div>
        <div className="flex-1 overflow-hidden relative">
          <ChatWindow />
          <div className="absolute bottom-0 left-0 right-0 z-10">
            <div className="px-4 py-3 bg-white border-t border-slate-200 shadow-lg">
              <ChatInput 
                onSendMessage={sendChatMessage} 
                isLoading={chatIsLoading} 
              />
              
              {/* 接続状態とチャットタイプ情報 */}
              <div className="flex justify-between items-center mt-2 px-1 text-xs text-slate-500 max-w-4xl mx-auto">
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
                  <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium">
                    {activeChatType === ChatTypeEnum.STUDY_SUPPORT ? '学習支援' :
                     activeChatType === ChatTypeEnum.SELF_ANALYSIS ? '自己分析' :
                     activeChatType === ChatTypeEnum.ADMISSION ? '総合型選抜' : 
                     activeChatType === ChatTypeEnum.FAQ ? 'FAQ' : activeChatType}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
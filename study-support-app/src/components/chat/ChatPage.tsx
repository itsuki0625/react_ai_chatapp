"use client";

import React, { useRef, useEffect, useCallback } from 'react';
import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatTypeValue, ChatTypeEnum } from '@/types/chat';
import { useRouter, usePathname } from 'next/navigation';
import { useChat } from '@/store/chat/ChatContext';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Lock, Zap, MessageSquare, Star } from 'lucide-react';
import Link from 'next/link';

interface ChatPageProps {
  initialChatType?: ChatTypeValue;
  initialSessionId?: string;
}

// フリーユーザー制限コンポーネント
const FreeUserRestriction = () => {
  return (
    <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-purple-50">
      <Card className="max-w-md w-full border-2 border-dashed border-blue-200">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mb-4">
            <Lock className="h-6 w-6 text-blue-600" />
          </div>
          <CardTitle className="text-xl text-gray-900">AIチャット機能</CardTitle>
          <CardDescription>
            この機能は有料プランでご利用いただけます
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
              <Zap className="h-5 w-5 text-yellow-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-sm text-gray-900">AI学習支援</p>
                <p className="text-xs text-gray-600">勉強法の相談や質問対応</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
              <MessageSquare className="h-5 w-5 text-blue-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-sm text-gray-900">自己分析AI</p>
                <p className="text-xs text-gray-600">適性診断と強み発見</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
              <Star className="h-5 w-5 text-purple-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-sm text-gray-900">総合型選抜AI</p>
                <p className="text-xs text-gray-600">入試対策と志望理由書添削</p>
              </div>
            </div>
          </div>
          
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs text-gray-600 mb-3 text-center">
              スタンダードプラン以上でご利用いただけます
            </p>
            <Link href="/subscription" className="w-full">
              <Button className="w-full bg-blue-600 hover:bg-blue-700">
                プランを確認する
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const ChatPage: React.FC<ChatPageProps> = ({ initialChatType, initialSessionId }) => {
  const { data: session } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  // ユーザーのプラン判定
  const userRole = session?.user?.role;
  const isFreeUser = userRole === 'フリー';
  const hasAccessToChat = !isFreeUser || session?.user?.isAdmin;

  const {
    isLoading: chatIsLoading,
    isWebSocketConnected: isConnected,
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
      // URLの形式（ハイフン）をEnum値（スネークケース）に変換
      typeFromUrl = rawType.replace(/-/g, '_').toLowerCase() as ChatTypeValue;
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

    // 新しいチャットページに遷移したとき、以前のセッションをクリア
    if (typeFromUrl && !sessionIdFromUrl && contextSessionId) {
      console.log(`[DEBUG ChatPage UnifiedEffect] Detected new chat path /chat/${typeFromUrl}, clearing previous session.`);
      dispatch({ type: 'CLEAR_CHAT', payload: { chatType: contextChatType } });
      return;
    }

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
        
        {/* フリーユーザー制限表示 */}
        {!hasAccessToChat ? (
          <FreeUserRestriction />
        ) : (
          <>
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
          </>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
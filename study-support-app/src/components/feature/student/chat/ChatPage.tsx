"use client";

import React, { useRef, useEffect, useCallback } from 'react';
import ChatSidebar from '@/components/feature/student/chat/ChatSidebar';
import ChatWindow from '@/components/feature/student/chat/ChatWindow';
import { ChatInput } from '@/components/feature/student/chat/ChatInput';
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
            <Link href="/student/subscription" className="w-full">
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

// カスタムフック: パス情報から チャット情報を取得
const useChatPathInfo = (pathname: string) => {
  return useCallback(() => {
    const pathSegments = pathname.split('/').filter(Boolean);
    const chatSegmentIndex = pathSegments.findIndex(segment => segment === 'chat');
    
    let typeFromUrl = undefined;
    if (chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 1) {
      const rawType = pathSegments[chatSegmentIndex + 1];
      // URLの形式（ハイフン）をEnum値（スネークケース）に変換
      typeFromUrl = rawType.replace(/-/g, '_').toLowerCase() as ChatTypeValue;
    }
    
    const sessionIdFromUrl = chatSegmentIndex !== -1 && pathSegments.length > chatSegmentIndex + 2 ? 
      pathSegments[chatSegmentIndex + 2] : undefined;
    
    return { typeFromUrl, sessionIdFromUrl };
  }, [pathname]);
};

// カスタムフック: セッション状態管理
const useSessionSync = () => {
  const {
    currentChatType: contextChatType,
    sessionId: contextSessionId,
    sessions,
    archivedSessions,
    justStartedNewChat,
    changeChatType,
    dispatch,
  } = useChat();

  const router = useRouter();
  const pathname = usePathname();
  const getChatInfoFromPath = useChatPathInfo(pathname);
  const prevContextSessionIdRef = useRef<string | null | undefined>(contextSessionId);

  // 新しいチャットページに遷移したときのクリア処理
  const clearPreviousSession = useCallback((typeFromUrl: string) => {
    if (contextSessionId) {
      dispatch({ type: 'CLEAR_CHAT', payload: { chatType: contextChatType } });
    }
  }, [contextSessionId, contextChatType, dispatch]);

  // 新しいセッション作成時のURL更新
  const updateUrlForNewSession = useCallback((sessionId: string, chatType: string) => {
          const newChatPath = `/student/chat/${chatType.toLowerCase()}/${sessionId}`;
    router.replace(newChatPath);
  }, [router]);

  // チャットタイプの同期
  const syncChatType = useCallback((typeFromUrl: ChatTypeValue) => {
    if (typeFromUrl !== contextChatType) {
      changeChatType(typeFromUrl);
    }
  }, [contextChatType, changeChatType]);

  // セッションIDの同期
  const syncSessionId = useCallback((sessionIdFromUrl: string) => {
    if (sessionIdFromUrl !== contextSessionId) {
      const foundSession = sessions.find(s => s.id === sessionIdFromUrl) || 
                           archivedSessions.find(s => s.id === sessionIdFromUrl);
      const sessionStatus = foundSession?.status;
      dispatch({ type: 'SET_SESSION_ID', payload: { id: sessionIdFromUrl, status: sessionStatus } });
    }
  }, [contextSessionId, sessions, archivedSessions, dispatch]);

  // コンテキストセッションのクリア
  const clearContextSession = useCallback(() => {
    dispatch({ type: 'SET_SESSION_ID', payload: { id: null, status: null } });
  }, [dispatch]);

  return {
    contextChatType,
    contextSessionId,
    justStartedNewChat,
    prevContextSessionIdRef,
    getChatInfoFromPath,
    clearPreviousSession,
    updateUrlForNewSession,
    syncChatType,
    syncSessionId,
    clearContextSession,
  };
};

// チャットタイプの表示名を取得
const getChatTypeDisplayName = (chatType: ChatTypeValue): string => {
  switch (chatType) {
    case ChatTypeEnum.SELF_ANALYSIS:
      return '自己分析AI';
    case ChatTypeEnum.ADMISSION:
      return '総合型選抜AI';
    case ChatTypeEnum.STUDY_SUPPORT:
      return '学習サポートAI';
    case ChatTypeEnum.FAQ:
      return 'FAQヘルプAI';
    default:
      return 'AIチャット';
  }
};

// チャットタイプの説明を取得
const getChatTypeDescription = (chatType: ChatTypeValue): string => {
  switch (chatType) {
    case ChatTypeEnum.SELF_ANALYSIS:
      return '自己分析を深め、自分の強みを見つけましょう';
    case ChatTypeEnum.ADMISSION:
      return '総合型選抜に関する相談や志望理由書の添削を行います';
    case ChatTypeEnum.STUDY_SUPPORT:
      return '学習に関する質問や課題の解決をサポートします';
    case ChatTypeEnum.FAQ:
      return 'よくある質問に回答します';
    default:
      return 'AIとチャットして情報を得ましょう';
  }
};

// チャットタイプの短縮名を取得
const getChatTypeShortName = (chatType: ChatTypeValue): string => {
  switch (chatType) {
    case ChatTypeEnum.STUDY_SUPPORT:
      return '学習支援';
    case ChatTypeEnum.SELF_ANALYSIS:
      return '自己分析';
    case ChatTypeEnum.ADMISSION:
      return '総合型選抜';
    case ChatTypeEnum.FAQ:
      return 'FAQ';
    default:
      return chatType;
  }
};

const ChatPage: React.FC<ChatPageProps> = ({ initialChatType, initialSessionId }) => {
  const { data: session } = useSession();

  // ユーザーのプラン判定
  const userRole = session?.user?.role;
  const isFreeUser = userRole === 'フリー';
  const hasAccessToChat = !isFreeUser || session?.user?.isAdmin;

  const {
    isLoading: chatIsLoading,
    isWebSocketConnected: isConnected,
    sendMessage: sendChatMessage,
  } = useChat();

  const {
    contextChatType,
    contextSessionId,
    justStartedNewChat,
    prevContextSessionIdRef,
    getChatInfoFromPath,
    clearPreviousSession,
    updateUrlForNewSession,
    syncChatType,
    syncSessionId,
    clearContextSession,
  } = useSessionSync();

  const checklistRef = useRef<{ triggerUpdate: () => void }>(null);

  // メインの同期効果
  useEffect(() => {
    const { typeFromUrl, sessionIdFromUrl } = getChatInfoFromPath();
    const previousContextSessionId = prevContextSessionIdRef.current;

    // ケース1: 新しいチャットページに遷移 - 以前のセッションをクリア
    if (typeFromUrl && !sessionIdFromUrl && contextSessionId) {
      clearPreviousSession(typeFromUrl);
      return;
    }

    // ケース2: 新しいセッション作成時のURL更新
    if (contextChatType && contextSessionId && !sessionIdFromUrl && 
        (previousContextSessionId === null || previousContextSessionId === undefined)) {
      updateUrlForNewSession(contextSessionId, contextChatType);
      return;
    }

    // ケース3: チャットタイプの同期
    if (typeFromUrl && typeFromUrl !== contextChatType) {
      syncChatType(typeFromUrl);
      return;
    }

    // ケース4: セッションIDの同期（同じチャットタイプの場合）
    if (typeFromUrl && typeFromUrl === contextChatType) {
      if (sessionIdFromUrl && sessionIdFromUrl !== contextSessionId) {
        syncSessionId(sessionIdFromUrl);
        return;
      } else if (!sessionIdFromUrl && contextSessionId && !justStartedNewChat) {
        if (previousContextSessionId !== null && previousContextSessionId !== undefined) {
          clearContextSession();
          return;
        }
      } else if (sessionIdFromUrl && !contextSessionId && !justStartedNewChat) {
        syncSessionId(sessionIdFromUrl);
        return;
      }
    }

    // ケース5: 初期チャットタイプの設定
    if (!typeFromUrl && initialChatType && initialChatType !== contextChatType && !contextChatType) {
      syncChatType(initialChatType);
      return;
    }

    // 前回のセッションIDを更新
    prevContextSessionIdRef.current = contextSessionId;
  }, [
    contextChatType,
    contextSessionId,
    justStartedNewChat,
    initialChatType,
    getChatInfoFromPath,
    clearPreviousSession,
    updateUrlForNewSession,
    syncChatType,
    syncSessionId,
    clearContextSession,
  ]);

  const activeChatType = contextChatType;

  return (
    <div className="flex h-full w-full overflow-hidden bg-slate-50 rounded-lg shadow-sm border border-slate-200">
      <ChatSidebar />
      <div className="flex-1 flex flex-col h-full border-l border-slate-200">
        {/* ヘッダー部分 */}
        <div className="bg-white py-4 px-6 border-b border-slate-200 hidden sm:block shadow-sm sticky top-0 z-10">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-lg font-semibold text-slate-800">
              {activeChatType ? getChatTypeDisplayName(activeChatType) : 'AIチャット'}
            </h1>
            <p className="text-sm text-slate-500">
              {activeChatType ? getChatTypeDescription(activeChatType) : 'AIとチャットして情報を得ましょう'}
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
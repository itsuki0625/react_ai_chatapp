'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
// import { apiClient } from '@/lib/api-client'; // ChatProvider側でAPIコール
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { PlusCircle, ChevronLeft, ChevronRight, Archive, ArchiveRestore, Inbox } from 'lucide-react';
// import { cn } from "@/lib/utils"; // 未使用
import { useChat } from '@/store/chat/ChatContext'; // useChat をインポート
import { ChatTypeEnum, type ChatTypeValue, type ChatSession } from '@/types/chat'; // ChatSession を追加インポート

const ChatSidebar: React.FC = () => {
  const router = useRouter();
  const { data: authSession, status: authStatus } = useSession();
  const {
    currentChatType,
    sessionId: currentSessionIdFromContext,
    sessions, // Contextからセッションリストを取得
    isLoadingSessions, // Contextからセッション読み込み状態を取得
    errorSessions, // Contextからセッションエラー状態を取得
    archivedSessions, // ChatContextType から直接取得
    isLoadingArchivedSessions, // ChatContextType から直接取得
    errorArchivedSessions, // ChatContextType から直接取得
    startNewChat,
    archiveSession,
    fetchSessions,
    fetchArchivedSessions,
    unarchiveSession,
    dispatch, // dispatch を useChat から取得
  } = useChat();

  // const [activeSessions, setActiveSessions] = useState<ChatSessionSummary[]>([]); // Contextで管理
  // const [isLoading, setIsLoading] = useState(false); // Contextで管理 (isLoadingSessions)
  // const [error, setError] = useState<string | null>(null); // Contextで管理 (errorSessions)
  const [isOpen, setIsOpen] = useState(true);
  const [showArchived, setShowArchived] = useState(false); // アーカイブ表示状態

  // 画面サイズに応じてサイドバーの初期状態を設定
  useEffect(() => {
    const checkScreenSize = () => {
      setIsOpen(window.innerWidth >= 768);
    };
    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  // 初回レンダリング時または currentChatType 変更時にセッションを読み込む
  useEffect(() => {
    console.log(`[ChatSidebar EFFECT on type/auth/showArchived change] authStatus: ${authStatus}, currentChatType: ${currentChatType}, showArchived: ${showArchived}`);
    if (authStatus === 'authenticated' && currentChatType) {
      if (showArchived) {
        console.log(`[ChatSidebar EFFECT] Fetching ARCHIVED sessions for ${currentChatType}`);
        fetchArchivedSessions(currentChatType);
      } else {
        console.log(`[ChatSidebar EFFECT] Fetching ACTIVE sessions for ${currentChatType}`);
        fetchSessions(currentChatType);
      }
    }
  }, [authStatus, currentChatType, fetchSessions, fetchArchivedSessions, showArchived]);

  const getChatTypeName = (type: ChatTypeValue | null | undefined): string => {
    if (!type) return "チャット";
    switch (type) {
      case ChatTypeEnum.SELF_ANALYSIS: return "自己分析";
      case ChatTypeEnum.ADMISSION: return "総合型選抜";
      case ChatTypeEnum.STUDY_SUPPORT: return "学習支援";
      case ChatTypeEnum.GENERAL: return "ジェネラル";
      case ChatTypeEnum.FAQ: return "FAQ";
      default: return "チャット";
    }
  };

  const handleToggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  const handleSelectSession = (sessionId: string, chatType: ChatTypeValue) => {
    const currentShowArchivedState = showArchived; // この関数スコープでのshowArchivedの状態を保持
    console.log(`[ChatSidebar handleSelectSession] Called with sessionId: ${sessionId}, chatType: ${chatType}. Current showArchived state is: ${currentShowArchivedState}`);

    // const selectedSession = sessions.find(s => s.id === sessionId) || archivedSessions.find(s => s.id === sessionId);
    const selectedSession = currentShowArchivedState
      ? archivedSessions.find(s => s.id === sessionId)
      : sessions.find(s => s.id === sessionId);

    if (!selectedSession) {
      console.warn(`[ChatSidebar handleSelectSession] Session with ID ${sessionId} not found in ${currentShowArchivedState ? 'archived' : 'active'} lists.`);
      return;
    }
    // セッションの実際のステータスを決定（APIレスポンスにstatusがない場合を考慮）
    const sessionStatusOnClick = currentShowArchivedState ? 'ARCHIVED' : (selectedSession.status || 'ACTIVE');

    console.log(`[ChatSidebar handleSelectSession] Selected session status from data: ${selectedSession.status}, Determined status for dispatch: ${sessionStatusOnClick}, Is current list displaying archived items? ${currentShowArchivedState}`);

    if (currentSessionIdFromContext === sessionId && currentChatType === chatType) {
      console.log(`[ChatSidebar handleSelectSession] Session ${sessionId} is already selected and chat type matches. No action needed.`);
      return;
    }
    
    console.log(`[ChatSidebar handleSelectSession] Proceeding to dispatch actions for session ${sessionId}`);
    if (currentChatType !== chatType) {
      dispatch({ type: 'SET_CURRENT_CHAT_TYPE', payload: chatType }); 
      // dispatch({ type: 'SET_SESSION_ID', payload: { id: sessionId, status: selectedSession.status || 'ACTIVE' } }); // 修正前
      dispatch({ type: 'SET_SESSION_ID', payload: { id: sessionId, status: sessionStatusOnClick } }); // 修正後
    } else {
      // dispatch({ type: 'SET_SESSION_ID', payload: { id: sessionId, status: selectedSession.status || 'ACTIVE' } }); // 修正前
      dispatch({ type: 'SET_SESSION_ID', payload: { id: sessionId, status: sessionStatusOnClick } }); // 修正後
    }
    router.push(`/chat/${chatType.toLowerCase()}/${sessionId}`);
  };

  const handleStartNewChat = async () => {
    if (showArchived) {
      setShowArchived(false); 
      return;
    }
    if (currentChatType) {
      const newSessionId = await startNewChat(currentChatType); // startNewChat は Promise<string | null> を返す
      if (typeof newSessionId === 'string') { // 文字列なら成功
        console.log("New session started, new ID:", newSessionId);
        // 新しいセッションIDを含むURLに遷移
        router.push(`/chat/${currentChatType.toLowerCase()}/${newSessionId}`);
      }
    }
  };

  const handleArchiveSession = async (sessionId: string) => {
    try {
      await archiveSession(sessionId);
      if (currentChatType && !showArchived) {
        fetchSessions(currentChatType);
      }
    } catch (error) {
      console.error("Failed to archive session in sidebar:", error);
      // ここでユーザーにエラーを通知する (例: toast)
    }
  };

  const handleUnarchiveSession = async (sessionId: string) => {
    try {
      await unarchiveSession(sessionId);
      if (currentChatType && showArchived) {
        fetchArchivedSessions(currentChatType);
      }
      // オプション: アクティブなセッションリストも更新する
      // if (currentChatType) { fetchSessions(currentChatType); }
    } catch (error) {
      console.error("Failed to unarchive session in sidebar:", error);
      // ここでユーザーにエラーを通知する (例: toast)
    }
  };

  const handleToggleArchivedView = () => {
    setShowArchived(!showArchived);
  };

  const sessionsToDisplay = showArchived ? archivedSessions : sessions;
  const isLoadingDisplay = showArchived ? isLoadingArchivedSessions : isLoadingSessions;
  const errorDisplay = showArchived ? errorArchivedSessions : errorSessions;

  if (authStatus === 'loading') {
    return <div className="p-4">セッション情報を読み込み中...</div>;
  }

  return (
    <div className={`transition-all duration-300 ease-in-out ${isOpen ? "w-72" : "w-16"} bg-gray-800 text-white flex flex-col`}>
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        {isOpen && <h2 className="text-lg font-semibold">{`${getChatTypeName(currentChatType)} AI：チャット履歴`}</h2>}
        <button onClick={handleToggleSidebar} className="p-1 hover:bg-gray-700 rounded">
          {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      {isOpen && (
        <div className="p-4">
          <button
            onClick={handleStartNewChat}
            disabled={showArchived} // アーカイブ表示中は新規チャットボタンを無効化
            className="w-full flex items-center justify-center px-4 py-2 mb-3 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-500"
          >
            <PlusCircle size={18} className="mr-2" />
            新しいチャット
          </button>
          <button
            onClick={handleToggleArchivedView}
            className="w-full flex items-center justify-center px-4 py-2 mb-3 text-sm font-medium text-white bg-gray-600 rounded-md hover:bg-gray-700"
          >
            {showArchived ? <Inbox size={18} className="mr-2" /> : <Archive size={18} className="mr-2" />}
            {showArchived ? "アクティブなチャットを表示" : "アーカイブ済みを表示"}
          </button>
        </div>
      )}

      {isOpen && (
        <div className="flex-grow overflow-y-auto p-4 space-y-2">
          {isLoadingDisplay && <p>読み込み中...</p>}
          {errorDisplay && <p className="text-red-400">エラー: {typeof errorDisplay === 'string' ? errorDisplay : errorDisplay.message}</p>}
          {!isLoadingDisplay && !errorDisplay && sessionsToDisplay.length === 0 && (
            <p className="text-gray-400">{showArchived ? "アーカイブ済みのチャットはありません。" : "チャット履歴はありません。"}</p>
          )}
          {sessionsToDisplay.map((session: ChatSession) => (
            <div
              key={session.id}
              onClick={() => handleSelectSession(session.id, session.chat_type)} 
              className={`p-3 rounded-lg cursor-pointer hover:bg-gray-700 ${currentSessionIdFromContext === session.id ? "bg-gray-700 font-semibold" : ""}`}
            >
              <div className="flex justify-between items-center">
                <span className="truncate text-sm">{session.title || "無題のチャット"}</span>
                <div className="flex space-x-1">
                  {showArchived ? (
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleUnarchiveSession(session.id); }}
                      className="p-1 hover:bg-gray-600 rounded"
                      title="アーカイブ解除"
                    >
                      <ArchiveRestore size={16} />
                    </button>
                  ) : (
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleArchiveSession(session.id); }}
                      className="p-1 hover:bg-gray-600 rounded"
                      title="アーカイブ"
                    >
                      <Archive size={16} />
                    </button>
                  )}
                </div>
              </div>
              <p className="text-xs text-gray-400 truncate">{session.last_message_summary || "メッセージなし"}</p>
              <p className="text-xs text-gray-500">
                {session.updated_at ? new Date(session.updated_at).toLocaleString() : (session.created_at ? new Date(session.created_at).toLocaleString() : '日時不明')}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatSidebar;

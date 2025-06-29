'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
// import { apiClient } from '@/lib/api-client'; // ChatProvider側でAPIコール
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { PlusCircle, ChevronLeft, ChevronRight, Archive, ArchiveRestore, Inbox, Wand2 } from 'lucide-react';
// import { cn } from "@/lib/utils"; // 未使用
import { useChat } from '@/store/chat/ChatContext'; // useChat をインポート
import { ChatTypeEnum, type ChatTypeValue, type ChatSession } from '@/types/chat'; // ChatSession を追加インポート
import { chatApi } from '@/lib/api';

const ChatSidebar: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname(); // pathname を usePathname から取得
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

  // ★ マウント・アンマウント監視用の useEffect
  useEffect(() => {
    console.log('[ChatSidebar MOUNTED_OR_UPDATED] Initial setup effect for screen size ran.');
    const checkScreenSize = () => {
      setIsOpen(window.innerWidth >= 768);
    };
    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => {
      console.log('[ChatSidebar UNMOUNTING] Cleanup effect for screen size ran.');
      window.removeEventListener('resize', checkScreenSize);
    };
  }, []); // 空の依存配列でマウント・アンマウント時にのみ実行

  // 画面サイズに応じてサイドバーの初期状態を設定 (これは既存のuseEffect、上記と統合しても良いが一旦分離のまま)
  // useEffect(() => {
  //   const checkScreenSize = () => {
  //     setIsOpen(window.innerWidth >= 768);
  //   };
  //   checkScreenSize();
  //   window.addEventListener('resize', checkScreenSize);
  //   return () => window.removeEventListener('resize', checkScreenSize);
  // }, []); 
  // ↑既存の画面サイズuseEffectは、上記の新しいマウント監視useEffectとほぼ同じなので、コメントアウトまたは削除を検討。
  // 今回は新しいマウント監視useEffectにログを追加した形。

  // 初回レンダリング時または currentChatType 変更時にセッションを読み込む
  useEffect(() => {
    console.log(`[ChatSidebar EFFECT] authStatus: ${authStatus}, currentChatType: ${currentChatType}, showArchived: ${showArchived}`);
    
    if (authStatus === 'authenticated' && currentChatType) {
      if (showArchived) {
        console.log(`[ChatSidebar] Fetching ARCHIVED sessions for ${currentChatType}`);
        fetchArchivedSessions(currentChatType);
      } else {
        console.log(`[ChatSidebar] Fetching ACTIVE sessions for ${currentChatType}`);
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
    const currentShowArchivedState = showArchived; 
    console.log(`[ChatSidebar handleSelectSession] Called with sessionId: ${sessionId}, chatType: ${chatType}. Current showArchived state is: ${currentShowArchivedState}`);

    // Check if already selected to prevent unnecessary navigation
    // Also check if the current pathname already reflects this selection
    const targetPath = `/student/chat/${chatType.toLowerCase()}/${sessionId}`;
    if (currentChatType === chatType && currentSessionIdFromContext === sessionId && pathname === targetPath) {
      console.log(`[ChatSidebar handleSelectSession] Session ${sessionId} of type ${chatType} is already active and URL matches (${pathname}). No action needed.`);
      return;
    }
    
    console.log(`[ChatSidebar handleSelectSession] Navigating to session ${sessionId} of type ${chatType}. Target path: ${targetPath}`);
    router.push(targetPath); // URLを変更するだけ
    console.log(`[ChatSidebar handleSelectSession] END - Navigation triggered to ${targetPath}.`); 
  };

  const handleStartNewChat = async () => {
    if (showArchived) {
      setShowArchived(false);
      // アーカイブ表示を解除したら、アクティブなセッションを再取得
      if (currentChatType) {
        fetchSessions(currentChatType);
      }
      // 新しいチャットを開始する場合は、再度「新しいチャット」ボタンを押してもらうか、
      // currentChatType が選択されていれば、そのまま新規チャット作成に進んでも良い。
      // ここでは一旦、アーカイブ表示解除のみ行い、ユーザーの次のアクションを待つ。
      return;
    }

    if (currentChatType) {
      try {
        console.log(`[ChatSidebar][handleStartNewChat] Calling startNewChat for type: ${currentChatType}`);
        // 変更された startNewChat を呼び出し、新しいセッションIDを取得
        const newSessionId = await startNewChat(currentChatType);

        if (newSessionId) {
          const newPath = `/student/chat/${currentChatType.toLowerCase()}/${newSessionId}`;
          console.log(`[ChatSidebar][handleStartNewChat] Navigating to ${newPath}`);
          router.push(newPath);
        } else {
          // startNewChat が null を返した場合 (エラーは ChatContext 内で throw され、ここでキャッチされる想定)
          // startNewChat 内でエラーがスローされなかったが、IDが取得できなかった場合 (フォールバック)
          console.error('[ChatSidebar][handleStartNewChat] Failed to get new session ID, startNewChat returned null or undefined.');
          // ここでユーザーにエラーを通知 (例: toast)
          // alert('新しいチャットを開始できませんでした。時間をおいて再度お試しください。');
        }
      } catch (error) {
        console.error('[ChatSidebar][handleStartNewChat] Error starting new chat:', error);
        // ここでユーザーにエラーを通知 (例: toast)
        // alert(`新しいチャットの開始に失敗しました: ${(error as Error).message}`);
      }
    } else {
      console.warn('[ChatSidebar][handleStartNewChat] currentChatType is null. Cannot start new chat.');
      // 必要であればユーザーにチャットタイプ選択を促すメッセージを表示
      // alert('チャットの種類を選択してください。');
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

  const handleGenerateTitle = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // セッション選択を防ぐ
    try {
      const result = await chatApi.generateSessionTitle(sessionId);
      console.log(`Session title generated: ${result.title} for session ${sessionId}`);
      
      // セッションリストを更新してタイトル変更を反映
      if (currentChatType) {
        if (showArchived) {
          fetchArchivedSessions(currentChatType);
        } else {
          fetchSessions(currentChatType);
        }
      }
    } catch (error) {
      console.error(`Failed to generate title for session ${sessionId}:`, error);
      // エラー通知 (必要に応じてtoastなど実装)
    }
  };

  // セッション一覧を更新時間でソート（最新順）
  const sessionsToDisplay = (showArchived ? archivedSessions : sessions)
    .slice() // 元の配列を変更しないようにコピーを作成
    .sort((a, b) => {
      // updated_at または created_at を比較（更新時間優先、なければ作成時間）
      const timeA = new Date(a.updated_at || a.created_at).getTime();
      const timeB = new Date(b.updated_at || b.created_at).getTime();
      return timeB - timeA; // 降順（最新が上）
    });
  
  const isLoadingDisplay = showArchived ? isLoadingArchivedSessions : isLoadingSessions;
  const errorDisplay = showArchived ? errorArchivedSessions : errorSessions;

  if (authStatus === 'loading') {
    return <div className="p-4">セッション情報を読み込み中...</div>;
  }

  return (
    <div className={`transition-all duration-300 ease-in-out ${isOpen ? "w-72" : "w-16"} bg-white border-r border-slate-200 shadow-sm flex flex-col h-full`}>
      <div className="flex items-center justify-between p-4 border-b border-slate-200 flex-shrink-0">
        {isOpen && (
          <h2 className="text-lg font-semibold text-slate-800">
            {currentChatType?.toLowerCase() === 'self_analysis' ? '自己分析AI' :
             currentChatType?.toLowerCase() === 'admission' ? '総合型選抜AI' :
             currentChatType?.toLowerCase() === 'study_support' ? '学習サポートAI' :
             currentChatType?.toLowerCase() === 'faq' ? 'ヘルプAI' : 
             `AIチャット${currentChatType ? ` (${currentChatType})` : ''}`}
          </h2>
        )}
        <button onClick={handleToggleSidebar} className="p-1 hover:bg-slate-100 rounded text-slate-600">
          {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      {isOpen && (
        <div className="p-4 flex-shrink-0">
          <button
            onClick={handleStartNewChat}
            disabled={showArchived} // アーカイブ表示中は新規チャットボタンを無効化
            className="w-full flex items-center justify-center px-4 py-2 mb-3 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-slate-400"
          >
            <PlusCircle size={18} className="mr-2" />
            新しいチャット
          </button>
          <button
            onClick={handleToggleArchivedView}
            className="w-full flex items-center justify-center px-4 py-2 mb-3 text-sm font-medium text-slate-700 bg-slate-100 border border-slate-200 rounded-md hover:bg-slate-200"
          >
            {showArchived ? <Inbox size={18} className="mr-2" /> : <Archive size={18} className="mr-2" />}
            {showArchived ? "アクティブなチャットを表示" : "アーカイブ済みを表示"}
          </button>
        </div>
      )}

      {isOpen && (
        <div className="flex-grow overflow-y-auto p-4 space-y-2">
          {isLoadingDisplay && <p className="text-slate-500 text-sm">読み込み中...</p>}
          {errorDisplay && <p className="text-red-500 text-sm">エラー: {typeof errorDisplay === 'string' ? errorDisplay : errorDisplay.message}</p>}
          {!isLoadingDisplay && !errorDisplay && sessionsToDisplay.length === 0 && (
            <p className="text-slate-400 text-sm">{showArchived ? "アーカイブ済みのチャットはありません。" : "チャット履歴はありません。"}</p>
          )}
          {sessionsToDisplay.map((session: ChatSession) => (
            <div
              key={session.id}
              onClick={() => handleSelectSession(session.id, session.chat_type)} 
              className={`p-2 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors
                ${currentSessionIdFromContext === session.id 
                  ? "bg-blue-50 border border-blue-100 text-blue-800" 
                  : "bg-white border border-slate-100"}`}
            >
              <div className="flex justify-between items-center">
                <span className="truncate text-sm font-medium">{session.title || "無題のチャット"}</span>
                <div className="flex space-x-1">
                  {(!session.title || session.title === "無題のチャット" || session.title === "新規チャット" || session.title.includes("セッション")) && (
                    <button 
                      onClick={(e) => handleGenerateTitle(session.id, e)}
                      className="p-1 hover:bg-slate-200 rounded text-slate-600"
                      title="タイトルを自動生成"
                    >
                      <Wand2 size={14} />
                    </button>
                  )}
                  {showArchived ? (
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleUnarchiveSession(session.id); }}
                      className="p-1 hover:bg-slate-200 rounded text-slate-600"
                      title="アーカイブ解除"
                    >
                      <ArchiveRestore size={14} />
                    </button>
                  ) : (
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleArchiveSession(session.id); }}
                      className="p-1 hover:bg-slate-200 rounded text-slate-600"
                      title="アーカイブ"
                    >
                      <Archive size={14} />
                    </button>
                  )}
                </div>
              </div>
              
              <p className="text-xs text-slate-500 mt-1">
                {session.updated_at ? new Date(session.updated_at).toLocaleString('ja-JP', {month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit'}) : (session.created_at ? new Date(session.created_at).toLocaleString('ja-JP', {month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit'}) : '日時不明')}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatSidebar;

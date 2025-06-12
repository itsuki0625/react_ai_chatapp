'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useChat } from '@/store/chat/ChatContext';
import { ChatTypeEnum } from '@/types/chat';
import { useSession } from 'next-auth/react';
import { 
  Brain, 
  History, 
  ArrowRight,
  Calendar,
  UserX,
  Loader2,
  Archive,
  ArrowLeft
} from 'lucide-react';

const SelfAnalysisSessionsPage: React.FC = () => {
  const router = useRouter();
  const { data: authSession, status: authStatus } = useSession();
  const { 
    fetchSessions, 
    sessions, 
    isLoadingSessions,
    archiveSession,
    fetchArchivedSessions,
    archivedSessions,
    isLoadingArchivedSessions
  } = useChat();

  const [viewMode, setViewMode] = useState<'active' | 'archived'>('active');

  // 自己分析セッションのみ取得
  useEffect(() => {
    if (authStatus === 'authenticated') {
      console.log('[SelfAnalysisSessionsPage] Fetching self-analysis sessions');
      fetchSessions('self_analysis');
    }
  }, [authStatus, fetchSessions]);

  // アーカイブセッションを取得
  useEffect(() => {
    if (authStatus === 'authenticated' && viewMode === 'archived') {
      fetchArchivedSessions('self_analysis');
    }
  }, [authStatus, viewMode, fetchArchivedSessions]);

  const handleViewSession = (sessionId: string) => {
    router.push(`/chat/self-analysis/${sessionId}`);
  };

  const handleArchiveSession = async (sessionId: string) => {
    try {
      await archiveSession(sessionId);
      // セッション一覧を再取得
      fetchSessions('self_analysis');
    } catch (error) {
      console.error('Failed to archive session:', error);
    }
  };

  // 自己分析セッションのみフィルタリングして更新時間でソート（最新順）
  const selfAnalysisSessions = (viewMode === 'active' 
    ? sessions.filter(session => session.chat_type === 'self_analysis')
    : archivedSessions.filter(session => session.chat_type === 'self_analysis'))
    .slice() // 元の配列を変更しないようにコピーを作成
    .sort((a, b) => {
      // updated_at または created_at を比較（更新時間優先、なければ作成時間）
      const timeA = new Date(a.updated_at || a.created_at).getTime();
      const timeB = new Date(b.updated_at || b.created_at).getTime();
      return timeB - timeA; // 降順（最新が上）
    });

  // 認証ローディング状態
  if (authStatus === 'loading') {
    return (
      <div className="flex flex-col flex-1 items-center justify-center h-full p-8 bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="flex flex-col items-center justify-center">
          <div className="w-16 h-16 relative mb-4">
            <div className="absolute inset-0 rounded-full border-t-4 border-blue-500 animate-spin"></div>
            <div className="absolute inset-3 rounded-full bg-white shadow-md flex items-center justify-center">
              <Loader2 className="w-6 h-6 text-blue-500" />
            </div>
          </div>
          <h3 className="text-lg font-medium text-slate-800">認証情報を確認中</h3>
          <p className="mt-2 text-slate-500 text-center max-w-xs">ログイン情報を検証しています...</p>
        </div>
      </div>
    );
  }

  // 未認証状態
  if (authStatus === 'unauthenticated') {
    return (
      <div className="flex flex-col flex-1 items-center justify-center h-full p-8 bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="flex flex-col items-center justify-center text-center max-w-md">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mb-4">
            <UserX className="h-8 w-8 text-red-500" />
          </div>
          <h3 className="text-xl font-semibold text-slate-800 mb-3">ログインが必要です</h3>
          <p className="text-slate-600 mb-6">
            自己分析セッション履歴を確認するには、ログインが必要です。
          </p>
          <div className="flex space-x-4">
            <a href="/auth/login" className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-150 font-medium">
              ログイン
            </a>
            <a href="/auth/register" className="px-5 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors duration-150 font-medium">
              新規登録
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-blue-50 to-slate-100">
      {/* ヘッダーセクション */}
      <div className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center mb-4">
                <button
                  onClick={() => router.push('/chat/self-analysis')}
                  className="mr-4 p-2 text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <h1 className="text-3xl font-bold text-slate-900 flex items-center">
                  <Brain className="h-8 w-8 mr-3 text-blue-600" />
                  自己分析セッション履歴
                </h1>
              </div>
              <p className="text-slate-600">
                これまでの自己分析チャットを確認・管理できます
              </p>
            </div>
            
            {/* ビューモード切り替え */}
            <div className="flex rounded-lg border border-slate-300 overflow-hidden">
              <button
                onClick={() => setViewMode('active')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  viewMode === 'active'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                アクティブ
              </button>
              <button
                onClick={() => setViewMode('archived')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  viewMode === 'archived'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                アーカイブ
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          {(isLoadingSessions || isLoadingArchivedSessions) ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mr-3" />
              <span className="text-slate-600 text-lg">セッションを読み込み中...</span>
            </div>
          ) : selfAnalysisSessions.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Brain className="h-10 w-10 text-blue-600" />
              </div>
              <h3 className="text-xl font-medium text-slate-900 mb-2">
                {viewMode === 'active' ? '自己分析セッションがありません' : 'アーカイブされた自己分析セッションがありません'}
              </h3>
              <p className="text-slate-600 mb-6">
                {viewMode === 'active' 
                  ? 'まだ自己分析チャットを始めていません。新しい自己分析を始めてみましょう。'
                  : 'アーカイブされた自己分析セッションがありません。'
                }
              </p>
              {viewMode === 'active' && (
                <button
                  onClick={() => router.push('/chat/self-analysis')}
                  className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                  新しい自己分析を開始
                </button>
              )}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {selfAnalysisSessions.map((session) => (
                <div key={session.id} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-blue-100">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <Brain className="w-5 h-5 text-blue-600" />
                        <div>
                          <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            自己分析
                          </span>
                        </div>
                      </div>
                      {viewMode === 'active' && (
                        <button
                          onClick={() => handleArchiveSession(session.id)}
                          className="text-slate-400 hover:text-slate-600 transition-colors"
                          title="アーカイブ"
                        >
                          <Archive className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    
                    <h3 className="text-lg font-semibold text-slate-900 mb-2 truncate">
                      {session.title || '自己分析セッション'}
                    </h3>
                    
                    <div className="flex items-center text-sm text-slate-500 mb-4">
                      <Calendar className="w-4 h-4 mr-1" />
                      {new Date(session.created_at).toLocaleDateString('ja-JP', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                    
                    <button
                      onClick={() => handleViewSession(session.id)}
                      className="w-full flex items-center justify-center px-4 py-2 bg-blue-50 text-blue-600 font-medium rounded-lg hover:bg-blue-100 transition-colors duration-200 group"
                    >
                      セッションを開く
                      <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SelfAnalysisSessionsPage; 
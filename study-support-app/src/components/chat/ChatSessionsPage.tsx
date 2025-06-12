'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useChat } from '@/store/chat/ChatContext';
import { ChatTypeEnum, ChatTypeValue } from '@/types/chat';
import { useSession } from 'next-auth/react';
import { 
  Brain, 
  MessageSquare, 
  History, 
  Book,
  HelpCircle,
  GraduationCap,
  ArrowRight,
  Calendar,
  Filter,
  UserX,
  Loader2,
  Archive,
  Trash2
} from 'lucide-react';

const ChatSessionsPage: React.FC = () => {
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

  const [selectedChatType, setSelectedChatType] = useState<ChatTypeValue | 'ALL'>('ALL');
  const [viewMode, setViewMode] = useState<'active' | 'archived'>('active');

  // 全チャットタイプのセッションを取得
  useEffect(() => {
    if (authStatus === 'authenticated') {
      const chatTypes: ChatTypeValue[] = [
        'general',
        'self_analysis',
        'admission',
        'study_support',
        'faq'
      ];
      console.log('[ChatSessionsPage] Chat types to fetch:', chatTypes);
      chatTypes.forEach(chatType => {
        console.log(`[ChatSessionsPage] Fetching sessions for type: "${chatType}"`);
        fetchSessions(chatType);
      });
    }
  }, [authStatus, fetchSessions]);

  // アーカイブセッションを取得
  useEffect(() => {
    if (authStatus === 'authenticated' && viewMode === 'archived') {
      const chatTypes: ChatTypeValue[] = [
        'general',
        'self_analysis',
        'admission',
        'study_support',
        'faq'
      ];
      chatTypes.forEach(chatType => {
        fetchArchivedSessions(chatType);
      });
    }
  }, [authStatus, viewMode, fetchArchivedSessions]);

  const handleViewSession = (sessionId: string, chatType: ChatTypeValue) => {
    const chatTypeRoutes: Record<ChatTypeValue, string> = {
      [ChatTypeEnum.GENERAL]: `/chat/${sessionId}`,
      [ChatTypeEnum.SELF_ANALYSIS]: `/chat/self-analysis/${sessionId}`,
      [ChatTypeEnum.ADMISSION]: `/chat/admission/${sessionId}`,
      [ChatTypeEnum.STUDY_SUPPORT]: `/chat/study-support/${sessionId}`,
      [ChatTypeEnum.FAQ]: `/chat/faq/${sessionId}`,
    };
    
    router.push(chatTypeRoutes[chatType]);
  };

  const handleArchiveSession = async (sessionId: string) => {
    try {
      await archiveSession(sessionId);
      // セッション一覧を再取得
      const chatTypes: ChatTypeValue[] = [
        'general',
        'self_analysis',
        'admission',
        'study_support',
        'faq'
      ];
      chatTypes.forEach(chatType => {
        fetchSessions(chatType);
      });
    } catch (error) {
      console.error('Failed to archive session:', error);
    }
  };

  const getChatTypeIcon = (chatType: ChatTypeValue) => {
    switch (chatType) {
      case ChatTypeEnum.GENERAL:
        return <MessageSquare className="w-5 h-5 text-gray-600" />;
      case ChatTypeEnum.SELF_ANALYSIS:
        return <Brain className="w-5 h-5 text-blue-600" />;
      case ChatTypeEnum.ADMISSION:
        return <GraduationCap className="w-5 h-5 text-purple-600" />;
      case ChatTypeEnum.STUDY_SUPPORT:
        return <Book className="w-5 h-5 text-green-600" />;
      case ChatTypeEnum.FAQ:
        return <HelpCircle className="w-5 h-5 text-orange-600" />;
      default:
        return <MessageSquare className="w-5 h-5 text-gray-600" />;
    }
  };

  const getChatTypeName = (chatType: ChatTypeValue) => {
    switch (chatType) {
      case ChatTypeEnum.GENERAL:
        return '一般チャット';
      case ChatTypeEnum.SELF_ANALYSIS:
        return '自己分析';
      case ChatTypeEnum.ADMISSION:
        return '総合型選抜';
      case ChatTypeEnum.STUDY_SUPPORT:
        return '学習支援';
      case ChatTypeEnum.FAQ:
        return 'FAQ';
      default:
        return '不明';
    }
  };

  const getChatTypeColor = (chatType: ChatTypeValue) => {
    switch (chatType) {
      case ChatTypeEnum.GENERAL:
        return 'bg-gray-100 text-gray-800';
      case ChatTypeEnum.SELF_ANALYSIS:
        return 'bg-blue-100 text-blue-800';
      case ChatTypeEnum.ADMISSION:
        return 'bg-purple-100 text-purple-800';
      case ChatTypeEnum.STUDY_SUPPORT:
        return 'bg-green-100 text-green-800';
      case ChatTypeEnum.FAQ:
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // フィルタリングされたセッションを更新時間でソート（最新順）
  const filteredSessions = (viewMode === 'active' 
    ? sessions.filter(session => 
        selectedChatType === 'ALL' || session.chat_type === selectedChatType
      )
    : archivedSessions.filter(session => 
        selectedChatType === 'ALL' || session.chat_type === selectedChatType
      ))
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
            チャットセッション履歴を確認するには、ログインが必要です。
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
    <div className="flex flex-col h-full bg-gradient-to-br from-slate-50 to-slate-100">
      {/* ヘッダーセクション */}
      <div className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 flex items-center">
                <History className="h-8 w-8 mr-3 text-blue-600" />
                チャットセッション履歴
              </h1>
              <p className="mt-2 text-slate-600">
                これまでのAIとの対話を確認・管理できます
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
          
          {/* フィルター */}
          <div className="mt-6 flex items-center space-x-4">
            <Filter className="w-5 h-5 text-slate-500" />
            <select
              value={selectedChatType}
              onChange={(e) => setSelectedChatType(e.target.value as ChatTypeValue | 'ALL')}
              className="border border-slate-300 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">すべてのタイプ</option>
              <option value={ChatTypeEnum.GENERAL}>一般チャット</option>
              <option value={ChatTypeEnum.SELF_ANALYSIS}>自己分析</option>
              <option value={ChatTypeEnum.ADMISSION}>総合型選抜</option>
              <option value={ChatTypeEnum.STUDY_SUPPORT}>学習支援</option>
              <option value={ChatTypeEnum.FAQ}>FAQ</option>
            </select>
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
          ) : filteredSessions.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <History className="h-10 w-10 text-slate-400" />
              </div>
              <h3 className="text-xl font-medium text-slate-900 mb-2">
                {viewMode === 'active' ? 'セッションがありません' : 'アーカイブされたセッションがありません'}
              </h3>
              <p className="text-slate-600 mb-6">
                {viewMode === 'active' 
                  ? 'まだチャットセッションがありません。新しいチャットを始めてみましょう。'
                  : 'アーカイブされたセッションがありません。'
                }
              </p>
              {viewMode === 'active' && (
                <button
                  onClick={() => router.push('/chat')}
                  className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                  新しいチャットを開始
                </button>
              )}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredSessions.map((session) => (
                <div key={session.id} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        {getChatTypeIcon(session.chat_type)}
                        <div>
                          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getChatTypeColor(session.chat_type)}`}>
                            {getChatTypeName(session.chat_type)}
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
                      {session.title || `${getChatTypeName(session.chat_type)}セッション`}
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
                      onClick={() => handleViewSession(session.id, session.chat_type)}
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

export default ChatSessionsPage; 
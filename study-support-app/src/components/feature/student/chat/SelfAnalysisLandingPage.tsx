'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useChat } from '@/store/chat/ChatContext';
import { ChatTypeEnum } from '@/types/chat';
import { useSession } from 'next-auth/react';
import { 
  Brain, 
  MessageSquare, 
  History, 
  Plus, 
  Target, 
  Lightbulb, 
  TrendingUp,
  Users,
  CheckCircle,
  ArrowRight,
  UserX,
  Loader2
} from 'lucide-react';

const SelfAnalysisLandingPage: React.FC = () => {
  const router = useRouter();
  const { data: authSession, status: authStatus } = useSession();
  const { 
    startNewChat, 
    fetchSessions, 
    sessions, 
    isLoadingSessions,
    changeChatType 
  } = useChat();

  // 自己分析チャットタイプを設定
  useEffect(() => {
    changeChatType(ChatTypeEnum.SELF_ANALYSIS);
  }, [changeChatType]);

  // セッション履歴を取得
  useEffect(() => {
    if (authStatus === 'authenticated') {
      fetchSessions(ChatTypeEnum.SELF_ANALYSIS);
    }
  }, [authStatus, fetchSessions]);

  const handleStartNewChat = async () => {
    try {
      const newSessionId = await startNewChat(ChatTypeEnum.SELF_ANALYSIS);
      if (newSessionId) {
        router.push(`/student/chat/self-analysis/${newSessionId}`);
      }
    } catch (error) {
      console.error('Failed to start new chat:', error);
    }
  };

  const handleViewSession = (sessionId: string) => {
    router.push(`/student/chat/self-analysis/${sessionId}`);
  };

  // 認証ローディング状態
  if (authStatus === 'loading') {
    return (
      <div className="flex flex-col flex-1 items-center justify-center h-full p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
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
      <div className="flex flex-col flex-1 items-center justify-center h-full p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="flex flex-col items-center justify-center text-center max-w-md">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mb-4">
            <UserX className="h-8 w-8 text-red-500" />
          </div>
          <h3 className="text-xl font-semibold text-slate-800 mb-3">ログインが必要です</h3>
          <p className="text-slate-600 mb-6">
            自己分析機能を利用するには、ログインが必要です。アカウントをお持ちでない場合は、新規登録してください。
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
    <div className="flex flex-col h-full bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* ヘッダーセクション */}
      <div className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="text-center">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Brain className="h-10 w-10 text-blue-600" />
            </div>
            <h1 className="text-4xl font-bold text-slate-900 mb-4">自己分析AI</h1>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-8">
              AIとの対話を通じて、あなた自身を深く理解し、将来の目標や強みを発見しましょう
            </p>
            
            {/* アクションボタン */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleStartNewChat}
                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg hover:shadow-xl"
              >
                <Plus className="w-5 h-5 mr-2" />
                新しい自己分析を開始
                <ArrowRight className="w-4 h-4 ml-2" />
              </button>
              
              {sessions.length > 0 && (
                <button
                  onClick={() => {
                    // セッションを更新時間でソートして最新のものを取得
                    const sortedSessions = [...sessions].sort((a, b) => {
                      const timeA = new Date(a.updated_at || a.created_at).getTime();
                      const timeB = new Date(b.updated_at || b.created_at).getTime();
                      return timeB - timeA; // 降順（最新が上）
                    });
                    const latestSession = sortedSessions[0];
                    if (latestSession) {
                      handleViewSession(latestSession.id);
                    }
                  }}
                  className="inline-flex items-center px-6 py-3 bg-white text-blue-600 font-medium rounded-lg border-2 border-blue-600 hover:bg-blue-50 transition-colors duration-200"
                >
                  <MessageSquare className="w-5 h-5 mr-2" />
                  前回の続きから
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-12">
          {/* 特長セクション */}
          <div className="mb-16">
            <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">自己分析AIの特長</h2>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow duration-300">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-6">
                  <Target className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-4">将来の目標発見</h3>
                <p className="text-slate-600 mb-4">
                  あなたの興味や価値観を深掘りし、将来やりたいことや目指したい方向性を明確にします。
                </p>
                <ul className="space-y-2 text-sm text-slate-500">
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    キャリア目標の明確化
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    興味分野の発見
                  </li>
                </ul>
              </div>

              <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow duration-300">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
                  <TrendingUp className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-4">強み・特徴の理解</h3>
                <p className="text-slate-600 mb-4">
                  これまでの経験や学習を振り返り、あなたの強みや特徴的な能力を発見・整理します。
                </p>
                <ul className="space-y-2 text-sm text-slate-500">
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    個人的な強みの発見
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    成長ポイントの特定
                  </li>
                </ul>
              </div>

              <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow duration-300">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-6">
                  <Lightbulb className="h-8 w-8 text-purple-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-4">動機・価値観の明確化</h3>
                <p className="text-slate-600 mb-4">
                  何が自分を動かすのか、どんな価値観を大切にしているのかを深く理解できます。
                </p>
                <ul className="space-y-2 text-sm text-slate-500">
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    コアな価値観の発見
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    行動の動機の理解
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* セッション履歴セクション */}
          {sessions.length > 0 && (
            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-slate-900 flex items-center">
                  <History className="w-6 h-6 mr-3 text-blue-600" />
                  これまでの自己分析セッション
                </h2>
              </div>
              
              {isLoadingSessions ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-2" />
                  <span className="text-slate-600">セッションを読み込み中...</span>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[...sessions]
                    .sort((a, b) => {
                      // 更新時間でソート（最新順）
                      const timeA = new Date(a.updated_at || a.created_at).getTime();
                      const timeB = new Date(b.updated_at || b.created_at).getTime();
                      return timeB - timeA; // 降順（最新が上）
                    })
                    .slice(0, 6)
                    .map((session) => (
                    <button
                      key={session.id}
                      onClick={() => handleViewSession(session.id)}
                      className="text-left p-4 border border-slate-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 group"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <MessageSquare className="w-4 h-4 text-blue-600" />
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                      </div>
                      <h3 className="font-medium text-slate-900 truncate mb-1">
                        {session.title || '自己分析セッション'}
                      </h3>
                      <p className="text-sm text-slate-500">
                        {new Date(session.created_at).toLocaleDateString('ja-JP', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </p>
                    </button>
                  ))}
                </div>
              )}
              
              {sessions.length > 6 && (
                <div className="mt-6 text-center">
                  <button 
                    onClick={() => router.push('/student/chat/self-analysis/sessions')}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    すべてのセッションを見る →
                  </button>
                </div>
              )}
            </div>
          )}

          {/* 使い方セクション */}
          <div className="mt-16 bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-slate-900 text-center mb-8">使い方</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-blue-600">1</span>
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">新しいセッションを開始</h3>
                <p className="text-slate-600 text-sm">
                  「新しい自己分析を開始」ボタンを押して、AIとの対話を始めましょう。
                </p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-green-600">2</span>
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">質問に答える</h3>
                <p className="text-slate-600 text-sm">
                  AIからの質問に正直に答えながら、自分について深く考えてみましょう。
                </p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-purple-600">3</span>
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">発見を記録</h3>
                <p className="text-slate-600 text-sm">
                  対話を通じて発見した自分の特徴や目標を記録し、活用しましょう。
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SelfAnalysisLandingPage; 
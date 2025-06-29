'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useChat } from '@/store/chat/ChatContext';
import { ChatTypeValue } from '@/types/chat';
import { useSession } from 'next-auth/react';
import { 
  Brain, 
  MessageSquare, 
  History, 
  Book,
  HelpCircle,
  GraduationCap,
  ArrowRight,
  Plus,
  Loader2,
  UserX,
  CheckCircle,
  Target,
  TrendingUp,
  Lightbulb,
  Search,
  FileText,
  Users,
  Award,
  BookOpen,
  PenTool,
  Globe
} from 'lucide-react';

interface GenericLandingPageProps {
  chatType: ChatTypeValue;
}

interface ChatTypeConfig {
  name: string;
  shortName: string;
  description: string;
  icon: React.ComponentType<any>;
  color: {
    primary: string;
    secondary: string;
    bg: string;
    iconBg: string;
    cardBg: string;
  };
  features: Array<{
    icon: React.ComponentType<any>;
    title: string;
    description: string;
    points: string[];
  }>;
  steps: Array<{
    number: number;
    title: string;
    description: string;
    color: string;
  }>;
}

const GenericLandingPage: React.FC<GenericLandingPageProps> = ({ chatType }) => {
  const router = useRouter();
  const { data: authSession, status: authStatus } = useSession();
  const { 
    startNewChat, 
    fetchSessions, 
    sessions, 
    isLoadingSessions 
  } = useChat();

  // セッション履歴を取得
  useEffect(() => {
    if (authStatus === 'authenticated') {
      fetchSessions(chatType);
    }
  }, [authStatus, fetchSessions, chatType]);

  const getChatTypeConfig = (type: ChatTypeValue): ChatTypeConfig => {
    switch (type) {
      case 'faq':
        return {
          name: 'FAQヘルプAI',
          shortName: 'FAQ',
          description: 'よくある質問にAIが迅速にお答えします',
          icon: HelpCircle,
          color: {
            primary: 'text-orange-600',
            secondary: 'text-orange-500',
            bg: 'from-orange-50 to-amber-50',
            iconBg: 'bg-orange-100',
            cardBg: 'bg-orange-50',
          },
          features: [
            {
              icon: Search,
              title: '迅速な問題解決',
              description: 'よくある質問に対して、AIが瞬時に適切な回答を提供します。',
              points: ['24時間対応', '即座に回答', '正確な情報提供']
            },
            {
              icon: FileText,
              title: '豊富な知識ベース',
              description: '幅広いトピックに関する詳細な情報とガイダンスを提供します。',
              points: ['包括的な情報', '最新の知識', '詳細な説明']
            },
            {
              icon: Users,
              title: 'ユーザーフレンドリー',
              description: '分かりやすく、親しみやすい対話で疑問を解決します。',
              points: ['簡潔な説明', '分かりやすい言葉', '親切なサポート']
            }
          ],
          steps: [
            { number: 1, title: '質問を入力', description: '気になることや分からないことを自由に質問してください。', color: 'bg-orange-100 text-orange-600' },
            { number: 2, title: 'AIが回答', description: 'AIが豊富な知識ベースから最適な回答を提供します。', color: 'bg-amber-100 text-amber-600' },
            { number: 3, title: '問題解決', description: '追加質問も可能です。完全に理解できるまでサポートします。', color: 'bg-yellow-100 text-yellow-600' }
          ]
        };
      
      case 'admission':
        return {
          name: '総合型選抜AI',
          shortName: '総合型選抜',
          description: '総合型選抜対策をAIがトータルサポートします',
          icon: GraduationCap,
          color: {
            primary: 'text-purple-600',
            secondary: 'text-purple-500',
            bg: 'from-purple-50 to-indigo-50',
            iconBg: 'bg-purple-100',
            cardBg: 'bg-purple-50',
          },
          features: [
            {
              icon: Award,
              title: '志望理由書作成支援',
              description: 'あなたの体験や想いを整理し、説得力のある志望理由書作成をサポートします。',
              points: ['体験の整理', '論理的構成', '添削アドバイス']
            },
            {
              icon: Users,
              title: '面接対策',
              description: '想定質問への回答練習や、自己PRの改善点をアドバイスします。',
              points: ['質問対策', '回答練習', '改善提案']
            },
            {
              icon: Target,
              title: '戦略立案',
              description: 'あなたの強みを活かした効果的な総合型選抜戦略を一緒に考えます。',
              points: ['強み分析', '戦略策定', '計画作成']
            }
          ],
          steps: [
            { number: 1, title: '志望校・学部を相談', description: 'あなたの興味や将来の目標について話し合いましょう。', color: 'bg-purple-100 text-purple-600' },
            { number: 2, title: '対策を計画', description: 'AIと一緒に志望理由書や面接の準備計画を立てます。', color: 'bg-indigo-100 text-indigo-600' },
            { number: 3, title: '実践・改善', description: '実際に作成・練習し、AIからのフィードバックで改善していきます。', color: 'bg-violet-100 text-violet-600' }
          ]
        };
      
      case 'study_support':
        return {
          name: '学習支援AI',
          shortName: '学習支援',
          description: 'あなたの学習をAIがパーソナライズしてサポートします',
          icon: Book,
          color: {
            primary: 'text-green-600',
            secondary: 'text-green-500',
            bg: 'from-green-50 to-emerald-50',
            iconBg: 'bg-green-100',
            cardBg: 'bg-green-50',
          },
          features: [
            {
              icon: BookOpen,
              title: '個別学習計画',
              description: 'あなたの学習状況と目標に合わせて、最適な学習計画を提案します。',
              points: ['個別最適化', 'スケジュール管理', '進捗追跡']
            },
            {
              icon: PenTool,
              title: '問題解決サポート',
              description: '分からない問題について、段階的に理解できるよう丁寧に説明します。',
              points: ['ステップバイステップ', '理解度確認', '類似問題提案']
            },
            {
              icon: TrendingUp,
              title: '学習効果向上',
              description: '効果的な学習方法や記憶術など、学習効率を高めるテクニックを教えます。',
              points: ['学習法指導', '記憶術', '効率化提案']
            }
          ],
          steps: [
            { number: 1, title: '学習状況を共有', description: '現在の学習状況や困っていることを教えてください。', color: 'bg-green-100 text-green-600' },
            { number: 2, title: '計画を立案', description: 'AIがあなたに最適な学習計画とアプローチを提案します。', color: 'bg-emerald-100 text-emerald-600' },
            { number: 3, title: '実践・フォロー', description: '計画に沿って学習し、定期的にAIからサポートを受けます。', color: 'bg-teal-100 text-teal-600' }
          ]
        };
      
             case 'general':
         return {
           name: '一般チャットAI',
           shortName: '一般チャット',
           description: 'AIと自由に対話して、様々なことを相談できます',
           icon: MessageSquare,
           color: {
             primary: 'text-gray-600',
             secondary: 'text-gray-500',
             bg: 'from-gray-50 to-slate-50',
             iconBg: 'bg-gray-100',
             cardBg: 'bg-gray-50',
           },
           features: [
             {
               icon: MessageSquare,
               title: '自由な対話',
               description: 'どんなトピックでも気軽にAIと対話することができます。',
               points: ['自由な会話', '多様なトピック', 'カジュアルな相談']
             },
             {
               icon: Lightbulb,
               title: 'アイデア創出',
               description: 'AIとのブレインストーミングで新しいアイデアを生み出せます。',
               points: ['創造的思考', 'ブレインストーミング', 'アイデア整理']
             },
             {
               icon: Globe,
               title: '幅広い知識',
               description: '様々な分野の知識を活用して、疑問に答えます。',
               points: ['幅広い分野', '豊富な知識', '多角的視点']
             }
           ],
           steps: [
             { number: 1, title: '気軽に話しかける', description: '何でも気になることを話しかけてみてください。', color: 'bg-gray-100 text-gray-600' },
             { number: 2, title: 'AIと対話', description: 'AIが様々な角度から回答し、対話を深めます。', color: 'bg-slate-100 text-slate-600' },
             { number: 3, title: '新しい発見', description: '対話を通じて新しい視点や発見を得ることができます。', color: 'bg-zinc-100 text-zinc-600' }
           ]
         };
       
       default:
         return {
           name: 'チャットAI',
           shortName: 'チャット',
           description: 'AIとの対話をお楽しみください',
           icon: MessageSquare,
           color: {
             primary: 'text-gray-600',
             secondary: 'text-gray-500',
             bg: 'from-gray-50 to-slate-50',
             iconBg: 'bg-gray-100',
             cardBg: 'bg-gray-50',
           },
           features: [],
           steps: []
         };
    }
  };

  const config = getChatTypeConfig(chatType);
  const IconComponent = config.icon;

  // 指定されたチャットタイプのセッションのみフィルタリングして更新時間でソート（最新順）
  const filteredSessions = sessions
    .filter(session => session.chat_type === chatType)
    .slice() // 元の配列を変更しないようにコピーを作成
    .sort((a, b) => {
      // updated_at または created_at を比較（更新時間優先、なければ作成時間）
      const timeA = new Date(a.updated_at || a.created_at).getTime();
      const timeB = new Date(b.updated_at || b.created_at).getTime();
      return timeB - timeA; // 降順（最新が上）
    });

  const handleStartNewChat = async () => {
    if (authStatus !== 'authenticated') {
      router.push('/auth/login');
      return;
    }
    
    try {
      const sessionId = await startNewChat(chatType);
      if (sessionId) {
        router.push(`/chat/${chatType}/${sessionId}`);
      }
    } catch (error) {
      console.error('新しいチャット開始エラー:', error);
    }
  };

  const handleViewSession = (sessionId: string) => {
    router.push(`/chat/${chatType}/${sessionId}`);
  };

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
            {config.name}をご利用いただくには、ログインが必要です。
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
    <div className={`flex flex-col h-full bg-gradient-to-br ${config.color.bg}`}>
      {/* ヘッダーセクション */}
      <div className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-12 text-center">
          <div className={`w-20 h-20 ${config.color.iconBg} rounded-full flex items-center justify-center mx-auto mb-6`}>
            <IconComponent className={`h-10 w-10 ${config.color.primary}`} />
          </div>
          <h1 className="text-4xl font-bold text-slate-900 mb-4">
            {config.name}
          </h1>
          <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
            {config.description}
          </p>
          
          {/* アクションボタン */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleStartNewChat}
              className={`inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg hover:shadow-xl`}
            >
              <Plus className="w-5 h-5 mr-2" />
              新しい{config.shortName}を開始
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
            
            {filteredSessions.length > 0 && (
              <button
                onClick={() => {
                  const latestSession = filteredSessions[0];
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

      {/* メインコンテンツ */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-12">
          {/* 特長セクション */}
          <div className="mb-16">
            <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">{config.name}の特長</h2>
            
            <div className="grid md:grid-cols-3 gap-8">
              {config.features.map((feature, index) => {
                const FeatureIcon = feature.icon;
                return (
                  <div key={index} className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow duration-300">
                    <div className={`w-16 h-16 ${config.color.iconBg} rounded-full flex items-center justify-center mb-6`}>
                      <FeatureIcon className={`h-8 w-8 ${config.color.primary}`} />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-900 mb-4">{feature.title}</h3>
                    <p className="text-slate-600 mb-4">
                      {feature.description}
                    </p>
                    <ul className="space-y-2 text-sm text-slate-500">
                      {feature.points.map((point, pointIndex) => (
                        <li key={pointIndex} className="flex items-center">
                          <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          </div>

          {/* セッション履歴セクション */}
          {filteredSessions.length > 0 && (
            <div className="bg-white rounded-xl shadow-lg p-8 mb-16">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-slate-900 flex items-center">
                  <History className={`w-6 h-6 mr-3 ${config.color.primary}`} />
                  これまでの{config.shortName}セッション
                </h2>
              </div>
              
              {isLoadingSessions ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className={`w-6 h-6 animate-spin ${config.color.primary} mr-2`} />
                  <span className="text-slate-600">セッションを読み込み中...</span>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredSessions.slice(0, 6).map((session) => (
                    <button
                      key={session.id}
                      onClick={() => handleViewSession(session.id)}
                      className={`text-left p-4 border border-slate-200 rounded-lg hover:border-blue-300 hover:${config.color.cardBg} transition-all duration-200 group`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className={`w-8 h-8 ${config.color.iconBg} rounded-full flex items-center justify-center`}>
                          <MessageSquare className={`w-4 h-4 ${config.color.primary}`} />
                        </div>
                        <ArrowRight className={`w-4 h-4 text-slate-400 group-hover:${config.color.secondary} transition-colors`} />
                      </div>
                      <h3 className="font-medium text-slate-900 truncate mb-1">
                        {session.title || `${config.shortName}セッション`}
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
              
              {filteredSessions.length > 6 && (
                <div className="mt-6 text-center">
                  <button 
                    onClick={() => router.push(`/chat/${chatType}/sessions`)}
                    className={`${config.color.primary} hover:${config.color.secondary} font-medium`}
                  >
                    すべてのセッションを見る →
                  </button>
                </div>
              )}
            </div>
          )}

          {/* 使い方セクション */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-slate-900 text-center mb-8">使い方</h2>
            <div className="grid md:grid-cols-3 gap-8">
              {config.steps.map((step, index) => (
                <div key={index} className="text-center">
                  <div className={`w-16 h-16 ${step.color} rounded-full flex items-center justify-center mx-auto mb-4`}>
                    <span className="text-2xl font-bold">{step.number}</span>
                  </div>
                  <h3 className="font-semibold text-slate-900 mb-2">{step.title}</h3>
                  <p className="text-slate-600 text-sm">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenericLandingPage; 
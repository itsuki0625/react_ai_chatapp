"use client";

import React, { useState, useEffect } from 'react';
import { FileText, Plus, Eye, Edit, Trash2, MessageSquare, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { statementApi } from '@/lib/api-client';

interface Feedback {
  id: string;
  user: {
    id: string;
    name: string;
    role: string;
  };
  content: string;
  created_at: string;
}

interface Statement {
  id: string;
  title: string;
  university: string;
  department: string;
  content: string;
  status: 'draft' | 'review' | 'completed';
  updated_at: string;
  word_count: number;
  feedbacks: Feedback[];
}

export const StatementList = () => {
  const [statements, setStatements] = useState<Statement[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchStatements = async () => {
      try {
        // 実際のAPIを呼び出してデータを取得
        const response = await statementApi.getStatements();
        setStatements(response.data as Statement[]);
      } catch (error) {
        console.error('志望理由書データの取得に失敗しました:', error);
        
        // API呼び出しに失敗した場合はデモデータをセット
        setStatements([
          {
            id: '1',
            title: '東京大学法学部 志望理由書',
            university: '東京大学',
            department: '法学部',
            content: '私が東京大学法学部を志望する理由は...',
            status: 'draft',
            updated_at: '2023-07-15',
            word_count: 450,
            feedbacks: []
          },
          {
            id: '2',
            title: '慶應義塾大学商学部 志望理由書',
            university: '慶應義塾大学',
            department: '商学部',
            content: '私が慶應義塾大学商学部を志望する理由は...',
            status: 'review',
            updated_at: '2023-07-20',
            word_count: 620,
            feedbacks: [
              {
                id: 'f1',
                user: {
                  id: 't1',
                  name: '山田先生',
                  role: 'teacher'
                },
                content: '導入部分が良く書けていますが、もう少し具体的な経験を加えるとより説得力が増すでしょう。',
                created_at: '2023-07-21'
              }
            ]
          },
          {
            id: '3',
            title: '早稲田大学政治経済学部 志望理由書',
            university: '早稲田大学',
            department: '政治経済学部',
            content: '私が早稲田大学政治経済学部を志望する理由は...',
            status: 'completed',
            updated_at: '2023-07-10',
            word_count: 580,
            feedbacks: [
              {
                id: 'f2',
                user: {
                  id: 't2',
                  name: '鈴木先生',
                  role: 'teacher'
                },
                content: '具体的なエピソードが効果的に使われていて、あなたの熱意が伝わる志望理由書になっています。',
                created_at: '2023-07-11'
              },
              {
                id: 'f3',
                user: {
                  id: 't1',
                  name: '山田先生',
                  role: 'teacher'
                },
                content: '文章全体の流れが良く、読み手を惹きつける内容になっています。',
                created_at: '2023-07-12'
              }
            ]
          }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchStatements();
  }, []);

  const handleDeleteStatement = async (statementId: string) => {
    if (!confirm('この志望理由書を削除してもよろしいですか？')) {
      return;
    }
    
    try {
      await statementApi.deleteStatement(statementId);
      setStatements(statements.filter(statement => statement.id !== statementId));
    } catch (error) {
      console.error('志望理由書の削除に失敗しました:', error);
    }
  };

  const handleImproveWithAI = async (statementId: string) => {
    try {
      setLoading(true);
      await statementApi.improveWithAI(statementId);
      
      // 更新された志望理由書を取得
      const response = await statementApi.getStatement(statementId);
      const updatedStatement = response.data as Statement;
      
      // statementsの配列内の該当するstatementを更新
      setStatements(statements.map(statement => 
        statement.id === statementId ? updatedStatement : statement
      ));
      
      alert('AIによる文章改善が完了しました。');
    } catch (error) {
      console.error('AIによる文章改善に失敗しました:', error);
      alert('AIによる文章改善中にエラーが発生しました。');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      case 'review':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch(status) {
      case 'draft':
        return '下書き';
      case 'review':
        return 'レビュー中';
      case 'completed':
        return '完成';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">志望理由書</h1>
        <button
          onClick={() => router.push('/statement/new')}
          className="flex items-center px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          新規作成
        </button>
      </div>
      
      <div className="mb-6">
        <p className="text-gray-600">
          志望理由書を作成・管理できます。AIによる文章改善や教師からのフィードバックを受けることができます。
        </p>
      </div>
      
      {statements.length === 0 ? (
        <div className="bg-white p-8 rounded-xl shadow text-center">
          <FileText className="h-16 w-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-medium mb-2">まだ志望理由書が作成されていません</h3>
          <p className="text-gray-600 mb-6">「新規作成」ボタンから志望理由書の作成を始めましょう</p>
          <button
            onClick={() => router.push('/statement/new')}
            className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
          >
            志望理由書を作成する
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {statements.map((statement) => (
            <div key={statement.id} className="bg-white rounded-xl shadow overflow-hidden">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-medium">{statement.title}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(statement.status)}`}>
                    {getStatusText(statement.status)}
                  </span>
                </div>
                
                <div className="text-sm text-gray-600 mb-4">
                  <p>{statement.university} {statement.department}</p>
                  <p>最終更新日: {statement.updated_at}</p>
                  <p>{statement.word_count}文字</p>
                </div>
                
                <div className="border rounded-lg p-3 bg-gray-50 mb-4 text-sm text-gray-700 max-h-24 overflow-hidden">
                  {statement.content}
                </div>
                
                {statement.feedbacks?.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium mb-2 flex items-center">
                      <MessageSquare className="h-4 w-4 mr-1 text-blue-600" />
                      フィードバック ({statement.feedbacks.length})
                    </h4>
                    <div className="bg-blue-50 p-3 rounded-lg text-sm">
                      <p className="font-medium">{statement.feedbacks[0].user.name}:</p>
                      <p className="text-gray-700">{statement.feedbacks[0].content}</p>
                      {statement.feedbacks.length > 1 && (
                        <p 
                          className="text-xs text-blue-600 mt-1 cursor-pointer"
                          onClick={() => router.push(`/statement/${statement.id}/feedback`)}
                        >
                          他 {statement.feedbacks.length - 1} 件のフィードバックを表示
                        </p>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="flex justify-between mt-4">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => router.push(`/statement/${statement.id}`)}
                      className="flex items-center text-sm px-3 py-1.5 bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
                    >
                      <Eye className="h-3.5 w-3.5 mr-1" />
                      表示
                    </button>
                    <button
                      onClick={() => router.push(`/statement/${statement.id}/edit`)}
                      className="flex items-center text-sm px-3 py-1.5 bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                    >
                      <Edit className="h-3.5 w-3.5 mr-1" />
                      編集
                    </button>
                    <button
                      onClick={() => handleDeleteStatement(statement.id)}
                      className="flex items-center text-sm px-3 py-1.5 bg-red-100 text-red-800 rounded hover:bg-red-200"
                    >
                      <Trash2 className="h-3.5 w-3.5 mr-1" />
                      削除
                    </button>
                  </div>
                  
                  <button
                    onClick={() => handleImproveWithAI(statement.id)}
                    className="flex items-center text-sm px-3 py-1.5 bg-purple-100 text-purple-800 rounded hover:bg-purple-200"
                  >
                    <Sparkles className="h-3.5 w-3.5 mr-1" />
                    AI改善
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div className="mt-8 bg-indigo-50 rounded-xl p-6 shadow-sm">
        <div className="flex items-start">
          <div className="bg-indigo-100 p-3 rounded-full">
            <Sparkles className="h-6 w-6 text-indigo-600" />
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-semibold mb-2">AIによる志望理由書作成サポート</h3>
            <p className="text-gray-700 mb-4">
              自己分析に基づいたAIアシスタントが、あなたにぴったりの志望理由書作成をサポートします。
              自分の強みや志望動機を整理して、魅力的な志望理由書を作成しましょう。
            </p>
            <button
              onClick={() => router.push('/student/chat/self-analysis')}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
            >
              自己分析AIを使ってみる
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}; 
'use client';

import { useParams } from 'next/navigation';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { PersonalStatement, convertToPersonalStatement, Feedback } from '@/types/statement';
import { getStatement, getFeedbacks } from '@/services/statementService';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Edit, 
  Calendar, 
  MessageSquare, 
  FileText, 
  User,
  Clock,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';

interface Props {
  params: {
    id: string;
  };
}

export default function StatementDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = typeof params.id === 'string' ? params.id : undefined;
  
  const [statement, setStatement] = useState<PersonalStatement | null>(null);
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 志望理由書とフィードバックを並行取得
        const [statementData, feedbackData] = await Promise.all([
          getStatement(id),
          getFeedbacks(id)
        ]);
        
        setStatement(convertToPersonalStatement(statementData));
        setFeedbacks(feedbackData);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
        toast.error('データの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (!id) {
    return <div className="p-4 text-red-500">無効なIDです。</div>;
  }

  if (loading) {
    return (
      <div className="container mx-auto p-4 md:p-6 lg:p-8 max-w-4xl">
        <Card className="text-center py-10">
          <CardContent>
            <Loader2 className="mx-auto h-12 w-12 text-gray-400 animate-spin" />
            <p className="mt-4 text-gray-600">読み込み中...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !statement) {
    return (
      <div className="container mx-auto p-4 md:p-6 lg:p-8 max-w-4xl">
        <Card className="text-center py-10">
          <CardContent>
            <FileText className="mx-auto h-12 w-12 text-red-400" />
            <h2 className="mt-4 text-xl font-semibold text-red-600">エラーが発生しました</h2>
            <p className="mt-2 text-gray-600">{error || '志望理由書が見つかりません'}</p>
            <Button 
              className="mt-4" 
              onClick={() => router.push('/student/statement')}
            >
              一覧に戻る
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'review': return 'bg-blue-100 text-blue-800';
      case 'reviewed': return 'bg-green-100 text-green-800';
      case 'final': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'draft': return '下書き';
      case 'review': return 'レビュー中';
      case 'reviewed': return 'レビュー済み';
      case 'final': return '完成版';
      default: return status;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8 max-w-4xl">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.push('/student/statement')}
          className="mb-4"
        >
          ← 一覧に戻る
        </Button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">{statement.title}</h1>
            <p className="text-gray-600">
              {statement.universityName} - {statement.departmentName}
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <Badge className={getStatusColor(statement.status)}>
              {getStatusText(statement.status)}
            </Badge>
            <Button
              onClick={() => router.push(`/student/statement/${id}/edit`)}
            >
              <Edit className="w-4 h-4 mr-2" />
              編集
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-6">
        {/* 基本情報 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="w-5 h-5 mr-2" />
              基本情報
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <span className="text-sm font-medium text-gray-500">文字数</span>
                <p className="text-lg font-semibold">{statement.wordCount}文字</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">最終更新</span>
                <p className="text-lg font-semibold">{formatDate(statement.updatedAt)}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">提出期限</span>
                <p className="text-lg font-semibold">
                  {statement.submissionDeadline ? formatDate(statement.submissionDeadline) : '未設定'}
                </p>
              </div>
            </div>
            
            {statement.keywords.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-500 block mb-2">キーワード</span>
                <div className="flex flex-wrap gap-2">
                  {statement.keywords.map((keyword: string, index: number) => (
                    <span 
                      key={index}
                      className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 志望理由書本文 */}
        <Card>
          <CardHeader>
            <CardTitle>志望理由書</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                {statement.content}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* フィードバック */}
        {feedbacks.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <MessageSquare className="w-5 h-5 mr-2" />
                フィードバック ({feedbacks.length}件)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {feedbacks.map((feedback: Feedback, index: number) => (
                <div key={feedback.id} className="border-l-4 border-blue-500 pl-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <User className="w-4 h-4 text-gray-500" />
                      <span className="font-medium">{feedback.authorName}</span>
                      <Badge variant={feedback.type === 'teacher' ? 'default' : 'secondary'}>
                        {feedback.type === 'teacher' ? '教師' : 'AI'}
                      </Badge>
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <Clock className="w-4 h-4 mr-1" />
                      {formatDate(feedback.createdAt)}
                    </div>
                  </div>
                  <p className="text-gray-700 whitespace-pre-wrap">{feedback.content}</p>
                  {index < feedbacks.length - 1 && <hr className="mt-4 border-t border-gray-200" />}
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
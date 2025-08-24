'use client';

import { useEffect, useState } from 'react';
import { 
  ArrowLeft,
  FileText,
  Download,
  Eye,
  Calendar,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  User,
  School
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { useRouter } from 'next/navigation';
import { MockTenantAPI } from '@/lib/mock/tenant-api';
import { StudentStatement } from '@/types/tenant';

interface StatementViewerProps {
  studentId: string;
  statementId: string;
}

interface StatementData {
  statement: StudentStatement & {
    content: string;
    feedback?: Array<{
      id: string;
      type: 'improvement' | 'positive' | 'question';
      message: string;
      timestamp: string;
    }>;
  };
  studentName: string;
}

export default function StatementViewer({ studentId, statementId }: StatementViewerProps) {
  const router = useRouter();
  const [statementData, setStatementData] = useState<StatementData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatementData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // 学生詳細と志望理由書詳細を取得
        const [studentDetails, statementDetails] = await Promise.all([
          MockTenantAPI.getStudentDetails(studentId),
          MockTenantAPI.getStatementDetails(statementId)
        ]);

        setStatementData({
          statement: statementDetails,
          studentName: studentDetails.student.fullName
        });
      } catch (err) {
        console.error('Failed to fetch statement data:', err);
        setError('志望理由書データの取得に失敗しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatementData();
  }, [studentId, statementId]);

  const handleExport = () => {
    if (!statementData) return;
    
    // 志望理由書をテキスト形式でエクスポート
    const statementText = `
志望理由書

学生: ${statementData.studentName}
大学: ${statementData.statement.universityName}
学部: ${statementData.statement.departmentName}
作成日: ${new Date(statementData.statement.createdAt).toLocaleDateString('ja-JP')}
更新日: ${new Date(statementData.statement.updatedAt).toLocaleDateString('ja-JP')}
文字数: ${statementData.statement.wordCount}/${statementData.statement.targetWordCount}文字
進捗: ${statementData.statement.progress}%

内容:
${statementData.statement.content}
    `.trim();

    const blob = new Blob([statementText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `statement_${statementData.studentName}_${statementData.statement.id}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return <StatementViewerSkeleton />;
  }

  if (error || !statementData) {
    return (
      <StatementViewerError 
        error={error || 'データが見つかりません'} 
        onRetry={() => window.location.reload()}
        onBack={() => router.back()}
      />
    );
  }

  const { statement, studentName } = statementData;

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            戻る
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">志望理由書</h1>
            <p className="text-gray-600">
              {studentName}さん - {statement.title}
            </p>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            エクスポート
          </Button>
        </div>
      </div>

      {/* 基本情報 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <FileText className="h-5 w-5 mr-2" />
                {statement.title}
              </CardTitle>
              <CardDescription>
                {statement.universityName} {statement.departmentName}
              </CardDescription>
            </div>
            <Badge variant={getStatusVariant(statement.status)}>
              {getStatusDisplayName(statement.status)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-600">作成日</p>
              <p className="font-medium">
                {new Date(statement.createdAt).toLocaleDateString('ja-JP')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">最終更新</p>
              <p className="font-medium">
                {new Date(statement.updatedAt).toLocaleDateString('ja-JP')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">提出期限</p>
              <p className="font-medium">
                {statement.submissionDeadline 
                  ? new Date(statement.submissionDeadline).toLocaleDateString('ja-JP')
                  : '未設定'
                }
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">ステータス</p>
              <p className="font-medium">{getStatusDisplayName(statement.status)}</p>
            </div>
          </div>

          {/* 進捗情報 */}
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">文字数進捗</span>
                <span className="text-sm text-gray-600">
                  {statement.wordCount} / {statement.targetWordCount} 文字
                </span>
              </div>
              <Progress 
                value={(statement.wordCount / statement.targetWordCount) * 100} 
                className="h-2"
              />
            </div>
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">全体進捗</span>
                <span className="text-sm text-gray-600">{statement.progress}%</span>
              </div>
              <Progress value={statement.progress} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 志望理由書内容 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Eye className="h-5 w-5 mr-2" />
            志望理由書内容
          </CardTitle>
          <CardDescription>
            現在の志望理由書の内容
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="prose max-w-none">
            <div className="bg-gray-50 p-6 rounded-lg border">
              <div className="whitespace-pre-wrap text-gray-900 leading-relaxed">
                {statement.content || '内容がまだ書かれていません。'}
              </div>
            </div>
          </div>
          
          {statement.content && (
            <div className="mt-4 text-sm text-gray-600 flex items-center space-x-4">
              <span className="flex items-center">
                <FileText className="h-4 w-4 mr-1" />
                文字数: {statement.wordCount}文字
              </span>
              <span className="flex items-center">
                <Target className="h-4 w-4 mr-1" />
                目標: {statement.targetWordCount}文字
              </span>
              <span className="flex items-center">
                <TrendingUp className="h-4 w-4 mr-1" />
                達成率: {Math.round((statement.wordCount / statement.targetWordCount) * 100)}%
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* フィードバック */}
      {statement.feedback && statement.feedback.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="h-5 w-5 mr-2" />
              AIフィードバック
            </CardTitle>
            <CardDescription>
              AI による添削と改善提案
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {statement.feedback.map((feedback) => (
                <FeedbackItem key={feedback.id} feedback={feedback} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 分析サマリー */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="h-5 w-5 mr-2" />
            分析サマリー
          </CardTitle>
          <CardDescription>
            この志望理由書の分析情報
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {statement.wordCount}
              </p>
              <p className="text-sm text-gray-600">現在の文字数</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {statement.progress}%
              </p>
              <p className="text-sm text-gray-600">完成度</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-600">
                {Math.ceil((statement.targetWordCount - statement.wordCount) / 50) || 0}
              </p>
              <p className="text-sm text-gray-600">推定残り時間（分）</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-600">
                {statement.submissionDeadline 
                  ? Math.max(0, Math.ceil((new Date(statement.submissionDeadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)))
                  : '-'
                }
              </p>
              <p className="text-sm text-gray-600">提出まで（日）</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface FeedbackItemProps {
  feedback: {
    id: string;
    type: 'improvement' | 'positive' | 'question';
    message: string;
    timestamp: string;
  };
}

function FeedbackItem({ feedback }: FeedbackItemProps) {
  const getIcon = () => {
    switch (feedback.type) {
      case 'improvement':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      case 'positive':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'question':
        return <FileText className="h-4 w-4 text-blue-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const getBgColor = () => {
    switch (feedback.type) {
      case 'improvement':
        return 'bg-orange-50 border-orange-200';
      case 'positive':
        return 'bg-green-50 border-green-200';
      case 'question':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`p-4 rounded-lg border ${getBgColor()}`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-1">
          {getIcon()}
        </div>
        <div className="flex-1">
          <p className="text-sm text-gray-900">{feedback.message}</p>
          <p className="text-xs text-gray-500 mt-2 flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            {new Date(feedback.timestamp).toLocaleString('ja-JP')}
          </p>
        </div>
      </div>
    </div>
  );
}

function getStatusDisplayName(status: string): string {
  const statusNames = {
    draft: '下書き',
    in_review: '作成中',
    completed: '完成',
    submitted: '提出済み'
  };
  return statusNames[status as keyof typeof statusNames] || status;
}

function getStatusVariant(status: string) {
  const variants = {
    draft: 'secondary' as const,
    in_review: 'default' as const,
    completed: 'default' as const,
    submitted: 'default' as const
  };
  return variants[status as keyof typeof variants] || 'secondary' as const;
}

function StatementViewerSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
      <div className="h-48 bg-gray-200 rounded animate-pulse"></div>
      <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
      <div className="h-32 bg-gray-200 rounded animate-pulse"></div>
    </div>
  );
}

function StatementViewerError({ 
  error, 
  onRetry, 
  onBack 
}: { 
  error: string; 
  onRetry: () => void;
  onBack: () => void;
}) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          エラーが発生しました
        </h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <div className="flex space-x-2 justify-center">
          <Button variant="outline" onClick={onBack}>
            戻る
          </Button>
          <Button onClick={onRetry}>
            再試行
          </Button>
        </div>
      </div>
    </div>
  );
}
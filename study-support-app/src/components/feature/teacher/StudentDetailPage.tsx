'use client';

import { useEffect, useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { 
  ArrowLeft,
  User,
  MessageSquare,
  FileText,
  School,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Eye,
  Mail,
  Phone
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  SchoolUser, 
  StudentChatSession, 
  StudentStatement, 
  StudentDesiredSchool 
} from '@/types/tenant';

interface StudentDetailData {
  student: SchoolUser;
  chatSessions: StudentChatSession[];
  statements: StudentStatement[];
  desiredSchools: StudentDesiredSchool[];
  stats: {
    totalChatSessions: number;
    activeChatSessions: number;
    completedChatSessions: number;
    totalStatements: number;
    completedStatements: number;
    statementsInProgress: number;
    totalDesiredSchools: number;
    decidedSchools: number;
  };
}

interface StudentDetailPageProps {
  studentId: string;
}

export default function StudentDetailPage({ studentId }: StudentDetailPageProps) {
  const router = useRouter();
  const { getStudentDetails } = useTenant();
  const [studentData, setStudentData] = useState<StudentDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStudentData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const data = await getStudentDetails(studentId);
        setStudentData(data);
      } catch (err) {
        console.error('Failed to fetch student details:', err);
        setError('生徒データの取得に失敗しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStudentData();
  }, [studentId, getStudentDetails]);

  if (isLoading) {
    return <StudentDetailSkeleton />;
  }

  if (error || !studentData) {
    return (
      <StudentDetailError 
        error={error || 'データが見つかりません'} 
        onRetry={() => window.location.reload()}
        onBack={() => router.back()}
      />
    );
  }

  const { student, chatSessions, statements, desiredSchools, stats } = studentData;

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
            <h1 className="text-2xl font-bold text-gray-900">生徒詳細</h1>
            <p className="text-gray-600">
              {student.fullName}さんの学習状況と進捗
            </p>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Mail className="h-4 w-4 mr-2" />
            メール送信
          </Button>
          <Button variant="outline" size="sm">
            <Phone className="h-4 w-4 mr-2" />
            連絡
          </Button>
        </div>
      </div>

      {/* プロフィール */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start space-x-6">
            <Avatar className="h-20 w-20">
              <AvatarImage src={student.profileImageUrl} alt={student.fullName} />
              <AvatarFallback className="text-2xl">
                {student.fullName.charAt(0)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h2 className="text-xl font-bold text-gray-900">{student.fullName}</h2>
                <Badge variant={student.isActive ? 'default' : 'secondary'}>
                  {student.isActive ? 'アクティブ' : '非アクティブ'}
                </Badge>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">学年・クラス</p>
                  <p className="font-medium">
                    {student.grade && student.className 
                      ? `${student.grade}年${student.className}組`
                      : '未設定'
                    }
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">出席番号</p>
                  <p className="font-medium">{student.studentNumber || '未設定'}</p>
                </div>
                <div>
                  <p className="text-gray-600">メールアドレス</p>
                  <p className="font-medium">{student.email}</p>
                </div>
                <div>
                  <p className="text-gray-600">最終ログイン</p>
                  <p className="font-medium">
                    {student.lastLoginAt 
                      ? formatLastLogin(student.lastLoginAt)
                      : '未ログイン'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 統計カード */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatsCard
          title="チャットセッション"
          value={stats.totalChatSessions}
          subtitle={`アクティブ: ${stats.activeChatSessions}`}
          icon={<MessageSquare className="h-6 w-6" />}
          color="blue"
        />
        <StatsCard
          title="志望理由書"
          value={stats.totalStatements}
          subtitle={`完成: ${stats.completedStatements}`}
          icon={<FileText className="h-6 w-6" />}
          color="green"
        />
        <StatsCard
          title="志望校"
          value={stats.totalDesiredSchools}
          subtitle={`確定: ${stats.decidedSchools}`}
          icon={<School className="h-6 w-6" />}
          color="purple"
        />
        <StatsCard
          title="進捗率"
          value={Math.round((stats.completedStatements / Math.max(stats.totalStatements, 1)) * 100)}
          subtitle="志望理由書完成率"
          icon={<TrendingUp className="h-6 w-6" />}
          color="orange"
          suffix="%"
        />
      </div>

      {/* タブコンテンツ */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="chat">チャット履歴</TabsTrigger>
          <TabsTrigger value="statements">志望理由書</TabsTrigger>
          <TabsTrigger value="schools">志望校</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 最近のチャット */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2" />
                  最近のチャット
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {chatSessions.slice(0, 3).map((session) => (
                    <div key={session.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{session.title}</p>
                        <p className="text-xs text-gray-600">
                          {session.messageCount}件のメッセージ
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
                          {getStatusDisplayName(session.status)}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatDate(session.lastMessageAt)}
                        </p>
                      </div>
                    </div>
                  ))}
                  {chatSessions.length === 0 && (
                    <p className="text-gray-500 text-center py-4">
                      チャット履歴はありません
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* 志望理由書の進捗 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  志望理由書の進捗
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {statements.slice(0, 3).map((statement) => (
                    <div key={statement.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{statement.title}</p>
                        <p className="text-xs text-gray-600">
                          {statement.wordCount}/{statement.targetWordCount}文字
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant={getStatementStatusVariant(statement.status)}>
                          {getStatementStatusDisplayName(statement.status)}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">
                          進捗: {statement.progress}%
                        </p>
                      </div>
                    </div>
                  ))}
                  {statements.length === 0 && (
                    <p className="text-gray-500 text-center py-4">
                      志望理由書はありません
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="chat" className="space-y-4">
          <ChatSessionList sessions={chatSessions} studentId={studentId} />
        </TabsContent>

        <TabsContent value="statements" className="space-y-4">
          <StatementList statements={statements} studentId={studentId} />
        </TabsContent>

        <TabsContent value="schools" className="space-y-4">
          <DesiredSchoolList schools={desiredSchools} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: number;
  subtitle: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'purple' | 'orange';
  suffix?: string;
}

function StatsCard({ title, value, subtitle, icon, color, suffix = '' }: StatsCardProps) {
  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    purple: 'text-purple-600',
    orange: 'text-orange-600'
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">
              {value}{suffix}
            </p>
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          </div>
          <div className={colorClasses[color]}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ChatSessionList({ sessions, studentId }: { sessions: StudentChatSession[]; studentId: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>チャット履歴</CardTitle>
        <CardDescription>
          {sessions.length}件のチャットセッション
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sessions.map((session) => (
            <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h4 className="font-medium">{session.title}</h4>
                  <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
                    {getStatusDisplayName(session.status)}
                  </Badge>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span className="flex items-center">
                    <MessageSquare className="h-4 w-4 mr-1" />
                    {session.messageCount}件のメッセージ
                  </span>
                  <span className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    {formatDate(session.lastMessageAt)}
                  </span>
                </div>
              </div>
              <Button asChild variant="outline" size="sm">
                <Link href={`/teacher/students/${studentId}/chat/${session.id}`}>
                  <Eye className="h-4 w-4 mr-2" />
                  詳細
                </Link>
              </Button>
            </div>
          ))}
          {sessions.length === 0 && (
            <p className="text-gray-500 text-center py-8">
              チャット履歴はありません
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function StatementList({ statements, studentId }: { statements: StudentStatement[]; studentId: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>志望理由書</CardTitle>
        <CardDescription>
          {statements.length}件の志望理由書
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {statements.map((statement) => (
            <div key={statement.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h4 className="font-medium">{statement.title}</h4>
                  <Badge variant={getStatementStatusVariant(statement.status)}>
                    {getStatementStatusDisplayName(statement.status)}
                  </Badge>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>
                    文字数: {statement.wordCount}/{statement.targetWordCount}
                  </span>
                  <span>
                    進捗: {statement.progress}%
                  </span>
                  <span>
                    更新: {formatDate(statement.updatedAt)}
                  </span>
                </div>
              </div>
              <Button asChild variant="outline" size="sm">
                <Link href={`/teacher/students/${studentId}/statements/${statement.id}`}>
                  <Eye className="h-4 w-4 mr-2" />
                  詳細
                </Link>
              </Button>
            </div>
          ))}
          {statements.length === 0 && (
            <p className="text-gray-500 text-center py-8">
              志望理由書はありません
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function DesiredSchoolList({ schools }: { schools: StudentDesiredSchool[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>志望校</CardTitle>
        <CardDescription>
          {schools.length}校の志望校
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {schools.map((school) => (
            <div key={school.id} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                    第{school.preferenceOrder}志望
                  </span>
                  <h4 className="font-medium">
                    {school.universityName} {school.departmentName}
                  </h4>
                  <Badge variant={getSchoolStatusVariant(school.status)}>
                    {getSchoolStatusDisplayName(school.status)}
                  </Badge>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>{school.admissionType}</span>
                  {school.examDate && (
                    <span className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1" />
                      {school.examDate}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
          {schools.length === 0 && (
            <p className="text-gray-500 text-center py-8">
              志望校情報はありません
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ユーティリティ関数
function formatLastLogin(timestamp: string): string {
  const now = new Date();
  const time = new Date(timestamp);
  const diffInHours = Math.floor((now.getTime() - time.getTime()) / (1000 * 60 * 60));
  
  if (diffInHours < 1) return '1時間以内';
  if (diffInHours < 24) return `${diffInHours}時間前`;
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays}日前`;
  
  return time.toLocaleDateString('ja-JP');
}

function formatDate(timestamp: string): string {
  return new Date(timestamp).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

function getStatusDisplayName(status: string): string {
  const statusNames = {
    active: 'アクティブ',
    completed: '完了',
    archived: 'アーカイブ'
  };
  return statusNames[status as keyof typeof statusNames] || status;
}

function getStatementStatusDisplayName(status: string): string {
  const statusNames = {
    draft: '下書き',
    in_review: '作成中',
    completed: '完成',
    submitted: '提出済み'
  };
  return statusNames[status as keyof typeof statusNames] || status;
}

function getStatementStatusVariant(status: string) {
  const variants = {
    draft: 'secondary' as const,
    in_review: 'default' as const,
    completed: 'default' as const,
    submitted: 'default' as const
  };
  return variants[status as keyof typeof variants] || 'secondary' as const;
}

function getSchoolStatusDisplayName(status: string): string {
  const statusNames = {
    considering: '検討中',
    decided: '確定',
    applied: '出願済み',
    accepted: '合格',
    rejected: '不合格'
  };
  return statusNames[status as keyof typeof statusNames] || status;
}

function getSchoolStatusVariant(status: string) {
  const variants = {
    considering: 'secondary' as const,
    decided: 'default' as const,
    applied: 'default' as const,
    accepted: 'default' as const,
    rejected: 'destructive' as const
  };
  return variants[status as keyof typeof variants] || 'secondary' as const;
}

function StudentDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
      <div className="h-32 bg-gray-200 rounded animate-pulse"></div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-200 rounded animate-pulse"></div>
        ))}
      </div>
      <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
    </div>
  );
}

function StudentDetailError({ 
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
'use client';

import { useEffect, useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useSchoolDashboard } from '@/hooks/useTenantApi';
import { 
  Users, 
  GraduationCap, 
  UserCheck, 
  FileText, 
  MessageSquare, 
  TrendingUp,
  Activity,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';
import { School, SchoolStats, Activity as ActivityType, AnalyticsData } from '@/types/tenant';

interface DashboardData {
  school: School;
  stats: SchoolStats;
  recentActivities: ActivityType[];
  analytics: AnalyticsData;
}

export default function SchoolDashboard() {
  const { currentSchool } = useTenant();
  const { data: dashboardData, loading: isLoading, error, refetch } = useSchoolDashboard();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return <DashboardError error={error} onRetry={() => window.location.reload()} />;
  }

  if (!dashboardData) {
    return <div>データが見つかりません</div>;
  }

  const { school, stats, recentActivities, analytics } = dashboardData;

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">学校管理ダッシュボード</h1>
          <p className="text-gray-600">
            {school.name} の管理状況
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button asChild>
            <Link href="/school-admin/users">
              <Users className="h-4 w-4 mr-2" />
              ユーザー管理
            </Link>
          </Button>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="総生徒数"
          value={stats.totalStudents}
          subtitle={`アクティブ: ${stats.activeStudents}人`}
          icon={<GraduationCap className="h-6 w-6" />}
          trend={{
            value: stats.monthlyNewUsers,
            label: "今月の新規登録"
          }}
          href="/school-admin/students"
        />
        
        <StatsCard
          title="総先生数"
          value={stats.totalTeachers}
          subtitle={`アクティブ: ${stats.activeTeachers}人`}
          icon={<UserCheck className="h-6 w-6" />}
          href="/school-admin/teachers"
        />
        
        <StatsCard
          title="志望理由書"
          value={stats.completedStatements}
          subtitle={`作成中: ${stats.statementsInProgress}件`}
          icon={<FileText className="h-6 w-6" />}
          trend={{
            value: Math.round((stats.completedStatements / (stats.completedStatements + stats.statementsInProgress)) * 100),
            label: "完成率",
            suffix: "%"
          }}
        />
        
        <StatsCard
          title="チャットセッション"
          value={stats.totalChatSessions}
          subtitle={`平均完成日数: ${stats.averageStatementCompletionDays}日`}
          icon={<MessageSquare className="h-6 w-6" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 最近の活動 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <Activity className="h-5 w-5 mr-2" />
                最近の活動
              </CardTitle>
              <CardDescription>
                学校内の最新の活動状況
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link href="/school-admin/analytics">
                詳細を見る
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivities.length === 0 ? (
                <p className="text-gray-500 text-center py-4">
                  最近の活動はありません
                </p>
              ) : (
                recentActivities.slice(0, 5).map((activity) => (
                  <ActivityItem key={activity.id} activity={activity} />
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* 志望理由書の進捗 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              志望理由書の進捗状況
            </CardTitle>
            <CardDescription>
              学校全体の志望理由書作成状況
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.statementProgress.map((progress) => (
                <div key={progress.status} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <StatementStatusIcon status={progress.status} />
                    <span className="font-medium">{progress.status}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">{progress.count}件</span>
                    <Badge variant="secondary">
                      {progress.percentage.toFixed(1)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t">
              <div className="text-sm text-gray-600">
                総計: {analytics.statementProgress.reduce((sum, p) => sum + p.count, 0)}件
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 月次進捗グラフエリア */}
      <Card>
        <CardHeader>
          <CardTitle>月次進捗</CardTitle>
          <CardDescription>
            過去5ヶ月の完成志望理由書数と新規ユーザー登録数
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center">
              <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">グラフコンポーネントが実装されます</p>
              <p className="text-sm text-gray-400 mt-1">
                Chart.js や Recharts の統合予定
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: number;
  subtitle: string;
  icon: React.ReactNode;
  trend?: {
    value: number;
    label: string;
    suffix?: string;
  };
  href?: string;
}

function StatsCard({ title, value, subtitle, icon, trend, href }: StatsCardProps) {
  const CardWrapper = href ? Link : 'div';
  
  return (
    <CardWrapper href={href || ''} className={href ? 'block' : ''}>
      <Card className={`transition-all duration-200 ${href ? 'hover:shadow-md cursor-pointer' : ''}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <p className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</p>
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
              {trend && (
                <div className="flex items-center mt-2">
                  <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                  <span className="text-sm font-medium text-green-600">
                    {trend.value}{trend.suffix || ''} {trend.label}
                  </span>
                </div>
              )}
            </div>
            <div className="text-blue-600">
              {icon}
            </div>
          </div>
        </CardContent>
      </Card>
    </CardWrapper>
  );
}

function ActivityItem({ activity }: { activity: ActivityType }) {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'statement_completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'chat_started':
        return <MessageSquare className="h-4 w-4 text-blue-500" />;
      case 'user_registered':
        return <Users className="h-4 w-4 text-purple-500" />;
      case 'login':
        return <Activity className="h-4 w-4 text-gray-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInHours = Math.floor((now.getTime() - time.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return '1時間以内';
    if (diffInHours < 24) return `${diffInHours}時間前`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}日前`;
  };

  return (
    <div className="flex items-start space-x-3">
      <div className="flex-shrink-0">
        {getActivityIcon(activity.type)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">
          {activity.userName}
        </p>
        <p className="text-sm text-gray-600">
          {activity.description}
        </p>
        <div className="flex items-center mt-1">
          <Clock className="h-3 w-3 text-gray-400 mr-1" />  
          <span className="text-xs text-gray-500">
            {formatTimeAgo(activity.timestamp)}
          </span>
        </div>
      </div>
    </div>
  );
}

function StatementStatusIcon({ status }: { status: string }) {
  switch (status) {
    case '完成':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case '作成中':
      return <Clock className="h-4 w-4 text-yellow-500" />;
    case '下書き':
      return <FileText className="h-4 w-4 text-gray-500" />;
    default:
      return <AlertCircle className="h-4 w-4 text-gray-500" />;
  }
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-200 rounded animate-pulse"></div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
        <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
      </div>
    </div>
  );
}

function DashboardError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          エラーが発生しました
        </h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button onClick={onRetry}>
          再試行
        </Button>
      </div>
    </div>
  );
}
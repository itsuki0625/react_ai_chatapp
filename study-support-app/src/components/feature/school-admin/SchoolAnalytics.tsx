'use client';

import { useEffect, useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { 
  BarChart, 
  TrendingUp, 
  Users, 
  FileText,
  MessageSquare,
  Calendar,
  Award,
  Activity,
  Download,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AnalyticsData, Activity as ActivityType } from '@/types/tenant';

export default function SchoolAnalytics() {
  const { currentSchool, getSchoolAnalytics, getRecentActivities } = useTenant();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [activities, setActivities] = useState<ActivityType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('month');

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!currentSchool) return;

      try {
        setIsLoading(true);
        setError(null);

        const [analyticsData, activitiesData] = await Promise.all([
          getSchoolAnalytics(),
          getRecentActivities()
        ]);

        setAnalytics(analyticsData);
        setActivities(activitiesData);
      } catch (err) {
        console.error('Failed to fetch analytics:', err);
        setError('分析データの取得に失敗しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, [currentSchool, getSchoolAnalytics, getRecentActivities]);

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleExport = () => {
    // 実装時にデータエクスポート機能を追加
    alert('データエクスポート機能は実装予定です');
  };

  if (isLoading) {
    return <AnalyticsSkeleton />;
  }

  if (error || !analytics) {
    return (
      <AnalyticsError 
        error={error || 'データが見つかりません'} 
        onRetry={handleRefresh} 
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">統計・分析</h1>
          <p className="text-gray-600">
            {currentSchool?.name} の詳細な分析データ
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex gap-2">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="week">過去1週間</SelectItem>
              <SelectItem value="month">過去1ヶ月</SelectItem>
              <SelectItem value="quarter">過去3ヶ月</SelectItem>
              <SelectItem value="year">過去1年間</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            更新
          </Button>
          <Button onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            エクスポート
          </Button>
        </div>
      </div>

      {/* 月次進捗チャート */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="h-5 w-5 mr-2" />
            月次進捗トレンド
          </CardTitle>
          <CardDescription>
            過去5ヶ月の志望理由書完成数と新規ユーザー登録数
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 簡易表示（実装時にはChart.jsやRechartsなどのライブラリを使用） */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">完成志望理由書数</h4>
                <div className="space-y-2">
                  {analytics.monthlyProgress.map((month) => (
                    <div key={month.month} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{month.month}</span>
                      <div className="flex items-center space-x-2">
                        <div 
                          className="h-2 bg-blue-500 rounded"
                          style={{ 
                            width: `${(month.completedStatements / Math.max(...analytics.monthlyProgress.map(m => m.completedStatements))) * 100}px` 
                          }}
                        />
                        <span className="text-sm font-medium">{month.completedStatements}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">新規ユーザー登録数</h4>
                <div className="space-y-2">
                  {analytics.monthlyProgress.map((month) => (
                    <div key={month.month} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{month.month}</span>
                      <div className="flex items-center space-x-2">
                        <div 
                          className="h-2 bg-green-500 rounded"
                          style={{ 
                            width: `${(month.newUsers / Math.max(...analytics.monthlyProgress.map(m => m.newUsers))) * 100}px` 
                          }}
                        />
                        <span className="text-sm font-medium">{month.newUsers}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 志望理由書進捗分析 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              志望理由書進捗分析
            </CardTitle>
            <CardDescription>
              現在の志望理由書作成状況
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.statementProgress.map((progress) => (
                <div key={progress.status} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{progress.status}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{progress.count}件</span>
                      <Badge variant="secondary">
                        {progress.percentage.toFixed(1)}%
                      </Badge>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full bg-blue-500"
                      style={{ width: `${progress.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
              <div className="pt-4 border-t text-sm text-gray-600">
                総計: {analytics.statementProgress.reduce((sum, p) => sum + p.count, 0)}件
              </div>
            </div>
          </CardContent>
        </Card>

        {/* トップパフォーマー */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Award className="h-5 w-5 mr-2" />
              優秀な生徒
            </CardTitle>
            <CardDescription>
              志望理由書完成数による上位生徒
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.topPerformingStudents.map((student, index) => (
                <div key={student.id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`
                      w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                      ${index === 0 ? 'bg-yellow-100 text-yellow-800' : 
                        index === 1 ? 'bg-gray-100 text-gray-800' : 
                        index === 2 ? 'bg-orange-100 text-orange-800' : 
                        'bg-blue-100 text-blue-800'}
                    `}>
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium">{student.name}</p>
                      <p className="text-sm text-gray-600">
                        完成: {student.completedStatements}件
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center space-x-1">
                      <span className="text-sm font-medium">★</span>
                      <span className="text-sm font-medium">{student.averageScore}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ユーザー活動状況 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            ユーザー活動状況
          </CardTitle>
          <CardDescription>
            過去1週間のユーザー活動データ
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-blue-600">
                  {analytics.userActivity.reduce((sum, day) => sum + day.activeUsers, 0)}
                </p>
                <p className="text-sm text-gray-600">総アクティブユーザー</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600">
                  {analytics.userActivity.reduce((sum, day) => sum + day.loginCount, 0)}
                </p>
                <p className="text-sm text-gray-600">総ログイン数</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-600">
                  {analytics.userActivity.reduce((sum, day) => sum + day.chatSessions, 0)}
                </p>
                <p className="text-sm text-gray-600">総チャットセッション</p>
              </div>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">日別活動状況</h4>
              {analytics.userActivity.map((day) => (
                <div key={day.date} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">
                      {new Date(day.date).toLocaleDateString('ja-JP', { 
                        month: 'short', 
                        day: 'numeric' 
                      })}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    <span className="flex items-center space-x-1">
                      <Users className="h-4 w-4 text-blue-500" />
                      <span>{day.activeUsers}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Activity className="h-4 w-4 text-green-500" />
                      <span>{day.loginCount}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <MessageSquare className="h-4 w-4 text-purple-500" />
                      <span>{day.chatSessions}</span>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 最近の活動 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            最近の活動履歴
          </CardTitle>
          <CardDescription>
            学校内の最新活動（詳細版）
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activities.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                最近の活動はありません
              </p>
            ) : (
              activities.map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                  <div className="flex-shrink-0">
                    <ActivityIcon type={activity.type} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900">
                        {activity.userName}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(activity.timestamp).toLocaleString('ja-JP')}
                      </p>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {activity.description}
                    </p>
                    <div className="flex items-center mt-2">
                      <Badge variant="outline" className="text-xs">
                        {getRoleDisplayName(activity.userRole)}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ActivityIcon({ type }: { type: string }) {
  const iconClass = "h-5 w-5";
  
  switch (type) {
    case 'statement_completed':
      return <FileText className={`${iconClass} text-green-500`} />;
    case 'chat_started':
      return <MessageSquare className={`${iconClass} text-blue-500`} />;
    case 'user_registered':
      return <Users className={`${iconClass} text-purple-500`} />;
    case 'login':
      return <Activity className={`${iconClass} text-gray-500`} />;
    default:
      return <Activity className={`${iconClass} text-gray-500`} />;
  }
}

function getRoleDisplayName(role: string): string {
  const roleNames = {
    student: '生徒',
    teacher: '先生',
    school_admin: '管理者',
    admin: 'システム管理者'
  };
  
  return roleNames[role as keyof typeof roleNames] || role;
}

function AnalyticsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
      <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-48 bg-gray-200 rounded animate-pulse"></div>
        <div className="h-48 bg-gray-200 rounded animate-pulse"></div>
      </div>
      <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
    </div>
  );
}

function AnalyticsError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <BarChart className="h-12 w-12 text-red-500 mx-auto mb-4" />
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
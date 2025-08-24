'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Building2, 
  MapPin, 
  Globe, 
  Phone, 
  Mail,
  Users,
  BarChart3,
  Settings,
  UserCheck,
  Clock,
  Edit,
  Trash2,
  Power,
  PowerOff,
  Save,
  X
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { useSchoolDetail } from '@/hooks/useSystemAdmin';

interface SchoolDetailManagementProps {
  schoolId: string;
}

export default function SchoolDetailManagement({ schoolId }: SchoolDetailManagementProps) {
  const router = useRouter();
  const [editMode, setEditMode] = useState(false);
  const [localSettings, setLocalSettings] = useState<any>(null);
  
  const { 
    data: school, 
    loading, 
    error, 
    refetch 
  } = useSchoolDetail(schoolId);

  useEffect(() => {
    if (school?.settings) {
      setLocalSettings(school.settings);
    }
  }, [school]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <div className="h-6 w-6 bg-gray-200 rounded animate-pulse" />
          <div className="h-8 bg-gray-200 rounded w-64 animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !school) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            戻る
          </Button>
          <h1 className="text-3xl font-bold">学校詳細</h1>
        </div>
        <Card className="p-6">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error || '学校データが見つかりません'}</p>
            <Button onClick={() => refetch()}>再試行</Button>
          </div>
        </Card>
      </div>
    );
  }

  const handleSaveSettings = async () => {
    try {
      // TODO: API呼び出しで設定を保存
      console.log('設定を保存:', localSettings);
      setEditMode(false);
    } catch (err) {
      console.error('設定の保存に失敗しました:', err);
    }
  };

  const handleToggleStatus = async () => {
    try {
      // TODO: 学校ステータス切り替えAPI呼び出し
      console.log('ステータス切り替え:', school.id);
      await refetch();
    } catch (err) {
      console.error('ステータス切り替えに失敗しました:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/admin/tenant-management">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              戻る
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold flex items-center">
              <Building2 className="h-8 w-8 mr-3 text-blue-600" />
              {school.name}
            </h1>
            <p className="text-gray-600 mt-1">学校コード: {school.school_code}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={school.is_active ? "default" : "secondary"}>
            {school.is_active ? "有効" : "無効"}
          </Badge>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm">
                {school.is_active ? (
                  <PowerOff className="h-4 w-4 mr-2 text-red-600" />
                ) : (
                  <Power className="h-4 w-4 mr-2 text-green-600" />
                )}
                {school.is_active ? '無効化' : '有効化'}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>学校ステータス変更</AlertDialogTitle>
                <AlertDialogDescription>
                  {school.name}を{school.is_active ? '無効' : '有効'}にしますか？
                  {school.is_active && 'この操作により、この学校の全ユーザーがサービスにアクセスできなくなります。'}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>キャンセル</AlertDialogCancel>
                <AlertDialogAction onClick={handleToggleStatus}>
                  {school.is_active ? '無効化' : '有効化'}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {/* 基本情報カード */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">総ユーザー数</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{school.statistics?.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              今月アクティブ: {school.statistics?.active_users_this_month || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">担当関係数</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{school.statistics?.assignments?.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              アクティブ: {school.statistics?.assignments?.active || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ユーザー活動率</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {school.statistics?.user_activity_rate ? `${school.statistics.user_activity_rate.toFixed(1)}%` : '0%'}
            </div>
            <p className="text-xs text-muted-foreground">
              過去30日間
            </p>
          </CardContent>
        </Card>
      </div>

      {/* タブコンテンツ */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="users">ユーザー</TabsTrigger>
          <TabsTrigger value="settings">設定</TabsTrigger>
          <TabsTrigger value="activities">アクティビティ</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* 基本情報 */}
          <Card>
            <CardHeader>
              <CardTitle>基本情報</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {school.details && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <MapPin className="h-4 w-4 text-gray-500" />
                      <span className="font-medium">住所</span>
                    </div>
                    <p className="text-sm text-gray-600 ml-6">
                      {school.details.address}
                    </p>
                    
                    <div className="flex items-center space-x-2">
                      <Building2 className="h-4 w-4 text-gray-500" />
                      <span className="font-medium">所在地</span>
                    </div>
                    <p className="text-sm text-gray-600 ml-6">
                      {school.details.prefecture} {school.details.city}
                    </p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Users className="h-4 w-4 text-gray-500" />
                      <span className="font-medium">校長</span>
                    </div>
                    <p className="text-sm text-gray-600 ml-6">
                      {school.details.principal_name}
                    </p>

                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <span className="font-medium">登録日</span>
                    </div>
                    <p className="text-sm text-gray-600 ml-6">
                      {new Date(school.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ユーザー構成 */}
          <Card>
            <CardHeader>
              <CardTitle>ユーザー構成</CardTitle>
            </CardHeader>
            <CardContent>
              {school.statistics?.users && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {Object.entries(school.statistics.users).map(([role, count]) => (
                    <div key={role} className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{count}</div>
                      <div className="text-sm text-gray-600">{role}</div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>学校管理者</CardTitle>
              <CardDescription>この学校の管理者一覧</CardDescription>
            </CardHeader>
            <CardContent>
              {school.school_admins && school.school_admins.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>氏名</TableHead>
                      <TableHead>メールアドレス</TableHead>
                      <TableHead>ステータス</TableHead>
                      <TableHead>最終ログイン</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {school.school_admins.map((admin: any) => (
                      <TableRow key={admin.id}>
                        <TableCell className="font-medium">{admin.full_name}</TableCell>
                        <TableCell>{admin.email}</TableCell>
                        <TableCell>
                          <Badge variant={admin.is_active ? "default" : "secondary"}>
                            {admin.is_active ? "有効" : "無効"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {admin.last_login_at ? new Date(admin.last_login_at).toLocaleDateString() : '未ログイン'}
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button variant="outline" size="sm">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="outline" size="sm">
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-gray-500">学校管理者が登録されていません。</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>学校設定</CardTitle>
                <CardDescription>この学校固有の機能設定</CardDescription>
              </div>
              <div className="flex space-x-2">
                {editMode ? (
                  <>
                    <Button variant="outline" size="sm" onClick={() => setEditMode(false)}>
                      <X className="h-4 w-4 mr-2" />
                      キャンセル
                    </Button>
                    <Button size="sm" onClick={handleSaveSettings}>
                      <Save className="h-4 w-4 mr-2" />
                      保存
                    </Button>
                  </>
                ) : (
                  <Button variant="outline" size="sm" onClick={() => setEditMode(true)}>
                    <Edit className="h-4 w-4 mr-2" />
                    編集
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {localSettings && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="allow_student_chat">チャット機能</Label>
                      <p className="text-sm text-muted-foreground">
                        生徒がAIとチャットできる機能を有効にします
                      </p>
                    </div>
                    <Switch
                      id="allow_student_chat"
                      checked={localSettings.allow_student_chat}
                      disabled={!editMode}
                      onCheckedChange={(checked) => setLocalSettings({
                        ...localSettings,
                        allow_student_chat: checked
                      })}
                    />
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="enable_analytics">分析機能</Label>
                      <p className="text-sm text-muted-foreground">
                        学習データの分析・統計機能を有効にします
                      </p>
                    </div>
                    <Switch
                      id="enable_analytics"
                      checked={localSettings.enable_analytics}
                      disabled={!editMode}
                      onCheckedChange={(checked) => setLocalSettings({
                        ...localSettings,
                        enable_analytics: checked
                      })}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activities" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>最近のアクティビティ</CardTitle>
              <CardDescription>この学校での最近の活動</CardDescription>
            </CardHeader>
            <CardContent>
              {school.recent_activities && school.recent_activities.length > 0 ? (
                <div className="space-y-4">
                  {school.recent_activities.map((activity: any, index: number) => (
                    <div key={index} className="flex items-center space-x-4 p-4 border rounded-lg">
                      <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{activity.description}</p>
                        <p className="text-xs text-gray-500">
                          {activity.timestamp ? new Date(activity.timestamp).toLocaleString() : '時刻不明'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">最近のアクティビティがありません。</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { useSystemSchools, useSystemOverview, useSchoolStatusToggle } from '@/hooks/useSystemAdmin';
import { SystemSchool, SystemOverview } from '@/lib/api/system-admin-client';
import { 
  School,
  Users,
  BarChart,
  Settings,
  Eye,
  Power,
  PowerOff,
  Search,
  Filter,
  Plus,
  ArrowUpRight,
  Building2,
  GraduationCap,
  UserCheck
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import Link from 'next/link';

// SystemSchoolとSystemOverviewは@/lib/api/system-admin-clientからimportしています

export default function SystemTenantManagement() {
  const [selectedSchool, setSelectedSchool] = useState<SystemSchool | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

  // API フック
  const { 
    data: overview, 
    loading: overviewLoading, 
    error: overviewError, 
    refetch: refetchOverview 
  } = useSystemOverview();
  
  const { 
    data: schools, 
    loading: schoolsLoading, 
    error: schoolsError, 
    refetch: refetchSchools 
  } = useSystemSchools({ 
    active_only: statusFilter === 'active',
    search: searchQuery 
  });

  const { 
    toggleStatus, 
    loading: toggleLoading 
  } = useSchoolStatusToggle();

  // 統合状態
  const loading = overviewLoading || schoolsLoading;
  const error = overviewError || schoolsError;

  const fetchData = async () => {
    await Promise.all([refetchOverview(), refetchSchools()]);
  };

  const filteredSchools = schools?.filter(school => {
    const matchesSearch = school.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         school.school_code.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && school.is_active) ||
                         (statusFilter === 'inactive' && !school.is_active);

    return matchesSearch && matchesStatus;
  }) || [];

  const handleToggleSchoolStatus = async (schoolId: string, currentStatus: boolean) => {
    try {
      await toggleStatus(schoolId, currentStatus);
      
      // データ再取得
      await fetchData();
      
      // 成功メッセージ（実装時はtoastなどで表示）
      console.log(`学校のステータスを${!currentStatus ? '有効' : '無効'}に変更しました`);
      
    } catch (err) {
      console.error('学校ステータスの更新に失敗しました:', err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">テナント管理</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={fetchData}>再試行</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">テナント管理</h1>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={fetchData}>
            <BarChart className="h-4 w-4 mr-2" />
            データ更新
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            新規学校登録
          </Button>
        </div>
      </div>

      {/* システム概要カード */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">登録学校数</CardTitle>
              <Building2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview.schools.total}</div>
              <p className="text-xs text-muted-foreground">
                有効: {overview.schools.active} / 無効: {overview.schools.inactive}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">総ユーザー数</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview.users.total}</div>
              <p className="text-xs text-muted-foreground">
                今月アクティブ: {overview.users.active_this_month}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">担当関係数</CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview.assignments.total}</div>
              <p className="text-xs text-muted-foreground">
                アクティブ: {overview.assignments.active}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">教員数</CardTitle>
              <GraduationCap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(overview.users.by_role["教員"] || 0) + (overview.users.by_role["学校管理者"] || 0)}
              </div>
              <p className="text-xs text-muted-foreground">
                管理者: {overview.users.by_role["学校管理者"] || 0}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* フィルター・検索 */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="学校名または学校コードで検索"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={statusFilter} onValueChange={(value: 'all' | 'active' | 'inactive') => setStatusFilter(value)}>
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">すべて</SelectItem>
            <SelectItem value="active">有効</SelectItem>
            <SelectItem value="inactive">無効</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 学校一覧テーブル */}
      <Card>
        <CardHeader>
          <CardTitle>学校一覧</CardTitle>
          <CardDescription>
            {filteredSchools.length}件の学校が登録されています
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>学校名</TableHead>
                <TableHead>学校コード</TableHead>
                <TableHead>所在地</TableHead>
                <TableHead>ユーザー数</TableHead>
                <TableHead>担当関係</TableHead>
                <TableHead>ステータス</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSchools.map((school) => (
                <TableRow key={school.id}>
                  <TableCell className="font-medium">{school.name}</TableCell>
                  <TableCell>{school.school_code}</TableCell>
                  <TableCell>
                    {school.details ? `${school.details.prefecture} ${school.details.city}` : '-'}
                  </TableCell>
                  <TableCell>{school.statistics.total_users}</TableCell>
                  <TableCell>
                    {school.statistics.assignments.active}/{school.statistics.assignments.total}
                  </TableCell>
                  <TableCell>
                    <Badge variant={school.is_active ? "default" : "secondary"}>
                      {school.is_active ? "有効" : "無効"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => setSelectedSchool(school)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-4xl">
                          <DialogHeader>
                            <DialogTitle>{school.name} - 詳細情報</DialogTitle>
                            <DialogDescription>
                              学校の詳細情報と統計データ
                            </DialogDescription>
                          </DialogHeader>
                          {selectedSchool && (
                            <SchoolDetailDialog school={selectedSchool} />
                          )}
                        </DialogContent>
                      </Dialog>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleSchoolStatus(school.id, school.is_active)}
                        disabled={toggleLoading}
                      >
                        {school.is_active ? (
                          <PowerOff className="h-4 w-4 text-red-600" />
                        ) : (
                          <Power className="h-4 w-4 text-green-600" />
                        )}
                      </Button>

                      <Link href={`/admin/tenant-management/${school.id}`}>
                        <Button variant="outline" size="sm">
                          <ArrowUpRight className="h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// 学校詳細ダイアログコンポーネント
function SchoolDetailDialog({ school }: { school: SystemSchool }) {
  return (
    <div className="space-y-6">
      {/* 基本情報 */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold mb-2">基本情報</h3>
          <div className="space-y-2 text-sm">
            <div><span className="font-medium">学校名:</span> {school.name}</div>
            <div><span className="font-medium">学校コード:</span> {school.school_code}</div>
            <div><span className="font-medium">校長:</span> {school.details?.principal_name || '-'}</div>
            <div><span className="font-medium">住所:</span> {school.details?.address || '-'}</div>
          </div>
        </div>
        <div>
          <h3 className="font-semibold mb-2">システム情報</h3>
          <div className="space-y-2 text-sm">
            <div><span className="font-medium">ステータス:</span> 
              <Badge variant={school.is_active ? "default" : "secondary"} className="ml-2">
                {school.is_active ? "有効" : "無効"}
              </Badge>
            </div>
            <div><span className="font-medium">作成日:</span> {new Date(school.created_at).toLocaleDateString()}</div>
            <div><span className="font-medium">更新日:</span> {new Date(school.updated_at).toLocaleDateString()}</div>
          </div>
        </div>
      </div>

      {/* 統計情報 */}
      <div>
        <h3 className="font-semibold mb-2">統計情報</h3>
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">ユーザー構成</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                {Object.entries(school.statistics.users).map(([role, count]) => (
                  <div key={role} className="flex justify-between">
                    <span>{role}:</span>
                    <span className="font-medium">{count}人</span>
                  </div>
                ))}
                <div className="border-t pt-1 flex justify-between font-semibold">
                  <span>合計:</span>
                  <span>{school.statistics.total_users}人</span>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">担当関係</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>アクティブ:</span>
                  <span className="font-medium">{school.statistics.assignments.active}件</span>
                </div>
                <div className="flex justify-between">
                  <span>総数:</span>
                  <span className="font-medium">{school.statistics.assignments.total}件</span>
                </div>
                <div className="border-t pt-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ 
                        width: `${(school.statistics.assignments.active / Math.max(school.statistics.assignments.total, 1)) * 100}%` 
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 設定情報 */}
      {school.settings && (
        <div>
          <h3 className="font-semibold mb-2">学校設定</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">チャット機能:</span>
              <Badge variant={school.settings.allow_student_chat ? "default" : "secondary"} className="ml-2">
                {school.settings.allow_student_chat ? "有効" : "無効"}
              </Badge>
            </div>
            <div>
              <span className="font-medium">分析機能:</span>
              <Badge variant={school.settings.enable_analytics ? "default" : "secondary"} className="ml-2">
                {school.settings.enable_analytics ? "有効" : "無効"}
              </Badge>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

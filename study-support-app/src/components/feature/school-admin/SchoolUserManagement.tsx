'use client';

import { useEffect, useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { 
  Users, 
  UserPlus, 
  Search, 
  Filter,
  MoreHorizontal,
  UserCheck,
  GraduationCap,
  Settings,
  Mail,
  Calendar,
  Eye
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { SchoolUser } from '@/types/tenant';
import Link from 'next/link';

export default function SchoolUserManagement() {
  const { currentSchool, getSchoolUsers } = useTenant();
  const [users, setUsers] = useState<SchoolUser[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<SchoolUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // フィルター状態
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  useEffect(() => {
    const fetchUsers = async () => {
      if (!currentSchool) return;

      try {
        setIsLoading(true);
        setError(null);
        
        const userData = await getSchoolUsers();
        setUsers(userData);
        setFilteredUsers(userData);
      } catch (err) {
        console.error('Failed to fetch users:', err);
        setError('ユーザーデータの取得に失敗しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, [currentSchool, getSchoolUsers]);

  // フィルタリング処理
  useEffect(() => {
    let filtered = users;

    // 検索クエリによるフィルタリング
    if (searchQuery) {
      filtered = filtered.filter(user =>
        user.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (user.studentNumber && user.studentNumber.includes(searchQuery))
      );
    }

    // ロールによるフィルタリング
    if (roleFilter !== 'all') {
      filtered = filtered.filter(user => user.role === roleFilter);
    }

    // ステータスによるフィルタリング
    if (statusFilter !== 'all') {
      const isActive = statusFilter === 'active';
      filtered = filtered.filter(user => user.isActive === isActive);
    }

    setFilteredUsers(filtered);
  }, [users, searchQuery, roleFilter, statusFilter]);

  if (isLoading) {
    return <UserManagementSkeleton />;
  }

  if (error) {
    return <UserManagementError error={error} onRetry={() => window.location.reload()} />;
  }

  const userStats = {
    total: users.length,
    active: users.filter(u => u.isActive).length,
    students: users.filter(u => u.role === 'student').length,
    teachers: users.filter(u => u.role === 'teacher').length,
    schoolAdmins: users.filter(u => u.role === 'school_admin').length
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ユーザー管理</h1>
          <p className="text-gray-600">
            学校のユーザーを管理します
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button>
            <UserPlus className="h-4 w-4 mr-2" />
            新規ユーザー招待
          </Button>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatsCard
          title="総ユーザー数"
          value={userStats.total}
          icon={<Users className="h-5 w-5" />}
        />
        <StatsCard
          title="アクティブ"
          value={userStats.active}
          icon={<Users className="h-5 w-5 text-green-600" />}
        />
        <StatsCard
          title="生徒"
          value={userStats.students}
          icon={<GraduationCap className="h-5 w-5 text-blue-600" />}
        />
        <StatsCard
          title="先生"
          value={userStats.teachers}
          icon={<UserCheck className="h-5 w-5 text-purple-600" />}
        />
        <StatsCard
          title="管理者"
          value={userStats.schoolAdmins}
          icon={<Settings className="h-5 w-5 text-orange-600" />}
        />
      </div>

      {/* フィルターと検索 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="h-5 w-5 mr-2" />
            フィルター・検索
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="名前、メールアドレス、出席番号で検索..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={roleFilter} onValueChange={setRoleFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="ロール" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全ロール</SelectItem>
                  <SelectItem value="student">生徒</SelectItem>
                  <SelectItem value="teacher">先生</SelectItem>
                  <SelectItem value="school_admin">管理者</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="状態" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全状態</SelectItem>
                  <SelectItem value="active">アクティブ</SelectItem>
                  <SelectItem value="inactive">非アクティブ</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ユーザーテーブル */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>ユーザー一覧</CardTitle>
              <CardDescription>
                {filteredUsers.length}件のユーザーが表示されています
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ユーザー</TableHead>
                  <TableHead>ロール</TableHead>
                  <TableHead>学年・クラス</TableHead>
                  <TableHead>状態</TableHead>
                  <TableHead>最終ログイン</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                      条件に一致するユーザーが見つかりません
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredUsers.map((user) => (
                    <UserTableRow key={user.id} user={user} />
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
}

function StatsCard({ title, value, icon }: StatsCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          </div>
          <div className="text-gray-400">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function UserTableRow({ user }: { user: SchoolUser }) {
  const getRoleBadge = (role: string) => {
    const roleConfig = {
      student: { label: '生徒', variant: 'default' as const },
      teacher: { label: '先生', variant: 'secondary' as const },
      school_admin: { label: '管理者', variant: 'destructive' as const }
    };
    
    const config = roleConfig[role as keyof typeof roleConfig] || { label: role, variant: 'outline' as const };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getGradeInfo = (user: SchoolUser) => {
    if (user.role === 'student' && user.grade && user.className) {
      return `${user.grade}年${user.className}組`;
    }
    return '-';
  };

  const getLastLoginText = (lastLoginAt?: string) => {
    if (!lastLoginAt) return '未ログイン';
    
    const now = new Date();
    const loginTime = new Date(lastLoginAt);
    const diffInHours = Math.floor((now.getTime() - loginTime.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return '1時間以内';
    if (diffInHours < 24) return `${diffInHours}時間前`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}日前`;
    
    return loginTime.toLocaleDateString('ja-JP');
  };

  const getUserDetailPath = () => {
    switch (user.role) {
      case 'student':
        return `/school-admin/students/${user.id}`;
      case 'teacher':
        return `/school-admin/teachers/${user.id}`;
      default:
        return `/school-admin/users/${user.id}`;
    }
  };

  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center space-x-3">
          <Avatar className="h-8 w-8">
            <AvatarImage src={user.profileImageUrl} alt={user.fullName} />
            <AvatarFallback>
              {user.fullName.charAt(0)}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium text-gray-900">{user.fullName}</p>
            <p className="text-sm text-gray-500">{user.email}</p>
            {user.studentNumber && (
              <p className="text-xs text-gray-400">出席番号: {user.studentNumber}</p>
            )}
          </div>
        </div>
      </TableCell>
      <TableCell>
        {getRoleBadge(user.role)}
      </TableCell>
      <TableCell>
        <span className="text-sm text-gray-900">{getGradeInfo(user)}</span>
      </TableCell>
      <TableCell>
        <Badge variant={user.isActive ? 'default' : 'secondary'}>
          {user.isActive ? 'アクティブ' : '非アクティブ'}
        </Badge>
      </TableCell>
      <TableCell>
        <div className="flex items-center text-sm text-gray-600">
          <Calendar className="h-4 w-4 mr-1" />
          {getLastLoginText(user.lastLoginAt)}
        </div>
      </TableCell>
      <TableCell className="text-right">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">メニューを開く</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>操作</DropdownMenuLabel>
            <DropdownMenuItem asChild>
              <Link href={getUserDetailPath()}>
                <Eye className="h-4 w-4 mr-2" />
                詳細を見る
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Mail className="h-4 w-4 mr-2" />
              メール送信
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Settings className="h-4 w-4 mr-2" />
              設定
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}

function UserManagementSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-20 bg-gray-200 rounded animate-pulse"></div>
        ))}
      </div>
      <div className="h-32 bg-gray-200 rounded animate-pulse"></div>
      <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
    </div>
  );
}

function UserManagementError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <Users className="h-12 w-12 text-red-500 mx-auto mb-4" />
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
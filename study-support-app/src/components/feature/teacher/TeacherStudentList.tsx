'use client';

import { useEffect, useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { useAssignedStudents } from '@/hooks/useTenantApi';
import { 
  Users, 
  Search, 
  GraduationCap,
  MessageSquare,
  FileText,
  School,
  Eye,
  Clock,
  CheckCircle,
  TrendingUp
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
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { SchoolUser } from '@/types/tenant';
import Link from 'next/link';

export default function TeacherStudentList() {
  const { currentUser, currentSchool, getTeacherStudents } = useTenant();
  const [students, setStudents] = useState<SchoolUser[]>([]);
  const [filteredStudents, setFilteredStudents] = useState<SchoolUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // フィルター状態
  const [searchQuery, setSearchQuery] = useState('');
  const [gradeFilter, setGradeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('name');

  useEffect(() => {
    const fetchStudents = async () => {
      if (!currentUser || !currentSchool) return;

      try {
        setIsLoading(true);
        setError(null);
        
        // 現在のユーザーが先生の場合、担当生徒を取得
        const studentData = await getTeacherStudents(currentSchool.id, currentUser.id);
        setStudents(studentData);
        setFilteredStudents(studentData);
      } catch (err) {
        console.error('Failed to fetch students:', err);
        setError('担当生徒データの取得に失敗しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStudents();
  }, [currentUser, currentSchool, getTeacherStudents]);

  // フィルタリング処理
  useEffect(() => {
    let filtered = students;

    // 検索クエリによるフィルタリング
    if (searchQuery) {
      filtered = filtered.filter(student =>
        student.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (student.studentNumber && student.studentNumber.includes(searchQuery)) ||
        (student.className && student.className.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // 学年によるフィルタリング
    if (gradeFilter !== 'all') {
      filtered = filtered.filter(student => student.grade === gradeFilter);
    }

    // ソート処理
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.fullName.localeCompare(b.fullName);
        case 'grade':
          const gradeA = parseInt(a.grade || '0');
          const gradeB = parseInt(b.grade || '0');
          if (gradeA !== gradeB) return gradeB - gradeA;
          return a.fullName.localeCompare(b.fullName);
        case 'lastLogin':
          const timeA = a.lastLoginAt ? new Date(a.lastLoginAt).getTime() : 0;
          const timeB = b.lastLoginAt ? new Date(b.lastLoginAt).getTime() : 0;
          return timeB - timeA;
        default:
          return 0;
      }
    });

    setFilteredStudents(filtered);
  }, [students, searchQuery, gradeFilter, sortBy]);

  if (isLoading) {
    return <StudentListSkeleton />;
  }

  if (error) {
    return <StudentListError error={error} onRetry={() => window.location.reload()} />;
  }

  const studentStats = {
    total: students.length,
    active: students.filter(s => s.isActive).length,
    byGrade: students.reduce((acc, student) => {
      const grade = student.grade || 'その他';
      acc[grade] = (acc[grade] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">担当生徒一覧</h1>
          <p className="text-gray-600">
            あなたが担当している生徒の一覧と進捗状況
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Badge variant="secondary" className="px-3 py-1">
            {currentSchool?.name}
          </Badge>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatsCard
          title="総担当生徒"
          value={studentStats.total}
          icon={<Users className="h-5 w-5" />}
        />
        <StatsCard
          title="アクティブ"
          value={studentStats.active}
          icon={<CheckCircle className="h-5 w-5 text-green-600" />}
        />
        <StatsCard
          title="3年生"
          value={studentStats.byGrade['3'] || 0}
          icon={<GraduationCap className="h-5 w-5 text-red-600" />}
        />
        <StatsCard
          title="2年生"
          value={studentStats.byGrade['2'] || 0}
          icon={<GraduationCap className="h-5 w-5 text-blue-600" />}
        />
      </div>

      {/* フィルターと検索 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Search className="h-5 w-5 mr-2" />
            検索・フィルター
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="名前、出席番号、クラスで検索..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={gradeFilter} onValueChange={setGradeFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="学年" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全学年</SelectItem>
                  <SelectItem value="3">3年生</SelectItem>
                  <SelectItem value="2">2年生</SelectItem>
                  <SelectItem value="1">1年生</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="並び順" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">名前順</SelectItem>
                  <SelectItem value="grade">学年順</SelectItem>
                  <SelectItem value="lastLogin">最終ログイン順</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 生徒一覧 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredStudents.length === 0 ? (
          <div className="col-span-full">
            <Card>
              <CardContent className="text-center py-12">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  生徒が見つかりません
                </h3>
                <p className="text-gray-600 mb-4">
                  条件に一致する生徒がいません。フィルターを調整してください。
                </p>
              </CardContent>
            </Card>
          </div>
        ) : (
          filteredStudents.map((student) => (
            <StudentCard key={student.id} student={student} />
          ))
        )}
      </div>
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

function StudentCard({ student }: { student: SchoolUser }) {
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

  const getGradeDisplayName = (grade?: string, className?: string) => {
    if (grade && className) {
      return `${grade}年${className}組`;
    }
    if (grade) {
      return `${grade}年生`;
    }
    return '学年不明';
  };

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={student.profileImageUrl} alt={student.fullName} />
              <AvatarFallback>
                {student.fullName.charAt(0)}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-lg">{student.fullName}</CardTitle>
              <CardDescription>
                {getGradeDisplayName(student.grade, student.className)}
                {student.studentNumber && ` (${student.studentNumber}番)`}
              </CardDescription>
            </div>
          </div>
          <Badge variant={student.isActive ? 'default' : 'secondary'}>
            {student.isActive ? 'アクティブ' : '非アクティブ'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 最終ログイン */}
        <div className="flex items-center text-sm text-gray-600">
          <Clock className="h-4 w-4 mr-2" />
          最終ログイン: {getLastLoginText(student.lastLoginAt)}
        </div>

        {/* 進捗情報（Mock データ） */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="flex flex-col items-center p-2 bg-blue-50 rounded-lg">
            <MessageSquare className="h-4 w-4 text-blue-600 mb-1" />
            <span className="text-xs text-gray-600">チャット</span>
            <span className="text-sm font-semibold">5</span>
          </div>
          <div className="flex flex-col items-center p-2 bg-green-50 rounded-lg">
            <FileText className="h-4 w-4 text-green-600 mb-1" />
            <span className="text-xs text-gray-600">志望理由書</span>
            <span className="text-sm font-semibold">2</span>
          </div>
          <div className="flex flex-col items-center p-2 bg-purple-50 rounded-lg">
            <School className="h-4 w-4 text-purple-600 mb-1" />
            <span className="text-xs text-gray-600">志望校</span>
            <span className="text-sm font-semibold">3</span>
          </div>
        </div>

        {/* アクションボタン */}
        <div className="pt-2 border-t">
          <Button asChild className="w-full" size="sm">
            <Link href={`/teacher/students/${student.id}`}>
              <Eye className="h-4 w-4 mr-2" />
              詳細を見る
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function StudentListSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-20 bg-gray-200 rounded animate-pulse"></div>
        ))}
      </div>
      <div className="h-32 bg-gray-200 rounded animate-pulse"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-64 bg-gray-200 rounded animate-pulse"></div>
        ))}
      </div>
    </div>
  );
}

function StudentListError({ error, onRetry }: { error: string; onRetry: () => void }) {
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
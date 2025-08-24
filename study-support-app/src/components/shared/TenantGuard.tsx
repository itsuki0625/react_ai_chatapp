'use client';

import { ReactNode } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { AlertTriangle, Lock, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

interface TenantGuardProps {
  children: ReactNode;
  requiredRole?: 'school_admin' | 'teacher' | 'student';
  requiredPermissions?: string[];
  fallback?: ReactNode;
  redirectTo?: string;
  allowSystemAdmin?: boolean;
}

/**
 * テナント境界を強制し、適切な権限を持つユーザーのみアクセスを許可するコンポーネント
 */
export function TenantGuard({ 
  children, 
  requiredRole, 
  requiredPermissions = [],
  fallback,
  redirectTo,
  allowSystemAdmin = true
}: TenantGuardProps) {
  const { 
    currentUser, 
    currentSchool,
    isSystemAdmin,
    isSchoolAdmin,
    isTeacher,
    isStudent,
    hasPermission,
    isLoading 
  } = useTenant();
  
  const router = useRouter();

  // ローディング中
  if (isLoading) {
    return (
      <div className="flex h-64 w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-lg text-gray-600">認証情報を確認中...</span>
      </div>
    );
  }

  // ユーザーが未認証
  if (!currentUser) {
    return (
      <div className="flex h-64 w-full items-center justify-center">
        <Alert className="max-w-md">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>認証が必要です</AlertTitle>
          <AlertDescription>
            このページにアクセスするにはログインが必要です。
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // 学校が選択されていない（システム管理者以外）
  if (!currentSchool && !isSystemAdmin) {
    return (
      <div className="flex h-64 w-full items-center justify-center">
        <Alert className="max-w-md">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>学校情報が見つかりません</AlertTitle>
          <AlertDescription>
            アクセスする学校が選択されていません。
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // システム管理者は基本的に全てのアクセスを許可
  if (allowSystemAdmin && isSystemAdmin) {
    return <>{children}</>;
  }

  // ロールチェック
  if (requiredRole) {
    let hasRequiredRole = false;

    switch (requiredRole) {
      case 'school_admin':
        hasRequiredRole = isSchoolAdmin;
        break;
      case 'teacher':
        hasRequiredRole = isTeacher;
        break;
      case 'student':
        hasRequiredRole = isStudent;
        break;
    }

    if (!hasRequiredRole) {
      if (fallback) {
        return <>{fallback}</>;
      }

      return (
        <AccessDeniedMessage 
          reason={`この機能は${getRoleDisplayName(requiredRole)}専用です。`}
          redirectTo={redirectTo}
        />
      );
    }
  }

  // 権限チェック
  if (requiredPermissions.length > 0) {
    if (!hasPermission(requiredPermissions)) {
      if (fallback) {
        return <>{fallback}</>;
      }

      return (
        <AccessDeniedMessage 
          reason="この機能にアクセスする権限がありません。"
          redirectTo={redirectTo}
        />
      );
    }
  }

  // 全てのチェックをパス
  return <>{children}</>;
}

interface AccessDeniedMessageProps {
  reason: string;
  redirectTo?: string;
}

function AccessDeniedMessage({ reason, redirectTo }: AccessDeniedMessageProps) {
  const router = useRouter();

  const handleRedirect = () => {
    if (redirectTo) {
      router.push(redirectTo);
    } else {
      router.back();
    }
  };

  return (
    <div className="flex h-64 w-full items-center justify-center">
      <Alert className="max-w-md">
        <Lock className="h-4 w-4" />
        <AlertTitle>アクセス拒否</AlertTitle>
        <AlertDescription className="mb-4">
          {reason}
        </AlertDescription>
        <Button onClick={handleRedirect} variant="outline" size="sm">
          {redirectTo ? '戻る' : '前のページに戻る'}
        </Button>
      </Alert>
    </div>
  );
}

function getRoleDisplayName(role: string): string {
  const roleNames = {
    school_admin: '学校管理者',
    teacher: '先生',
    student: '生徒'
  };
  
  return roleNames[role as keyof typeof roleNames] || role;
}

/**
 * 特定のロールのユーザーのみアクセス可能なページをラップするヘルパーコンポーネント
 */
export function SchoolAdminOnly({ children }: { children: ReactNode }) {
  return (
    <TenantGuard
      requiredRole="school_admin"
      requiredPermissions={['school_manage_users']}
      redirectTo="/dashboard"
    >
      {children}
    </TenantGuard>
  );
}

export function TeacherOnly({ children }: { children: ReactNode }) {
  return (
    <TenantGuard
      requiredRole="teacher"
      requiredPermissions={['teacher_view_assigned_students']}
      redirectTo="/dashboard"
    >
      {children}
    </TenantGuard>
  );
}

export function StudentOnly({ children }: { children: ReactNode }) {
  return (
    <TenantGuard
      requiredRole="student"
      requiredPermissions={['student_manage_own_data']}
      redirectTo="/dashboard"
    >
      {children}
    </TenantGuard>
  );
}
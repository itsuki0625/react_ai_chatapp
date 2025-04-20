"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { Loader2 } from 'lucide-react';
import TeacherNavbar from '@/components/teacher/TeacherNavbar';

export default function TeacherLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { data: session, status } = useSession();

  // セッション状態を監視して認証とロールチェックを行う
  useEffect(() => {
    // ロード中はスキップ
    if (status === 'loading') return;

    // 認証されていない場合はログインページへリダイレクト
    if (status === 'unauthenticated') {
      console.log('未認証ユーザー - ログインページへリダイレクト');
      router.push('/login?redirect=' + encodeURIComponent('/teacher/dashboard'));
      return;
    }

    // 認証されているが教師ロールがない場合はダッシュボードへリダイレクト
    if (status === 'authenticated' && session) {
      const userRoles = session.user.role || [];
      const isTeacher = userRoles.includes('teacher') || session.user.isTeacher;
      
      if (!isTeacher) {
        console.log('教師権限なし - ダッシュボードへリダイレクト');
        router.push('/dashboard');
        return;
      }
    }
  }, [session, status, router]);

  // ロード中の表示
  if (status === 'loading') {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-lg">ロード中...</span>
      </div>
    );
  }

  // 認証済みかつ教師の場合のみ子コンポーネントを表示
  if (status === 'authenticated' && session) {
    const userRoles = session.user.role || [];
    const isTeacher = userRoles.includes('teacher') || session.user.isTeacher;
    
    if (isTeacher) {
      return (
        <div className="min-h-screen bg-gray-50">
          <TeacherNavbar />
          <main className="container mx-auto p-4 sm:p-6 md:p-8">
            {children}
          </main>
        </div>
      );
    }
  }

  // ロード中以外の状態での表示（通常はリダイレクトされるため表示されない）
  return (
    <div className="flex h-screen w-full items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      <span className="ml-2 text-lg">認証確認中...</span>
    </div>
  );
} 
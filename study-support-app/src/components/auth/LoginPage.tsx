"use client";

import React, { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { LoginForm } from './LoginForm';

const LoginPage = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoading } = useAuth();
  
  // リダイレクト先のURLを取得
  const redirectPath = searchParams.get('redirect') || '/dashboard';

  useEffect(() => {
    // ユーザーが既にログインしている場合
    if (!isLoading && user) {
      // 管理者権限を持つユーザーかどうかを確認
      const isAdmin = user.role && 
                     user.role.permissions && 
                     user.role.permissions.includes('admin');

      // 管理者の場合は管理者ダッシュボードへ、それ以外は指定されたリダイレクト先へ
      if (isAdmin && redirectPath === '/dashboard') {
        router.push('/admin/dashboard');
      } else {
        router.push(redirectPath);
      }
    }
  }, [user, isLoading, router, redirectPath]);

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">読み込み中...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">ログイン</h1>
      <LoginForm />
    </div>
  );
};

export default LoginPage;
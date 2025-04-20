import React, { useState } from 'react';
import { signOut } from 'next-auth/react';
import { apiClient } from '@/lib/api-client';

export default function LogoutButton() {
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (isLoggingOut) return; // 二重クリック防止
    
    setIsLoggingOut(true);
    
    try {
      // バックエンドのログアウトAPIも呼び出す（セッションクッキー削除のため）
      await apiClient.post('/api/v1/auth/logout');
      
      // NextAuthのログアウト処理
      await signOut({ redirect: true, callbackUrl: '/login' });
    } catch (error) {
      console.error('ログアウト中にエラーが発生しました:', error);
      setIsLoggingOut(false);
      
      // エラーが発生した場合でもNextAuthのログアウトを試みる
      try {
        await signOut({ redirect: true, callbackUrl: '/login' });
      } catch (e) {
        console.error('NextAuthのログアウトにも失敗しました:', e);
      }
    }
  };

  return (
    <button
      onClick={handleLogout}
      disabled={isLoggingOut}
      className={`px-4 py-2 text-white rounded ${isLoggingOut ? 'bg-red-400' : 'bg-red-600 hover:bg-red-700'}`}
    >
      {isLoggingOut ? 'ログアウト中...' : 'ログアウト'}
    </button>
  );
} 
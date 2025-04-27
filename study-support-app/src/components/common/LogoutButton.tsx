import React, { useState } from 'react';
import { signOut } from 'next-auth/react';
import { apiClient } from '@/lib/api-client';

export default function LogoutButton() {
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (isLoggingOut) return; // 二重クリック防止

    setIsLoggingOut(true);

    try {
      // 先に NextAuth の signOut を呼び出す
      // コールバックURLを指定して、成功したらそのページに遷移
      await signOut({ callbackUrl: '/login' });

      // ★注意: signOut が完了するとページ遷移が発生するため、
      //   通常、この下のコード（API呼び出し）は実行されない可能性が高い。
      //   もしバックエンドでの追加処理が必要な場合は、
      //   NextAuth の events.signOut コールバックを使うのが確実。

      // --- 必要であれば残すが、signOut の後では実行されない可能性あり ---
      /*
      // バックエンドのログアウトAPIも呼び出す（セッションクッキー削除のため）
      await apiClient.post('/api/v1/auth/logout');
      console.log("Backend logout API called after signOut (may not run if redirect happens first)");
      */
      // ---------------------------------------------------------------

    } catch (error) {
      console.error('ログアウト中にエラーが発生しました:', error);
      // setIsLoggingOut(false); // ページ遷移するので不要になることが多い

      // エラーが発生した場合でもNextAuthのログアウトを試みる（すでに実行試行済みだが）
      try {
        await signOut({ callbackUrl: '/login' });
      } catch (e) {
        console.error('NextAuthのログアウトにも失敗しました:', e);
      }
    } finally {
       // ページ遷移が始まるので、必ずしも false に戻す必要はないかもしれない
       // setIsLoggingOut(false);
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
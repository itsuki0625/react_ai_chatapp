"use client";

import React from 'react';
import Link from 'next/link';
import { signOut } from 'next-auth/react';
import { usePathname } from 'next/navigation';

export const AdminNavBar: React.FC = () => {
  const pathname = usePathname();
  
  const handleLogout = async () => {
    if (confirm('ログアウトしますか？')) {
      try {
        // 先に NextAuth の signOut を呼び出す
        // コールバックURLを指定して、成功したらそのページに遷移
        await signOut({ callbackUrl: '/login?status=logged_out' });

        // ★注意: signOut が完了するとページ遷移が発生するため、
        //   通常、この下のコード（fetch）は実行されない可能性が高い。
        //   もしバックエンドでの追加処理が必要な場合は、
        //   NextAuth の events.signOut コールバックを使うか、
        //   別の方法（例：useEffect でログアウト状態を監視）を検討する。

        // --- 必要であれば残すが、signOut の後では実行されない可能性あり ---
        /*
        const session = await getSession();
        const accessToken = (session as any)?.accessToken;
        const headers: HeadersInit = {};
        if (accessToken) {
          headers['Authorization'] = `Bearer ${accessToken}`;
        }
        const apiUrl = process.env.NEXT_PUBLIC_BROWSER_API_URL || 'http://localhost:5050';
        await fetch(`${apiUrl}/api/v1/auth/logout`, {
          method: 'POST',
          credentials: 'include',
          headers: headers,
        });
        console.log("Backend logout API called after signOut (may not run if redirect happens first)");
        */
       // ---------------------------------------------------------------

      } catch (err) {
        console.error('ログアウト中にエラーが発生しました:', err);
        alert('ログアウト処理中にエラーが発生しました。');
        // エラー時も念のため signOut を試みる（すでに実行試行済みだが）
        try {
           await signOut({ callbackUrl: '/login?status=logged_out' });
        } catch(e) {
           console.error('Error during final signOut attempt:', e);
        }
      }
    }
  };

  const navItems = [
    { label: '管理ダッシュボード', path: '/admin/dashboard' },
    { label: 'ユーザー管理', path: '/admin/users' },
    { label: 'コンテンツ管理', path: '/admin/content' },
    { label: 'サブスクリプション', path: '/admin/subscription' },
    { label: '通知管理', path: '/admin/notification-settings' },
  ];

  return (
    <div className="bg-white shadow-sm py-3 px-6 mb-6">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-bold text-gray-900">管理パネル</h1>
          <nav>
            <ul className="flex space-x-4">
              {navItems.map((item) => (
                <li key={item.path}>
                  <Link
                    href={item.path}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      pathname === item.path
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
        >
          ログアウト
        </button>
      </div>
    </div>
  );
}; 
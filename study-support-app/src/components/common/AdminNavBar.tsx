"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { signOut } from 'next-auth/react';

export const AdminNavBar: React.FC = () => {
  const pathname = usePathname();
  
  const handleLogout = async () => {
    if (confirm('ログアウトしますか？')) {
      try {
        // バックエンドのログアウトAPIも呼び出し
        await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/logout`, {
          method: 'POST',
          credentials: 'include',
        });
        
        // NextAuthのログアウト処理
        await signOut({ redirect: true, callbackUrl: '/login' });
      } catch (err) {
        console.error('ログアウト中にエラーが発生しました:', err);
        alert('ログアウトに失敗しました。');
        
        // エラーが発生した場合でもNextAuthのログアウトを試みる
        try {
          await signOut({ redirect: true, callbackUrl: '/login' });
        } catch (e) {
          console.error('NextAuthのログアウトにも失敗しました:', e);
        }
      }
    }
  };

  const navItems = [
    { label: '管理ダッシュボード', path: '/admin/dashboard' },
    { label: 'サブスクリプション', path: '/admin/subscription' },
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
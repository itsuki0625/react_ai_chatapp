'use client';

import Link from 'next/link';
import { useSession } from 'next-auth/react';

export const Navbar = () => {
  const { data: session, status } = useSession();
  
  const isAuthenticated = status === 'authenticated';
  const isAdmin = session?.user?.isAdmin || false;

  return (
    <nav className="bg-white shadow">
      <div className="container mx-auto px-6 py-3">
        <div className="flex justify-between">
          <div className="flex items-center">
            <Link href={isAdmin ? "/admin/dashboard" : "/dashboard"} className="text-xl font-bold text-gray-800">
              Study Support
            </Link>
          </div>
          
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="text-gray-700 hover:text-blue-500">
                  ダッシュボード
                </Link>
                
                {/* 管理者の場合のみ管理者ダッシュボードへのリンクを表示 */}
                {isAdmin && (
                  <Link href="/admin/dashboard" className="text-gray-700 hover:text-blue-500">
                    管理者ダッシュボード
                  </Link>
                )}
                
                {/* その他のナビゲーションリンク */}
              </>
            ) : (
              <>
                <Link href="/login" className="text-gray-700 hover:text-blue-500">
                  ログイン
                </Link>
                <Link href="/signup" className="text-gray-700 hover:text-blue-500">
                  新規登録
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}; 
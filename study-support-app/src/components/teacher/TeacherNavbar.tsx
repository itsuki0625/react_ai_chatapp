"use client";

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import {
  Users,
  FileText,
  MessageSquare,
  Home,
  Book,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { useState } from 'react';

export default function TeacherNavbar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    {
      name: 'ダッシュボード',
      href: '/teacher/dashboard',
      icon: <Home className="h-5 w-5" />
    },
    {
      name: '生徒一覧',
      href: '/teacher/students',
      icon: <Users className="h-5 w-5" />
    },
    {
      name: '添削リクエスト',
      href: '/teacher/reviews',
      icon: <FileText className="h-5 w-5" />
    },
    {
      name: '教材管理',
      href: '/teacher/materials',
      icon: <Book className="h-5 w-5" />
    },
    {
      name: 'メッセージ',
      href: '/teacher/messages',
      icon: <MessageSquare className="h-5 w-5" />
    }
  ];

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleSignOut = async () => {
    await signOut({ redirect: true, callbackUrl: '/login' });
  };

  return (
    <nav className="bg-white shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          <div className="flex">
            <div className="flex flex-shrink-0 items-center">
              <Link href="/teacher/dashboard" className="text-xl font-bold text-blue-600">
                Teacher Portal
              </Link>
            </div>
          </div>

          {/* デスクトップメニュー */}
          <div className="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-4">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={`group inline-flex items-center px-3 py-2 text-sm font-medium ${
                  pathname === item.href
                    ? 'text-blue-600'
                    : 'text-gray-700 hover:text-blue-500'
                }`}
              >
                <span className="mr-2">{item.icon}</span>
                {item.name}
              </Link>
            ))}
          </div>

          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">
                {typeof session?.user?.name === 'string' ? session.user.name : '講師'}
              </span>
              <button
                onClick={handleSignOut}
                className="rounded-md bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-500"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* モバイルメニューボタン */}
          <div className="flex items-center sm:hidden">
            <button
              onClick={toggleMobileMenu}
              className="inline-flex items-center justify-center rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* モバイルメニュー */}
      {isMobileMenuOpen && (
        <div className="sm:hidden">
          <div className="space-y-1 pb-3 pt-2">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={`block px-4 py-2 text-base font-medium ${
                  pathname === item.href
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-blue-500'
                }`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <div className="flex items-center">
                  <span className="mr-3">{item.icon}</span>
                  {item.name}
                </div>
              </Link>
            ))}
            <button
              onClick={handleSignOut}
              className="flex w-full items-center px-4 py-2 text-base font-medium text-gray-700 hover:bg-gray-50 hover:text-blue-500"
            >
              <LogOut className="mr-3 h-5 w-5" />
              ログアウト
            </button>
          </div>
          <div className="border-t border-gray-200 pb-3 pt-4">
            <div className="flex items-center px-4">
              <div className="flex-shrink-0">
                <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                  <Users className="h-6 w-6 text-gray-500" />
                </div>
              </div>
              <div className="ml-3">
                <div className="text-base font-medium text-gray-800">
                  {typeof session?.user?.name === 'string' ? session.user.name : '講師'}
                </div>
                <div className="text-sm font-medium text-gray-500">
                  {typeof session?.user?.email === 'string' ? session.user.email : ''}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
} 
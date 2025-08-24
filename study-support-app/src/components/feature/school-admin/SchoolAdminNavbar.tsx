'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import {
  Users,
  GraduationCap,
  UserCheck,
  BarChart,
  Settings,
  Home,
  LogOut,
  Menu,
  X,
  School
} from 'lucide-react';
import { useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { TenantSelector, CurrentSchoolInfo } from '@/components/shared/TenantSelector';

export default function SchoolAdminNavbar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const { currentSchool, isSystemAdmin } = useTenant();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    {
      name: 'ダッシュボード',
      href: '/school-admin/dashboard',
      icon: <Home className="h-5 w-5" />
    },
    {
      name: 'ユーザー管理',
      href: '/school-admin/users',
      icon: <Users className="h-5 w-5" />
    },
    {
      name: '先生管理',
      href: '/school-admin/teachers',
      icon: <UserCheck className="h-5 w-5" />
    },
    {
      name: '生徒管理',
      href: '/school-admin/students',
      icon: <GraduationCap className="h-5 w-5" />
    },
    {
      name: '統計・分析',
      href: '/school-admin/analytics',
      icon: <BarChart className="h-5 w-5" />
    },
    {
      name: '学校設定',
      href: '/school-admin/settings',
      icon: <Settings className="h-5 w-5" />
    }
  ];

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleSignOut = async () => {
    await signOut({ redirect: true, callbackUrl: '/login' });
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          <div className="flex items-center">
            <div className="flex flex-shrink-0 items-center">
              <Link href="/school-admin/dashboard" className="flex items-center space-x-2">
                <School className="h-8 w-8 text-blue-600" />
                <div className="flex flex-col">
                  <span className="text-lg font-bold text-blue-600">School Admin</span>
                  {currentSchool && (
                    <span className="text-xs text-gray-500 hidden sm:block">
                      {currentSchool.name}
                    </span>
                  )}
                </div>
              </Link>
            </div>
            
            {/* システム管理者の場合は学校セレクターを表示 */}
            {isSystemAdmin && (
              <div className="ml-6 hidden md:block">
                <TenantSelector />
              </div>
            )}
          </div>

          {/* デスクトップメニュー */}
          <div className="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-4">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={`group inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  pathname === item.href
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
              >
                <span className="mr-2">{item.icon}</span>
                {item.name}
              </Link>
            ))}
          </div>

          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            <div className="flex items-center space-x-4">
              {!isSystemAdmin && (
                <CurrentSchoolInfo className="hidden lg:flex" />
              )}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-700">
                  {typeof session?.user?.name === 'string' ? session.user.name : '管理者'}
                </span>
                <button
                  onClick={handleSignOut}
                  className="rounded-md bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-500 hover:bg-gray-50 transition-colors"
                  title="ログアウト"
                >
                  <LogOut className="h-5 w-5" />
                </button>
              </div>
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
            {/* システム管理者用の学校セレクター（モバイル） */}
            {isSystemAdmin && (
              <div className="px-4 py-2 border-b border-gray-200">
                <TenantSelector />
              </div>
            )}
            
            {/* 現在の学校情報（モバイル） */}
            {!isSystemAdmin && (
              <div className="px-4 py-2 border-b border-gray-200">
                <CurrentSchoolInfo />
              </div>
            )}
            
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
                <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <School className="h-6 w-6 text-blue-600" />
                </div>
              </div>
              <div className="ml-3">
                <div className="text-base font-medium text-gray-800">
                  {typeof session?.user?.name === 'string' ? session.user.name : '管理者'}
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
"use client";

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Menu, 
  X, 
  Home,
  MessageSquare,
  FileText,
  User,
  Settings,
  SquarePlay,
  CircleHelp
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
}

const navigation: NavItem[] = [
  { name: 'ダッシュボード', href: '/dashboard', icon: Home },
  { name: 'AIチャット', href: '/chat', icon: MessageSquare },
  { name: 'FAQチャット', href: '/faq', icon: CircleHelp },
  { name: '志望校管理', href: '/application', icon: User },
  { name: '志望理由書', href: '/statement', icon: FileText },
  { name: 'コンテンツ', href: '/contents', icon: SquarePlay },
  { name: '設定', href: '/settings', icon: Settings },
];

export const AppLayout = ({ children }: { children: React.ReactNode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* モバイルサイドバートグル */}
      <div className="lg:hidden fixed top-4 left-4 z-40">
        <button
          className="p-2 rounded-md bg-white shadow-sm"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>

      {/* サイドバー */}
      <div className={`
        fixed top-0 left-0 z-30 h-full w-64 transform bg-white shadow-lg transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-slate-900">SmartAO</h1>
            <button
              className="lg:hidden p-2"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        <nav className="px-4 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`
                  flex items-center px-4 py-2 text-sm font-medium rounded-md
                  ${isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-700 hover:bg-slate-50'
                  }
                `}
              >
                <Icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* メインコンテンツ */}
      <main className="lg:pl-64">
        <div className="py-6 px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
};
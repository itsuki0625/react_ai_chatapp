"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { 
  Menu, 
  X, 
  Home,
  MessageSquare,
  FileText,
  User,
  Settings,
  SquarePlay,
  CircleHelp,
  BrainCircuit,
  GraduationCap,
  BookOpen,
  Users,
  Shield,
  DollarSign
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  children?: NavItem[];
  expanded?: boolean;
}

const studentNavigation: NavItem[] = [
  { name: 'ダッシュボード', href: '/dashboard', icon: Home },
  { 
    name: 'AIチャット', 
    href: '/chat', 
    icon: BrainCircuit,
    expanded: false,
    children: [
      { name: '自己分析AI', href: '/chat/self-analysis', icon: MessageSquare },
      { name: '総合型選抜AI', href: '/chat/admission', icon: GraduationCap },
      { name: '学習支援AI', href: '/chat/study-support', icon: BookOpen },
    ] 
  },
  { name: 'コミュニケーション', href: '/communication', icon: Users },
  { name: 'FAQチャット', href: '/faq', icon: CircleHelp },
  { name: '志望校管理', href: '/application', icon: User },
  { name: '志望理由書', href: '/statement', icon: FileText },
  { name: 'コンテンツ', href: '/contents', icon: SquarePlay },
  { name: '設定', href: '/settings', icon: Settings },
  { name: 'プラン', href: '/subscription/plans', icon: DollarSign },
];

const adminNavigation: NavItem[] = [
  { name: '管理ダッシュボード', href: '/admin/dashboard', icon: Home },
  { name: 'ユーザー管理', href: '/admin/users', icon: Users },
  { name: 'コンテンツ管理', href: '/admin/content', icon: SquarePlay },
  { name: 'サブスクリプション管理', href: '/admin/subscription', icon: DollarSign },
  { name: '設定', href: '/settings', icon: Settings },
];

export const AppLayout = ({ children }: { children: React.ReactNode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { data: session, status } = useSession();
  const [currentNavItems, setCurrentNavItems] = useState<NavItem[]>(studentNavigation);
  const pathname = usePathname();

  useEffect(() => {
    if (status === 'authenticated') {
      if (session?.user?.isAdmin) {
        setCurrentNavItems(adminNavigation);
      } else {
        setCurrentNavItems(studentNavigation);
      }
    } else if (status === 'unauthenticated') {
      setCurrentNavItems([]);
    }
  }, [session, status]);

  const [navItemsState, setNavItemsState] = useState<NavItem[]>([]);

  useEffect(() => {
    setNavItemsState(currentNavItems.map(item => ({ ...item, expanded: item.expanded ?? false })));
  }, [currentNavItems]);

  const toggleExpand = (index: number) => {
    setNavItemsState(prevItems => 
      prevItems.map((item, i) => 
        i === index ? { ...item, expanded: !item.expanded } : item
      )
    );
  };

  if (status === 'loading') {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="lg:hidden fixed top-4 left-4 z-40">
        <button
          className="p-2 rounded-md bg-white shadow-sm"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>

      <div className={`
        fixed top-0 left-0 z-30 h-full w-64 transform bg-white shadow-lg transition-transform duration-200 ease-in-out overflow-y-auto
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
          {navItemsState.map((item, index) => {
            const isActive = pathname === item.href || 
                           (item.children && item.children.some(child => pathname?.startsWith(child.href)));
            const Icon = item.icon;
            
            return (
              <div key={item.name}>
                {item.children ? (
                  <>
                    <button
                      onClick={() => toggleExpand(index)}
                      className={`
                        w-full flex items-center justify-between px-4 py-2 text-sm font-medium rounded-md
                        ${isActive
                          ? 'bg-blue-50 text-blue-700'
                          : 'text-slate-700 hover:bg-slate-50'
                        }
                      `}
                    >
                      <div className="flex items-center">
                        <Icon className="mr-3 h-5 w-5" />
                        {item.name}
                      </div>
                      <svg
                        className={`w-5 h-5 transform transition-transform ${item.expanded ? 'rotate-90' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                    
                    <div 
                      className={`overflow-hidden transition-all duration-300 ease-in-out ${item.expanded ? 'max-h-96' : 'max-h-0'}`}
                    >
                      <div className="pl-8 mt-1 space-y-1 py-1">
                        {item.children.map(child => {
                          const isChildActive = pathname === child.href;
                          const ChildIcon = child.icon;
                          
                          return (
                            <Link
                              key={child.name}
                              href={child.href}
                              onClick={() => setSidebarOpen(false)}
                              className={`
                                flex items-center px-4 py-2 text-sm font-medium rounded-md
                                ${isChildActive
                                  ? 'bg-blue-50 text-blue-700'
                                  : 'text-slate-700 hover:bg-slate-50'
                                }
                              `}
                            >
                              <ChildIcon className="mr-3 h-4 w-4" />
                              {child.name}
                            </Link>
                          );
                        })}
                      </div>
                    </div>
                  </>
                ) : (
                  <Link
                    href={item.href}
                    onClick={() => setSidebarOpen(false)}
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
                )}
              </div>
            );
          })}
        </nav>
      </div>

      <main className="lg:pl-64">
        <div className="py-6 px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
};
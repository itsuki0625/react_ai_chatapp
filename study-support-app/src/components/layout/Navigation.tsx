import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import {
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
  DollarSign,
  Bell
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

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
      { name: 'FAQチャット', href: '/chat/faq', icon: CircleHelp },
    ] 
  },
  { name: 'コミュニケーション', href: '/communication', icon: Users },
  { name: '志望校管理', href: '/application', icon: User },
  { name: '志望理由書', href: '/statement', icon: FileText },
  { name: 'コンテンツ', href: '/contents', icon: SquarePlay },
  { name: '設定', href: '/settings', icon: Settings },
  { name: 'プラン', href: '/subscription', icon: DollarSign },
];

const adminNavigation: NavItem[] = [
  { name: '管理ダッシュボード', href: '/admin/dashboard', icon: Home },
  { name: 'ユーザー管理', href: '/admin/users', icon: Users },
  { name: 'コンテンツ管理', href: '/admin/content', icon: SquarePlay },
  { name: 'サブスクリプション管理', href: '/admin/subscription', icon: DollarSign },
  { name: '設定', href: '/settings', icon: Settings },
];

export const Navigation = () => {
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

  // 未読通知数の取得
  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => {
      const response = await apiClient.get('/in-app-notifications');
      return response.data;
    },
  });

  const unreadCount = notifications?.filter((n: any) => !n.is_read).length || 0;

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <Link
            href="/notifications"
            className="relative p-2 hover:bg-muted rounded-full transition-colors"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-primary text-primary-foreground text-xs rounded-full flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </Link>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-1">
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
  );
}; 
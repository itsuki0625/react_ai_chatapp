import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
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
  Bell,
  Lock
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Badge } from '@/components/ui/badge';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  children?: NavItem[];
  expanded?: boolean;
  requiresPaid?: boolean; // 有料プラン限定機能かどうか
  requiresPremium?: boolean; // プレミアムプラン限定機能かどうか
  disabled?: boolean;
}

// フリーユーザー向けナビゲーション
const freeUserNavigation: NavItem[] = [
  { name: 'ダッシュボード', href: '/dashboard', icon: Home },
  {
    name: 'AIチャット',
    href: '/chat',
    icon: BrainCircuit,
    expanded: false,
    requiresPaid: true,
    disabled: true,
    children: [
      { name: '自己分析AI', href: '/chat/self-analysis', icon: MessageSquare, requiresPaid: true, disabled: true },
      { name: '総合型選抜AI', href: '/chat/admission', icon: GraduationCap, requiresPaid: true, disabled: true },
      { name: '学習支援AI', href: '/chat/study-support', icon: BookOpen, requiresPaid: true, disabled: true },
      { name: 'FAQチャット', href: '/chat/faq', icon: CircleHelp, requiresPaid: true, disabled: true },
    ] 
  },
  { name: 'コミュニケーション', href: '/communication', icon: Users, requiresPaid: true },
  { name: '志望校管理', href: '/application', icon: User },
  { name: '志望理由書', href: '/statement', icon: FileText, requiresPaid: true },
  { name: 'コンテンツ', href: '/contents', icon: SquarePlay, requiresPaid: true },
  { name: '設定', href: '/settings', icon: Settings },
  { name: 'プラン', href: '/subscription', icon: DollarSign },
];

// 有料ユーザー向けナビゲーション
const paidUserNavigation: NavItem[] = [
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

// 簡易的な通知型を定義
interface MinimalNotification {
  id: string;
  is_read: boolean; // バックエンドの is_read に合わせる (または read)
  // 他に必要なプロパティがあれば追加
}

export const Navigation = () => {
  const { data: session, status } = useSession();
  const [currentNavItems, setCurrentNavItems] = useState<NavItem[]>([]);
  const pathname = usePathname();
  const router = useRouter();

  // ユーザーのプラン判定
  const isAdmin = session?.user?.isAdmin;
  const userRole = session?.user?.role;
  const isFreeUser = userRole === 'フリー';
  const isPaidUser = userRole === 'スタンダード' || userRole === 'プレミアム';
  const isPremiumUser = userRole === 'プレミアム';

  useEffect(() => {
    if (status === 'authenticated') {
      if (isAdmin) {
        setCurrentNavItems(adminNavigation);
      } else if (isPaidUser) {
        setCurrentNavItems(paidUserNavigation);
      } else {
        // スタンダード・プレミアム以外はフリー扱い
        setCurrentNavItems(freeUserNavigation);
      }
    } else if (status === 'unauthenticated') {
      setCurrentNavItems([]);
    }
  }, [session, status, isAdmin, isFreeUser, isPaidUser, isPremiumUser]);

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

  const { data: notificationsData } = useQuery<{
    unread: number;
  }>({
    queryKey: ['notificationsCount'], // クエリキーを NotificationHistory と区別
    queryFn: async () => {
      if (status !== 'authenticated') return { unread: 0 };
      try {
        const response = await apiClient.get('/api/v1/in-app-notifications/');
        const notifications = response.data as MinimalNotification[];
        const unread = notifications.filter(n => !n.is_read).length;
        return { unread };
      } catch (error) {
        console.error('Error fetching notifications count:', error);
        return { unread: 0 }; // エラー時は0件とする
      }
    },
    enabled: status === 'authenticated', // 認証済みの場合のみ実行
    staleTime: 5 * 60 * 1000, // 5分間はキャッシュを有効にする
  });

  const unreadCount = notificationsData?.unread || 0;

  // 制限されたアイテムのクリックハンドラー
  const handleRestrictedClick = (e: React.MouseEvent, item: NavItem) => {
    if ((item.requiresPaid && !isPaidUser && !isAdmin) || 
        (item.requiresPremium && !isPremiumUser && !isAdmin)) {
      e.preventDefault();
      router.push('/subscription');
    }
  };

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
          const isRestricted = (item.requiresPaid && !isPaidUser && !isAdmin) || 
                             (item.requiresPremium && !isPremiumUser && !isAdmin);

          return (
            <div key={item.name}>
              {item.children ? (
                <>
                  <button
                    onClick={() => {
                      if (isRestricted) {
                        router.push('/subscription');
                      } else {
                        toggleExpand(index);
                      }
                    }}
                    className={`
                      w-full flex items-center justify-between px-4 py-2 text-sm font-medium rounded-md
                      ${isActive && !isRestricted
                        ? 'bg-blue-50 text-blue-700'
                        : isRestricted
                        ? 'text-slate-400 hover:bg-slate-50 cursor-pointer'
                        : 'text-slate-700 hover:bg-slate-50'
                      }
                    `}
                  >
                    <div className="flex items-center">
                      <Icon className={`mr-3 h-5 w-5 ${isRestricted ? 'text-slate-400' : ''}`} />
                      {item.name}
                      {isRestricted && (
                        <div className="ml-2 flex items-center gap-1">
                          <Lock className="h-3 w-3 text-slate-400" />
                          <Badge variant="outline" className="text-xs px-1 py-0">
                            {item.requiresPremium ? 'プレミアム' : '有料'}
                          </Badge>
                        </div>
                      )}
                    </div>
                    <svg
                      className={`w-5 h-5 transform transition-transform ${item.expanded ? 'rotate-90' : ''} ${isRestricted ? 'text-slate-400' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>

                  <div
                    className={`overflow-hidden transition-all duration-300 ease-in-out ${item.expanded && !isRestricted ? 'max-h-96' : 'max-h-0'}`}
                  >
                    <div className="pl-8 mt-1 space-y-1 py-1">
                      {item.children.map(child => {
                        const isChildActive = pathname === child.href;
                        const ChildIcon = child.icon;
                        const isChildRestricted = (child.requiresPaid && !isPaidUser && !isAdmin) || 
                                                 (child.requiresPremium && !isPremiumUser && !isAdmin);

                        return (
                          <Link
                            key={child.name}
                            href={isChildRestricted ? '/subscription' : child.href}
                            onClick={(e) => handleRestrictedClick(e, child)}
                            className={`
                              flex items-center px-4 py-2 text-sm font-medium rounded-md
                              ${isChildActive && !isChildRestricted
                                ? 'bg-blue-50 text-blue-700'
                                : isChildRestricted
                                ? 'text-slate-400 hover:bg-slate-50'
                                : 'text-slate-700 hover:bg-slate-50'
                              }
                            `}
                          >
                            <ChildIcon className={`mr-3 h-4 w-4 ${isChildRestricted ? 'text-slate-400' : ''}`} />
                            {child.name}
                            {isChildRestricted && (
                              <div className="ml-auto flex items-center">
                                <Lock className="h-3 w-3 text-slate-400" />
                              </div>
                            )}
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                </>
              ) : (
                <Link
                  href={isRestricted ? '/subscription' : item.href}
                  onClick={(e) => handleRestrictedClick(e, item)}
                  className={`
                    flex items-center px-4 py-2 text-sm font-medium rounded-md
                    ${isActive && !isRestricted
                      ? 'bg-blue-50 text-blue-700'
                      : isRestricted
                      ? 'text-slate-400 hover:bg-slate-50'
                      : 'text-slate-700 hover:bg-slate-50'
                    }
                  `}
                >
                  <Icon className={`mr-3 h-5 w-5 ${isRestricted ? 'text-slate-400' : ''}`} />
                  {item.name}
                  {isRestricted && (
                    <div className="ml-auto flex items-center gap-1">
                      <Lock className="h-3 w-3 text-slate-400" />
                      <Badge variant="outline" className="text-xs px-1 py-0">
                        有料
                      </Badge>
                    </div>
                  )}
                </Link>
              )}
            </div>
          );
        })}
      </nav>

      {/* フリーユーザー向けプラン案内 */}
      {!isPaidUser && !isAdmin && (
        <div className="p-4 border-t border-gray-200">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Lock className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">フリープラン</span>
            </div>
            <p className="text-xs text-blue-700 mb-2">
              AIチャットや志望校管理などの機能をご利用いただくには、有料プランへのアップグレードが必要です。
            </p>
            <Link href="/subscription">
              <button className="w-full bg-blue-600 text-white text-xs py-1.5 px-3 rounded-md hover:bg-blue-700 transition-colors">
                プランを確認する
              </button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}; 
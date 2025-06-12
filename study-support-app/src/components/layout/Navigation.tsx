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
  Lock,
  CreditCard
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
  { name: '決済履歴', href: '/subscription/history', icon: CreditCard },
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
  { name: '決済履歴', href: '/subscription/history', icon: CreditCard },
];

const adminNavigation: NavItem[] = [
  { name: '管理ダッシュボード', href: '/admin/dashboard', icon: Home },
  { name: 'ユーザー管理', href: '/admin/users', icon: Users },
  { name: 'コンテンツ管理', href: '/admin/content', icon: SquarePlay },
  { name: 'サブスクリプション管理', href: '/admin/subscription', icon: DollarSign },
  { name: '決済監視', href: '/admin/payments', icon: CreditCard },
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
  const [isMobile, setIsMobile] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  // ユーザーの権限判定（完全に権限ベース）
  const isAdmin = session?.user?.isAdmin;
  const userPermissions = session?.user?.permissions || [];
  
  // 権限ベースで機能利用可否を判定
  const canUseCommunication = userPermissions.includes('communication_read') || userPermissions.includes('communication_write');
  const canUseChat = userPermissions.includes('chat_session_read') || userPermissions.includes('chat_message_send');
  const canUseStatement = userPermissions.includes('statement_review_request') || userPermissions.includes('statement_manage_own');
  const canUseContent = userPermissions.includes('content_read');
  const canUseDesiredSchool = userPermissions.includes('desired_school_manage_own') || userPermissions.includes('application_read');
  
  // 表示用の判定（後方互換性のため）
  const isPaidUser = canUseCommunication || canUseChat || canUseStatement;
  const isPremiumUser = userPermissions.includes('statement_review_request');

  useEffect(() => {
    if (status === 'authenticated') {
      if (isAdmin) {
        setCurrentNavItems(adminNavigation);
      } else if (isPaidUser) {
        setCurrentNavItems(paidUserNavigation);
      } else {
        // 有料プラン権限がない場合はフリー扱い
        setCurrentNavItems(freeUserNavigation);
      }
    } else if (status === 'unauthenticated') {
      setCurrentNavItems([]);
    }
  }, [session, status, isAdmin, isPaidUser, isPremiumUser, userPermissions]);

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
    if (!isAdmin) {
      let restricted = false;
      if (item.href === '/communication' && !canUseCommunication) restricted = true;
      else if (item.href === '/chat' && !canUseChat) restricted = true;
      else if (item.href === '/statement' && !canUseStatement) restricted = true;
      else if (item.href === '/contents' && !canUseContent) restricted = true;
      else if (item.href === '/application' && !canUseDesiredSchool) restricted = true;
      else if (item.requiresPaid && !isPaidUser) restricted = true;
      else if (item.requiresPremium && !isPremiumUser) restricted = true;
      
      if (restricted) {
        e.preventDefault();
        router.push('/subscription');
      }
    }
  };

  if (status === 'loading') {
    return <div className="flex items-center justify-center p-4">Loading...</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className={`flex items-center justify-between ${isMobile ? 'p-3' : 'p-4'}`}>
        <div className="flex items-center gap-2">
          <Link
            href="/notifications"
            className={`relative p-2 hover:bg-muted rounded-full transition-colors ${isMobile ? 'p-3' : ''}`}
          >
            <Bell className={`${isMobile ? 'w-6 h-6' : 'w-5 h-5'}`} />
            {unreadCount > 0 && (
              <span className={`absolute -top-1 -right-1 bg-primary text-primary-foreground text-xs rounded-full flex items-center justify-center ${isMobile ? 'w-5 h-5 text-sm' : 'w-4 h-4'}`}>
                {unreadCount}
              </span>
            )}
          </Link>
        </div>
      </div>

      <nav className={`flex-1 space-y-1 ${isMobile ? 'px-2' : 'px-4'}`}>
        {navItemsState.map((item, index) => {
          const isActive = pathname === item.href ||
                         (item.children && item.children.some(child => pathname?.startsWith(child.href)));
          const Icon = item.icon;
          
          // 権限ベースで制限判定
          let isRestricted = false;
          if (!isAdmin) {
            if (item.href === '/communication' && !canUseCommunication) isRestricted = true;
            else if (item.href === '/chat' && !canUseChat) isRestricted = true;
            else if (item.href === '/statement' && !canUseStatement) isRestricted = true;
            else if (item.href === '/contents' && !canUseContent) isRestricted = true;
            else if (item.href === '/application' && !canUseDesiredSchool) isRestricted = true;
            else if (item.requiresPaid && !isPaidUser) isRestricted = true;
            else if (item.requiresPremium && !isPremiumUser) isRestricted = true;
          }

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
                      w-full flex items-center justify-between font-medium rounded-md
                      ${isMobile ? 'px-3 py-3 text-base' : 'px-4 py-2 text-sm'}
                      ${isActive && !isRestricted
                        ? 'bg-blue-50 text-blue-700'
                        : isRestricted
                        ? 'text-slate-400 hover:bg-slate-50 cursor-pointer'
                        : 'text-slate-700 hover:bg-slate-50'
                      }
                    `}
                  >
                    <div className="flex items-center min-w-0 flex-1">
                      <Icon className={`flex-shrink-0 ${isMobile ? 'mr-4 h-6 w-6' : 'mr-3 h-5 w-5'} ${isRestricted ? 'text-slate-400' : ''}`} />
                      <span className={`truncate ${isMobile ? '' : ''}`}>{item.name}</span>
                      {isRestricted && (
                        <div className="ml-2 flex items-center gap-1 flex-shrink-0">
                          <Lock className={`text-slate-400 ${isMobile ? 'h-4 w-4' : 'h-3 w-3'}`} />
                          <Badge variant="outline" className={`px-1 py-0 ${isMobile ? 'text-xs' : 'text-xs'}`}>
                            {item.requiresPremium ? 'プレミアム' : '有料'}
                          </Badge>
                        </div>
                      )}
                    </div>
                    <svg
                      className={`transform transition-transform flex-shrink-0 ${item.expanded ? 'rotate-90' : ''} ${isRestricted ? 'text-slate-400' : ''} ${isMobile ? 'w-6 h-6' : 'w-5 h-5'}`}
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
                    <div className={`mt-1 space-y-1 py-1 ${isMobile ? 'pl-6' : 'pl-8'}`}>
                      {item.children.map(child => {
                        const isChildActive = pathname === child.href;
                        const ChildIcon = child.icon;
                        
                        // 子アイテムの権限ベース制限判定
                        let isChildRestricted = false;
                        if (!isAdmin) {
                          if (child.href.startsWith('/chat') && !canUseChat) isChildRestricted = true;
                          else if (child.requiresPaid && !isPaidUser) isChildRestricted = true;
                          else if (child.requiresPremium && !isPremiumUser) isChildRestricted = true;
                        }

                        return (
                          <Link
                            key={child.name}
                            href={isChildRestricted ? '/subscription' : child.href}
                            onClick={(e) => handleRestrictedClick(e, child)}
                            className={`
                              flex items-center font-medium rounded-md
                              ${isMobile ? 'px-3 py-3 text-base' : 'px-4 py-2 text-sm'}
                              ${isChildActive && !isChildRestricted
                                ? 'bg-blue-50 text-blue-700'
                                : isChildRestricted
                                ? 'text-slate-400 hover:bg-slate-50'
                                : 'text-slate-700 hover:bg-slate-50'
                              }
                            `}
                          >
                            <ChildIcon className={`flex-shrink-0 ${isMobile ? 'mr-4 h-5 w-5' : 'mr-3 h-4 w-4'} ${isChildRestricted ? 'text-slate-400' : ''}`} />
                            <span className="truncate flex-1">{child.name}</span>
                            {isChildRestricted && (
                              <div className="ml-auto flex items-center flex-shrink-0">
                                <Lock className={`text-slate-400 ${isMobile ? 'h-4 w-4' : 'h-3 w-3'}`} />
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
                    flex items-center font-medium rounded-md
                    ${isMobile ? 'px-3 py-3 text-base' : 'px-4 py-2 text-sm'}
                    ${isActive && !isRestricted
                      ? 'bg-blue-50 text-blue-700'
                      : isRestricted
                      ? 'text-slate-400 hover:bg-slate-50'
                      : 'text-slate-700 hover:bg-slate-50'
                    }
                  `}
                >
                  <Icon className={`flex-shrink-0 ${isMobile ? 'mr-4 h-6 w-6' : 'mr-3 h-5 w-5'} ${isRestricted ? 'text-slate-400' : ''}`} />
                  <span className="truncate flex-1">{item.name}</span>
                  {isRestricted && (
                    <div className="ml-auto flex items-center gap-1 flex-shrink-0">
                      <Lock className={`text-slate-400 ${isMobile ? 'h-4 w-4' : 'h-3 w-3'}`} />
                      <Badge variant="outline" className={`px-1 py-0 ${isMobile ? 'text-xs' : 'text-xs'}`}>
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
        <div className={`border-t border-gray-200 ${isMobile ? 'p-3' : 'p-4'}`}>
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Lock className={`text-blue-600 ${isMobile ? 'h-5 w-5' : 'h-4 w-4'}`} />
              <span className={`font-medium text-blue-800 ${isMobile ? 'text-base' : 'text-sm'}`}>フリープラン</span>
            </div>
            <p className={`text-blue-700 mb-2 ${isMobile ? 'text-sm' : 'text-xs'}`}>
              AIチャットや志望校管理などの機能をご利用いただくには、有料プランへのアップグレードが必要です。
            </p>
            <Link href="/subscription">
              <button className={`w-full bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors ${isMobile ? 'text-sm py-2 px-3' : 'text-xs py-1.5 px-3'}`}>
                プランを確認する
              </button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}; 
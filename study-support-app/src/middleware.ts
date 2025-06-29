import { auth } from '@/auth';
import { NextResponse } from 'next/server';
import { hasRoutePermission, getPermissionRedirectUrl } from '@/lib/permissions';

// NextAuthのミドルウェアをエクスポート
export default auth((req) => {
  const { nextUrl, auth: authObj } = req;
  const { pathname, searchParams } = nextUrl;
  const isLoggedIn = !!authObj?.user;
  const userStatus = authObj?.user?.status;
  const isAdmin = authObj?.user?.isAdmin;
  const isTeacher = authObj?.user?.isTeacher;
  const userPermissions: string[] = authObj?.user?.permissions || [];
  const isLoggedOut = searchParams.get('status') === 'logged_out';

  console.log(`[Middleware] Path: ${pathname}, IsLoggedIn: ${isLoggedIn}, Status: ${userStatus}, IsAdmin: ${isAdmin}, IsTeacher: ${isTeacher}, Permissions: ${userPermissions.join(', ')}`);

  // --- RefreshAccessTokenError の処理を改善 ---
  if (authObj?.error === "RefreshAccessTokenError") {
    console.log(`[Middleware] RefreshAccessTokenError detected on path: ${pathname}.`);

    let response;
    const loginUrl = new URL('/login?error=session_expired', nextUrl.origin);

    // ログインページにいるかどうかで処理を分岐
    if (nextUrl.pathname === '/login') {
      console.log('[Middleware] Already on login page, not redirecting again.');
      // ログインページへのリクエストは許可
      response = NextResponse.next();
    } else {
      console.log('[Middleware] Not on login page, redirecting.');
      // ログインページにリダイレクト
      response = NextResponse.redirect(loginUrl);
    }

    // NextAuthのセッションCookieを削除
    const cookiesToDelete = [
      'next-auth.session-token',
      '__Secure-next-auth.session-token', 
      'next-auth.csrf-token',
      '__Host-next-auth.csrf-token'
    ];
    
    cookiesToDelete.forEach(cookieName => {
      response.cookies.delete({
        name: cookieName,
        path: '/',
      });
    });
    
    return response;
  }

  // --- アクセス制御対象ルートの定義 ---
  const protectedRoutes = [
    '/student/dashboard',
    '/student/settings',
    '/admin',
    '/student/contents',
    '/student/chat',
    '/student/faq',
    '/student/statement',
    '/student/application',
    '/student/subscription'
  ];
  
  const subscriptionRequiredRoutes = ['/student/contents', '/student/chat', '/student/faq', '/student/statement'];

  const isAdminRoute = pathname.startsWith('/admin');
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  const isSubscriptionRequiredRoute = subscriptionRequiredRoutes.some(route => pathname.startsWith(route));
  const isStatusPageRoute = pathname === '/pending-activation' || pathname === '/payment-required' || pathname === '/inactive-account';
  const isAuthPage = pathname === '/login' || pathname === '/signup';

  // --- 1. 未認証ユーザーの処理 ---
  if (!isLoggedIn && isProtectedRoute) {
    console.log(`[Middleware] Unauthenticated user accessing protected route ${pathname}. Redirecting to login.`);
    const redirectUrl = new URL('/login', nextUrl.origin);
    redirectUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // --- 2. 認証済みユーザーの処理 ---
  if (isLoggedIn) {
    // 2a. 古いダッシュボードパスのリダイレクト
    if (pathname === '/dashboard' || pathname === '/chat' || pathname === '/settings' || pathname === '/contents' || pathname === '/application' || pathname === '/statement' || pathname === '/subscription') {
      const newPath = `/student${pathname}`;
      console.log(`[Middleware] Redirecting old path ${pathname} to new path ${newPath}`);
      return NextResponse.redirect(new URL(newPath, nextUrl.origin));
    }

    // 2b. ステータスページへのアクセスは常に許可
    if (isStatusPageRoute) {
      console.log(`[Middleware] Allowing access to status page: ${pathname}`);
      return NextResponse.next();
    }

    // 2c. アカウントステータスに基づくリダイレクト
    if (userStatus === 'pending' && !isStatusPageRoute) {
      console.log(`[Middleware] Pending user accessing non-status page ${pathname}. Redirecting to /pending-activation.`);
      return NextResponse.redirect(new URL('/pending-activation', nextUrl.origin));
    }
    
    if (userStatus === 'inactive' && !isStatusPageRoute) {
      console.log(`[Middleware] Inactive user accessing non-status page ${pathname}. Redirecting to /inactive-account.`);
      return NextResponse.redirect(new URL('/inactive-account', nextUrl.origin));
    }

    // 2d. 権限ベースのアクセス制御
    if (isSubscriptionRequiredRoute && pathname) {
      const hasPermission = hasRoutePermission(pathname, userPermissions, isAdmin, isTeacher);
      
      if (!hasPermission) {
        const redirectUrl = getPermissionRedirectUrl(pathname, userStatus || 'inactive');
        console.log(`[Middleware] User lacks permission for route ${pathname}. Permissions: [${userPermissions.join(', ')}]. Redirecting to ${redirectUrl}.`);
        return NextResponse.redirect(new URL(redirectUrl, nextUrl.origin));
      }
      
      console.log(`[Middleware] User has permission for route ${pathname}. Permissions: [${userPermissions.join(', ')}].`);
    }

    // 2e. 管理者関連のチェック
    if (isAdminRoute && !isAdmin) {
      console.log(`[Middleware] Non-admin access to /admin. Redirecting to student dashboard.`);
      return NextResponse.redirect(new URL('/student/dashboard', nextUrl.origin));
    }
    
    if (isAdmin && !isAdminRoute && !isAuthPage && !isStatusPageRoute) {
      console.log(`[Middleware] Admin user accessing non-admin path ${pathname}. Redirecting to /admin/dashboard.`);
      return NextResponse.redirect(new URL('/admin/dashboard', nextUrl.origin));
    }

    // 2f. 認証済みユーザーがログイン/サインアップページにアクセスした場合
    if (isAuthPage) {
      // ログアウト直後またはセッションエラー時はログインページへのアクセスを許可
      if (pathname === '/login' && (isLoggedOut || searchParams.get('error') === 'session_expired')) {
        console.log(`[Middleware] Allowing access to /login after logout or session error.`);
        return NextResponse.next();
      }
      
      const redirectUrl = isAdmin ? '/admin/dashboard' : '/student/dashboard';
      console.log(`[Middleware] Authenticated user accessing auth page ${pathname}. Redirecting to ${redirectUrl}.`);
      return NextResponse.redirect(new URL(redirectUrl, nextUrl.origin));
    }

    // 上記のどのリダイレクト条件にも当てはまらない場合はアクセスを許可
    console.log(`[Middleware] Allowing request for logged-in user to ${pathname}`);
    return NextResponse.next();
  }

  // --- 3. 未認証ユーザーが保護されていないルートにアクセス ---
  console.log(`[Middleware] Allowing request for unauthenticated user to non-protected route ${pathname}`);
  return NextResponse.next();
});

// ミドルウェアを適用するパスを設定
export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
};
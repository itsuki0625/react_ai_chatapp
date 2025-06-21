import { auth } from '@/auth';
import { NextResponse } from 'next/server';

// NextAuthのミドルウェアをエクスポート
export default auth((req) => {
  const { nextUrl, auth: authObj } = req;
  const { pathname, searchParams } = nextUrl;
  const isLoggedIn = !!authObj?.user;
  const userStatus = authObj?.user?.status;
  const isAdmin = authObj?.user?.isAdmin;
  const isLoggedOut = searchParams.get('status') === 'logged_out';

  console.log(`[Middleware] Path: ${pathname}, IsLoggedIn: ${isLoggedIn}, Status: ${userStatus}, IsAdmin: ${isAdmin}`);

  // --- RefreshAccessTokenError の処理を改善 ---
  if (authObj?.error === "RefreshAccessTokenError") {
    console.log(`[Middleware] RefreshAccessTokenError detected. Redirecting to login with session_expired.`);
    
    // 既にログインページで session_expired エラーパラメータがある場合は、無限ループを防ぐ
    if (pathname === '/login' && searchParams.get('error') === 'session_expired') {
      console.log('[Middleware] Already on login page with session_expired, allowing through');
      return NextResponse.next();
    }
    
    // セッションCookieをクリアしてログインページにリダイレクト
    const response = NextResponse.redirect(new URL('/login?error=session_expired', nextUrl.origin));
    
    // NextAuthのセッションCookieを削除
    const cookiesToDelete = [
      'next-auth.session-token',
      '__Secure-next-auth.session-token', 
      'next-auth.csrf-token',
      '__Host-next-auth.csrf-token'
    ];
    
    cookiesToDelete.forEach(cookieName => {
      response.cookies.delete(cookieName);
    });
    
    return response;
  }

  // --- アクセス制御対象ルートの定義 ---
  const protectedRoutes = [
    '/dashboard',
    '/settings',
    '/admin',
    '/contents',
    '/chat',
    '/faq',
    '/statement',
    '/application',
    '/subscription'
  ];
  
  const subscriptionRequiredRoutes = ['/contents', '/chat', '/faq', '/statement'];

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
    // 2a. ステータスページへのアクセスは常に許可
    if (isStatusPageRoute) {
      console.log(`[Middleware] Allowing access to status page: ${pathname}`);
      return NextResponse.next();
    }

    // 2b. アカウントステータスに基づくリダイレクト
    if (userStatus === 'pending' && !isStatusPageRoute) {
      console.log(`[Middleware] Pending user accessing non-status page ${pathname}. Redirecting to /pending-activation.`);
      return NextResponse.redirect(new URL('/pending-activation', nextUrl.origin));
    }
    
    if (userStatus === 'inactive' && !isStatusPageRoute) {
      console.log(`[Middleware] Inactive user accessing non-status page ${pathname}. Redirecting to /inactive-account.`);
      return NextResponse.redirect(new URL('/inactive-account', nextUrl.origin));
    }

    // 2c. サブスクリプション必須ルートのチェック
    if (isSubscriptionRequiredRoute && userStatus !== 'active') {
      console.log(`[Middleware] Non-active user (status: ${userStatus}) accessing subscription required route ${pathname}. Redirecting to /subscription/plans.`);
      return NextResponse.redirect(new URL('/subscription/plans', nextUrl.origin));
    }

    // 2d. 管理者関連のチェック
    if (isAdminRoute && !isAdmin) {
      console.log(`[Middleware] Non-admin access to /admin. Redirecting to dashboard.`);
      return NextResponse.redirect(new URL('/dashboard', nextUrl.origin));
    }
    
    if (isAdmin && !isAdminRoute && !isAuthPage && !isStatusPageRoute) {
      console.log(`[Middleware] Admin user accessing non-admin path ${pathname}. Redirecting to /admin/dashboard.`);
      return NextResponse.redirect(new URL('/admin/dashboard', nextUrl.origin));
    }

    // 2e. 認証済みユーザーがログイン/サインアップページにアクセスした場合
    if (isAuthPage) {
      // ログアウト直後またはセッションエラー時はログインページへのアクセスを許可
      if (pathname === '/login' && (isLoggedOut || searchParams.get('error') === 'session_expired')) {
        console.log(`[Middleware] Allowing access to /login after logout or session error.`);
        return NextResponse.next();
      }
      
      const redirectUrl = isAdmin ? '/admin/dashboard' : '/dashboard';
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
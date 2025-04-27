import { auth } from '@/auth';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// NextAuthのミドルウェアをエクスポート
export default auth((req) => {
  // auth コールバックが認証をチェックした後に実行されるミドルウェア
  const { nextUrl, auth: authObj } = req;
  const { pathname } = nextUrl;
  const isLoggedIn = !!authObj?.user;
  const userStatus = authObj?.user?.status;
  const isAdmin = authObj?.user?.isAdmin;

  console.log(`[Middleware] Path: ${pathname}, Auth Status: ${isLoggedIn}, Status: ${userStatus}, IsAdmin: ${isAdmin}, User: ${JSON.stringify(authObj?.user)}, Error: ${authObj?.error}`); // DEBUG LOG

  // 保護されたルートの定義
  const protectedRoutes = ['/dashboard', '/settings', '/admin'];
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  const isStatusPageRoute = pathname === '/pending-activation' || pathname === '/payment-required' || pathname === '/inactive-account';

  // 未認証で保護されたルートにアクセスしようとした場合
  if (!isLoggedIn && isProtectedRoute) {
    console.log(`[Middleware] Not authenticated for protected route ${pathname}. Redirecting to login.`);
    const redirectUrl = new URL('/login', nextUrl.origin);
    redirectUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // 認証済みユーザーのステータスチェック
  if (isLoggedIn && !isStatusPageRoute) { // ステータスページ自体へのアクセスはチェック対象外
    if (userStatus === 'pending') {
      console.log(`[Middleware] Pending user accessing ${pathname}. Redirecting to /pending-activation.`);
      return NextResponse.redirect(new URL('/pending-activation', nextUrl.origin));
    }
    if (userStatus === 'unpaid') {
      console.log(`[Middleware] Unpaid user accessing ${pathname}. Redirecting to /payment-required.`);
      return NextResponse.redirect(new URL('/payment-required', nextUrl.origin));
    }
    if (userStatus === 'inactive') {
      console.log(`[Middleware] Inactive user accessing ${pathname}. Redirecting to /inactive-account.`);
      return NextResponse.redirect(new URL('/inactive-account', nextUrl.origin));
    }
  }

  // --- 以降のチェックは、アクティブユーザー (またはステータスページへのアクセス) のみが対象 ---

  // JWT認証エラー
  if (authObj?.error === "RefreshAccessTokenError") {
    console.log(`[Middleware] RefreshAccessTokenError detected. Redirecting to login.`);
    const redirectUrl = new URL('/login', nextUrl.origin);
    redirectUrl.searchParams.set('error', 'session_expired');
    return NextResponse.redirect(redirectUrl);
  }

  // 管理者パスへのアクセスチェック (アクティブユーザーのみ)
  if (isLoggedIn && userStatus === 'active' && pathname.startsWith('/admin')) {
    if (!isAdmin) {
      console.log(`[Middleware] Non-admin access to /admin. Redirecting to dashboard.`);
      return NextResponse.redirect(new URL('/dashboard', nextUrl.origin));
    }
  }

  // ログイン済みアクティブユーザーが認証ページへアクセス
  if (isLoggedIn && userStatus === 'active' && (pathname === '/login' || pathname === '/signup')) {
    const redirectUrl = isAdmin ? '/admin/dashboard' : '/dashboard';
    console.log(`[Middleware] Authenticated active user accessing auth page ${pathname}. Redirecting to ${redirectUrl}.`);
    return NextResponse.redirect(new URL(redirectUrl, nextUrl.origin));
  }

  // ログイン済みアクティブ管理者が /admin 以外のページへアクセス
  if (isLoggedIn && userStatus === 'active' && isAdmin && !pathname.startsWith('/admin') && !isStatusPageRoute && pathname !== '/login' && pathname !== '/signup') {
      console.log(`[Middleware] Admin user accessing non-admin path ${pathname}. Redirecting to /admin/dashboard.`);
      return NextResponse.redirect(new URL('/admin/dashboard', nextUrl.origin));
  }

  console.log(`[Middleware] Allowing request to ${pathname}`);
  return NextResponse.next();
});

// ミドルウェアを適用するパスを設定
export const config = {
  matcher: [
    /*
     * / (ホームページ)と/api、public、_nextのような静的ファイルへのリクエストをスキップ
     * ただし、/login, /signup, /dashboard, /settings, /adminのパスにはマッチさせる
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
};
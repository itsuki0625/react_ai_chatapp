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

  // ログを強化
  console.log(`[Middleware Start] Path: ${pathname}, IsLoggedIn: ${isLoggedIn}, Status: ${userStatus}, IsAdmin: ${isAdmin}, IsLoggedOut: ${isLoggedOut}`);

  // --- アクセス制御対象ルートの定義 ---
  const protectedRoutes = [
    '/dashboard',
    '/settings',
    '/admin',
    '/contents',
    '/chat',
    '/faq',
    '/statement',
    '/application' // 志望校管理機能のパス (必要に応じて修正)
  ];
  const subscriptionRequiredRoutes = ['/contents', '/chat', '/faq', '/statement'];

  const isAdminRoute = pathname.startsWith('/admin');
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  const isSubscriptionRequiredRoute = subscriptionRequiredRoutes.some(route => pathname.startsWith(route));
  // console.log(`[Middleware Check] isProtectedRoute: ${isProtectedRoute}, isSubscriptionRequiredRoute: ${isSubscriptionRequiredRoute}`); // isSubscriptionRequiredRoute の値を確認

  const isStatusPageRoute = pathname === '/pending-activation' || pathname === '/payment-required' || pathname === '/inactive-account';
  const isAuthPage = pathname === '/login' || pathname === '/signup';

  // --- 1. 未認証ユーザーの処理 ---
  if (!isLoggedIn && isProtectedRoute) {
    console.log(`[Middleware Redirect 1] Not authenticated for protected route ${pathname}. Redirecting to login.`);
    const redirectUrl = new URL('/login', nextUrl.origin);
    redirectUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // --- 2. 認証済みユーザーの処理 ---
  if (isLoggedIn) {
    // console.log(`[Middleware DEBUG] Logged in user. Allowing access to ${pathname} (temporarily bypassing checks).`); // デバッグ用ログ削除
    // /* // ★★★ 一時的に以下のチェックをすべてコメントアウト ★★★ // コメントアウト解除
    // 2a. ステータスページへのアクセスは常に許可
    if (isStatusPageRoute) {
      console.log(`[Middleware Allow 2a] Allowing access to status page: ${pathname}`);
      return NextResponse.next();
    }

    // 2b. アカウントステータスに基づく基本的なリダイレクト (Pending / Inactive のみ)
    //    ステータスページ以外へのアクセス時にリダイレクト
    if (userStatus === 'pending') {
      console.log(`[Middleware Redirect 2b] Pending user accessing non-status page ${pathname}. Redirecting to /pending-activation.`);
      return NextResponse.redirect(new URL('/pending-activation', nextUrl.origin));
    }
    if (userStatus === 'inactive') {
      console.log(`[Middleware Redirect 2b] Inactive user accessing non-status page ${pathname}. Redirecting to /inactive-account.`);
      return NextResponse.redirect(new URL('/inactive-account', nextUrl.origin));
    }
    // 【重要】'unpaid' ステータスに対するリダイレクトはここには含めない

    // 2c. サブスクリプション必須ルートへのアクセスチェック
    // アクセス先がサブスクリプション必須ルートであり、かつ、ユーザーステータスが 'active' でない場合のみリダイレクト
    if (isSubscriptionRequiredRoute && userStatus !== 'active') {
      console.log(`[Middleware Redirect 2c] Non-active user (status: ${userStatus}) accessing subscription required route ${pathname}. Redirecting to /subscription/plans.`);
      return NextResponse.redirect(new URL('/subscription/plans', nextUrl.origin));
    }

    // 2d. JWTエラーチェック
    if (authObj?.error === "RefreshAccessTokenError") {
      console.log(`[Middleware Redirect 2d] RefreshAccessTokenError detected. Redirecting to login.`);
      const redirectUrl = new URL('/login', nextUrl.origin);
      redirectUrl.searchParams.set('error', 'session_expired');
      return NextResponse.redirect(redirectUrl);
    }

    // 2e. 管理者関連のチェック
    if (isAdminRoute && !isAdmin) {
      console.log(`[Middleware Redirect 2e] Non-admin access to /admin. Redirecting to dashboard.`);
      return NextResponse.redirect(new URL('/dashboard', nextUrl.origin));
    }
    if (isAdmin && !isAdminRoute && !isAuthPage && !isStatusPageRoute) {
        console.log(`[Middleware Redirect 2e] Admin user accessing non-admin path ${pathname}. Redirecting to /admin/dashboard.`);
        return NextResponse.redirect(new URL('/admin/dashboard', nextUrl.origin));
    }

    // 2f. 認証済みユーザーがログイン/サインアップページにアクセスした場合
    if (isAuthPage) {
      if (pathname === '/login' && isLoggedOut) {
          console.log(`[Middleware Allow 2f] Allowing access to /login immediately after logout.`);
          return NextResponse.next();
      }
      
      const redirectUrl = isAdmin ? '/admin/dashboard' : '/dashboard';
      console.log(`[Middleware Redirect 2f] Authenticated user accessing auth page ${pathname}. Redirecting to ${redirectUrl}.`);
      return NextResponse.redirect(new URL(redirectUrl, nextUrl.origin));
    }
    // */ // ★★★ ここまでコメントアウト ★★★ // コメントアウト解除

    // 上記のどのリダイレクト条件にも当てはまらない場合はアクセスを許可
    console.log(`[Middleware Allow 2g] Allowing request for logged-in user to ${pathname}`);
    return NextResponse.next();
  }

  // --- 3. 未認証ユーザーが保護されていないルートにアクセス ---
  console.log(`[Middleware Allow 3] Allowing request for unauthenticated user to non-protected route ${pathname}`);
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
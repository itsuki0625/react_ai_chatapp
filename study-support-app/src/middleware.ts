import { auth } from '@/auth';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// NextAuthのミドルウェアをエクスポート
export default auth((req) => {
  // auth コールバックが認証をチェックした後に実行されるミドルウェア
  const { nextUrl, auth: authObj } = req;
  const { pathname } = nextUrl;

  // 未認証でアクセスを試みた場合、元のURLのクエリパラメータにリダイレクト先を含めて認証ページへ
  if (!authObj && (
      pathname.startsWith('/dashboard') || 
      pathname.startsWith('/settings') || 
      pathname.startsWith('/admin'))) {
    const redirectUrl = new URL('/login', nextUrl.origin);
    redirectUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // 管理者パスへのアクセスチェック（追加のセキュリティとして）
  if (pathname.startsWith('/admin')) {
    const isAdmin = authObj?.user?.role?.includes('admin');
    if (!isAdmin) {
      // 管理者以外は一般ユーザーダッシュボードへリダイレクト
      return NextResponse.redirect(new URL('/dashboard', nextUrl.origin));
    }
  }

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
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// 認証が不要なパス
const PUBLIC_PATHS = ['/login', '/signup']

export function middleware(request: NextRequest) {
  // 現在のパスを取得
  const path = request.nextUrl.pathname

  // セッションの存在確認
  const isAuthenticated = request.cookies.has('session')
  
  // 認証が不要なパスの場合はスキップ
  if (PUBLIC_PATHS.includes(path)) {
    return NextResponse.next()
  }

  // トークンがない場合はログインページへリダイレクト
  if (!isAuthenticated) {
    const loginUrl = new URL('/login', request.url)
    // 元々アクセスしようとしていたURLをクエリパラメータとして付与
    loginUrl.searchParams.set('redirect', path)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

// ミドルウェアを適用するパスを設定
export const config = {
  matcher: [
    // 除外するパス
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
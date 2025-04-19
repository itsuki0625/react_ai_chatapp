import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// 認証が必要なパス
const protectedPaths = ['/dashboard', '/settings']
// 認証済みユーザーがアクセスできないパス
const authPaths = ['/login', '/signup']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // セッションクッキーの存在を確認（実際の認証状態確認方法はプロジェクトによって異なる）
  const isAuthenticated = request.cookies.has('session')
  
  // 認証が必要なパスに未認証でアクセスした場合
  if (protectedPaths.some(path => pathname.startsWith(path)) && !isAuthenticated) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  
  // 認証済みユーザーが認証ページにアクセスした場合
  if (authPaths.some(path => pathname.startsWith(path)) && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }
  
  return NextResponse.next()
}

// ミドルウェアを適用するパスを設定
export const config = {
  matcher: [...protectedPaths, ...authPaths],
}
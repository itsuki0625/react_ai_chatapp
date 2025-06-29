import { API_BASE_URL } from '@/lib/config';

// APIベースURLを取得
export const getAuthApiUrl = () => {
  return process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || API_BASE_URL;
};

// 認証エンドポイント
export const AUTH_ENDPOINTS = {
  login: '/api/v1/auth/login',
  refresh: '/api/v1/auth/refresh-token',
} as const;

// 認証設定
export const AUTH_CONFIG = {
  // トークンの有効期限（分）
  defaultExpireMinutes: parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES || '15'),
  
  // セッションの最大有効期間（秒）
  sessionMaxAge: 30 * 24 * 60 * 60, // 30日
  
  // トークンリフレッシュの最大試行回数
  maxRefreshAttempts: 3,
  
  // リクエストタイムアウト（ミリ秒）
  requestTimeout: 10000,
  
  // トークンの安全マージン（秒）
  tokenSafetyMargin: 60,
} as const;

// NextAuth設定
export const NEXTAUTH_CONFIG = {
  secret: process.env.NEXTAUTH_SECRET,
  trustHost: true,
  pages: {
    signIn: '/login',
    error: '/login',
  },
  session: {
    strategy: 'jwt' as const,
    maxAge: AUTH_CONFIG.sessionMaxAge,
  },
  cookies: {
    sessionToken: {
      name: 'next-auth.session-token',
      options: {
        httpOnly: true,
        sameSite: 'lax' as const,
        path: '/',
        secure: process.env.NODE_ENV === 'production',
      },
    },
  },
} as const; 
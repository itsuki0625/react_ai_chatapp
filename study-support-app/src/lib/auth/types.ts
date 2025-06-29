import { User as NextAuthUser } from 'next-auth';

// JWT デコード結果の型定義
export interface DecodedToken {
  sub?: string;
  name?: string;
  roles?: string[];
  status?: string;
  permissions?: string[];
  exp?: number;
  [key: string]: any; // Allow other claims
}

// 認証情報の型定義
export interface Credentials {
  email: string;
  password: string;
}

// 拡張されたUserインターフェース
export interface ExtendedUser extends NextAuthUser {
  role?: string | string[];
  status?: string;
  permissions?: string[];
  isTeacher?: boolean;
  grade?: string;
  prefecture?: string;
  profile_image_url?: string | null;
  accessToken?: string;
  refreshToken?: string;
  accessTokenExpires?: number;
}

// バックエンドからのログインレスポンス型
export interface LoginResponse {
  user: {
    id: string;
    full_name: string;
    email: string;
    profile_image_url?: string;
    role: string;
    status: string;
    grade?: string;
    prefecture?: string;
    permissions?: string[]; // 権限情報を追加
  };
  token: {
    access_token: string;
    refresh_token: string;
    expires_in: number;
  };
}

// トークンリフレッシュレスポンス型
export interface RefreshTokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
}

// 認証エラー型
export interface AuthError {
  type: 'RefreshAccessTokenError' | 'AuthorizeError' | 'NetworkError';
  message: string;
  status?: number;
} 
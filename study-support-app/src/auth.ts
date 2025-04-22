import NextAuth from "next-auth";
import { NextAuthConfig } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { API_BASE_URL } from "@/lib/config";
import { jwtDecode } from "jwt-decode";

// APIベースURLを取得
const getBaseUrl = () => {
  return API_BASE_URL;
};

// JWT デコード結果の型定義
interface DecodedToken {
  sub?: string;
  name?: string;
  roles?: string[];
  exp?: number;
  [key: string]: any;
}

// 認証情報の型定義
interface Credentials {
  email: string;
  password: string;
}

const authConfig: NextAuthConfig = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "メールアドレス", type: "email" },
        password: { label: "パスワード", type: "password" }
      },
      async authorize(credentials, request) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const { email, password } = credentials as Credentials;

        try {
          const baseUrl = getBaseUrl();
          console.log('使用するAPIエンドポイント:', baseUrl);

          // JWTベースの認証リクエスト
          const response = await fetch(
            `${baseUrl}/api/v1/auth/login`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
              },
              body: new URLSearchParams({
                username: email,
                password: password
              }).toString(),
              credentials: 'include'
            }
          );

          if (!response.ok) {
            console.error('ログインリクエストが失敗しました:', await response.text());
            return null;
          }

          const data = await response.json();
          
          if (!data.token || !data.token.access_token) {
            console.error('アクセストークンが返されませんでした');
            return null;
          }

          // アクセストークンをデコードしてユーザー情報を取得
          const decodedToken = jwtDecode<DecodedToken>(data.token.access_token);
          console.log('デコードされたトークン:', decodedToken);

          // トークンからユーザー情報を抽出
          return {
            id: decodedToken.sub || 'unknown',
            email,
            name: decodedToken.name || email,
            role: decodedToken.roles || ['user'],
            accessToken: data.token.access_token,
            refreshToken: data.token.refresh_token
          };
        } catch (error) {
          console.error('Auth error:', error);
          return null;
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      // 初回ログイン時にユーザー情報をトークンに追加
      if (user) {
        token.id = user.id || '';
        token.email = user.email || '';
        token.role = user.role || [];
        token.name = user.name || undefined;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.accessTokenExpires = Date.now() + 15 * 60 * 1000; // 15分
      }

      // アクセストークンの期限が切れている場合はリフレッシュ
      const shouldRefreshTime = Math.round((token.accessTokenExpires as number) - 60 * 1000 - Date.now());
      
      if (shouldRefreshTime <= 0) {
        console.log('トークンの有効期限が切れています。リフレッシュします...');
        
        try {
          const baseUrl = getBaseUrl();
          const response = await fetch(`${baseUrl}/api/v1/auth/refresh-token`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              refresh_token: token.refreshToken
            }),
            credentials: 'include'
          });

          if (!response.ok) {
            console.error('トークンリフレッシュに失敗しました');
            return { ...token, error: "RefreshAccessTokenError" };
          }

          const refreshedTokens = await response.json();
          console.log('トークンがリフレッシュされました');

          if (!refreshedTokens.access_token) {
            console.error('新しいアクセストークンが返されませんでした');
            return { ...token, error: "RefreshAccessTokenError" };
          }

          // 新しいトークン情報をデコード
          const decodedRefreshedToken = jwtDecode<DecodedToken>(refreshedTokens.access_token);

          return {
            ...token,
            accessToken: refreshedTokens.access_token,
            refreshToken: refreshedTokens.refresh_token || token.refreshToken,
            accessTokenExpires: Date.now() + 15 * 60 * 1000,
            role: decodedRefreshedToken.roles || token.role
          };
        } catch (error) {
          console.error('トークンリフレッシュエラー:', error);
          return { ...token, error: "RefreshAccessTokenError" };
        }
      }

      return token;
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.id = token.id as string;
        session.user.email = token.email as string;
        session.user.name = token.name as string;
        
        // ロールが配列であることを確認
        const roles = Array.isArray(token.role) 
          ? token.role as string[] 
          : (typeof token.role === 'string' ? [token.role as string] : []);
        
        session.user.role = roles;
        
        // 権限フラグを設定
        session.user.isAdmin = roles.includes('admin');
        session.user.isTeacher = roles.includes('teacher');
        session.user.isStudent = roles.includes('student');
        
        // トークン情報をセッションに追加
        session.accessToken = token.accessToken as string;
        session.error = token.error as string;
      }
      return session;
    },
    authorized({ auth, request }) {
      const { pathname } = request.nextUrl;
      const isLoggedIn = !!auth?.user;
      
      // 管理者パス
      const isAdminPath = pathname.startsWith('/admin');
      // 認証が必要なパス
      const authRequired = pathname.startsWith('/dashboard') || 
                           pathname.startsWith('/settings') || 
                           isAdminPath;
      // 認証ページ
      const isAuthPage = pathname.startsWith('/login') || pathname.startsWith('/signup');

      // 管理者パスへのアクセスは管理者のみ
      if (isAdminPath) {
        const isAdmin = auth?.user?.role ? 
          (Array.isArray(auth.user.role) ? auth.user.role.includes('admin') : auth.user.role === 'admin')
          : false;
        return isLoggedIn && isAdmin;
      }

      // 認証ページへのアクセスはログインしていない場合のみ
      if (isAuthPage) {
        return !isLoggedIn;
      }

      // 認証が必要なパスへのアクセスはログインしている場合のみ
      if (authRequired) {
        return isLoggedIn;
      }

      return true;
    }
  },
  pages: {
    signIn: '/login',
    newUser: '/signup',
    error: '/login'
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30日
  },
  cookies: {
    sessionToken: {
      name: `next-auth.session-token`,
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: process.env.NODE_ENV === "production",
      },
    }
  }
};

export const { handlers, auth, signIn, signOut } = NextAuth(authConfig);

// 型拡張
declare module "next-auth" {
  interface User {
    id?: string;
    email?: string | null;
    name?: string | null;
    role?: string[];
    accessToken?: string;
    refreshToken?: string;
  }
  
  interface Session {
    user: {
      id: string;
      email: string;
      name?: string | null;
      role: string[];
      isAdmin: boolean;
      isTeacher: boolean;
      isStudent: boolean;
    };
    accessToken: string;
    error?: string;
  }
}

// JWTの型拡張
declare module "@auth/core/jwt" {
  interface JWT {
    id: string;
    email: string;
    name?: string | null;
    role: string[] | string;
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    error?: string;
  }
} 
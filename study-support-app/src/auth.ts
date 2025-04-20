import NextAuth from "next-auth";
import { NextAuthConfig } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { API_BASE_URL } from "@/lib/config";

// APIベースURLを取得
const getBaseUrl = () => {
  return API_BASE_URL;
};

const authConfig: NextAuthConfig = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "メールアドレス", type: "email" },
        password: { label: "パスワード", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          // フォームデータを使用
          const formData = new URLSearchParams();
          formData.append('username', credentials.email as string);
          formData.append('password', credentials.password as string);

          const baseUrl = getBaseUrl();
          console.log('使用するAPIエンドポイント:', baseUrl);

          // クッキーを保持するための設定
          const response = await fetch(
            `${baseUrl}/api/v1/auth/login`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
              },
              body: formData.toString(),
              credentials: 'include'
            }
          );

          if (!response.ok) {
            console.error('ログインリクエストが失敗しました:', await response.text());
            return null;
          }

          // レスポンスのクッキーヘッダーを確認（デバッグ用）
          console.log('ログインレスポンスヘッダー:', response.headers);
          
          // Set-Cookieヘッダーを保存
          const cookies = response.headers.get('set-cookie');
          console.log('受信したクッキー:', cookies);

          const userData = await response.json();
          console.log('ログイン成功:', userData);

          // セッションクッキーを明示的に確認
          if (typeof window !== 'undefined') {
            console.log('現在のクッキー:', document.cookie);
          }

          // 少し待機してセッションが確立されるようにする
          await new Promise(resolve => setTimeout(resolve, 1000));

          // ユーザー情報を取得して管理者かどうかを確認
          try {
            const userResponse = await fetch(
              `${baseUrl}/api/v1/auth/me`,
              { 
                credentials: 'include',
                headers: {
                  // セッションクッキーを明示的に送信
                  'Cookie': cookies || 
                    (typeof window !== 'undefined' ? document.cookie : '')
                }
              }
            );

            if (!userResponse.ok) {
              console.error('ユーザー情報の取得に失敗しました:', await userResponse.text());
              // クリティカルなエラーではなく、基本的な情報だけで進める
              return {
                id: userData.user_id || 'temp-id',
                email: credentials.email as string,
                role: userData.role || ['user'],
                name: userData.full_name || credentials.email
              };
            }

            const user = await userResponse.json();
            console.log('ユーザー情報取得成功:', user);

            return {
              id: user.user_id || userData.user_id || 'temp-id',
              email: user.email || userData.email,
              role: user.role || userData.role || ['user'],
              name: userData.full_name
            };
          } catch (userError) {
            console.error('ユーザー情報取得中のエラー:', userError);
            // エラーが発生しても、基本的な認証情報だけで進める
            return {
              id: 'temp-id',
              email: credentials.email as string,
              role: userData.role || ['user'],
              name: userData.full_name || credentials.email
            };
          }
        } catch (error) {
          console.error('Auth error:', error);
          return null;
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role || [];
        token.id = user.id || '';
      }
      return token;
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.id = token.id as string;
        
        // ロールが配列であることを確認
        const roles = Array.isArray(token.role) 
          ? token.role as string[] 
          : (typeof token.role === 'string' ? [token.role as string] : []);
        
        session.user.role = roles;
        
        // 管理者権限の確認
        session.user.isAdmin = roles.includes('admin');
        
        // 講師権限の確認
        session.user.isTeacher = roles.includes('teacher');
        
        // 生徒権限の確認
        session.user.isStudent = roles.includes('student');
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
    role?: string[];
    isAdmin?: boolean;
    isTeacher?: boolean;
    isStudent?: boolean;
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
  }
}

// JWTの型拡張
declare module "@auth/core/jwt" {
  interface JWT {
    id: string;
    role: string[] | string;
  }
} 
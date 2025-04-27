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
  status?: string;
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
        console.log("[Authorize] Attempting authorization..."); // DEBUG LOG
        if (!credentials?.email || !credentials?.password) {
          console.log("[Authorize] Missing credentials."); // DEBUG LOG
          return null;
        }

        const { email, password } = credentials as Credentials;

        try {
          const baseUrl = getBaseUrl();
          console.log(`[Authorize] Using API base URL: ${baseUrl}`); // DEBUG LOG

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
            const errorBody = await response.text();
            console.error(`[Authorize] Login request failed (${response.status}): ${errorBody}`); // DEBUG LOG
            return null;
          }

          const data = await response.json();

          if (!data.token || !data.token.access_token) {
            console.error('[Authorize] Access token not found in response.'); // DEBUG LOG
            return null;
          }

          const decodedToken = jwtDecode<DecodedToken>(data.token.access_token);
          console.log('[Authorize] Decoded access token:', decodedToken); // DEBUG LOG

          const user = {
            id: decodedToken.sub || 'unknown',
            email,
            name: decodedToken.name || email,
            role: decodedToken.roles || ['user'],
            status: data.user?.status || 'pending',
            accessToken: data.token.access_token,
            refreshToken: data.token.refresh_token,
            // accessTokenExpires をミリ秒で設定 (例: 15分)
            accessTokenExpires: (decodedToken.exp ? decodedToken.exp * 1000 : Date.now() + 15 * 60 * 1000)
          };
          console.log("[Authorize] Authorization successful, returning user:", user); // DEBUG LOG
          return user;
        } catch (error) {
          console.error('[Authorize] Error during authorization:', error); // DEBUG LOG
          return null;
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      console.log("[JWT Callback] Invoked. User:", user, "Account:", account, "Existing Token:", token); // DEBUG LOG
      // 初回ログイン時
      if (user && account?.provider === "credentials") {
        console.log("[JWT Callback] Initial sign in. Populating token from user object."); // DEBUG LOG
        token.id = user.id || '';
        token.email = user.email || '';
        token.role = user.role || [];
        token.name = user.name || undefined;
        token.status = (user as any).status || 'pending';
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        // authorizeから渡された有効期限を使用 (userにaccessTokenExpiresを追加する必要あり)
        token.accessTokenExpires = (user as any).accessTokenExpires || Date.now() + 15 * 60 * 1000;
        console.log("[JWT Callback] Token populated:", token); // DEBUG LOG
        return token;
      }

      // アクセストークンの有効期限チェック
      if (token.accessTokenExpires && Date.now() < (token.accessTokenExpires as number)) {
          console.log("[JWT Callback] Access token is still valid."); // DEBUG LOG
          return token; // 有効期限内ならそのまま返す
      }

      // アクセストークンの有効期限切れ、または有効期限情報がない場合リフレッシュを試みる
      console.log('[JWT Callback] Access token expired or expiry unknown. Attempting refresh...');
      if (!token.refreshToken) {
          console.error("[JWT Callback] No refresh token available."); // DEBUG LOG
          return { ...token, error: "RefreshAccessTokenError" };
      }

      try {
        const baseUrl = getBaseUrl();
        console.log(`[JWT Callback] Refreshing token using URL: ${baseUrl}/api/v1/auth/refresh-token`); // DEBUG LOG
        const response = await fetch(`${baseUrl}/api/v1/auth/refresh-token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            refresh_token: token.refreshToken
          }),
          credentials: 'include' // 必要であれば
        });

        if (!response.ok) {
          const errorBody = await response.text();
          console.error(`[JWT Callback] Token refresh failed (${response.status}): ${errorBody}`); // DEBUG LOG
          return { ...token, error: "RefreshAccessTokenError" };
        }

        const refreshedTokens = await response.json();
        console.log('[JWT Callback] Tokens refreshed successfully:', refreshedTokens); // DEBUG LOG

        if (!refreshedTokens.access_token) {
          console.error('[JWT Callback] Refreshed response missing access_token.'); // DEBUG LOG
          return { ...token, error: "RefreshAccessTokenError" };
        }

        const decodedRefreshedToken = jwtDecode<DecodedToken>(refreshedTokens.access_token);
        console.log("[JWT Callback] Decoded refreshed access token:", decodedRefreshedToken); // DEBUG LOG

        const updatedToken = {
          ...token, // 既存のトークン情報を保持
          accessToken: refreshedTokens.access_token,
          // リフレッシュトークンが返却されていれば更新、なければ既存のを維持
          refreshToken: refreshedTokens.refresh_token || token.refreshToken,
          // 新しいアクセストークンの有効期限を設定 (デコード結果 or デフォルト15分)
          accessTokenExpires: (decodedRefreshedToken.exp ? decodedRefreshedToken.exp * 1000 : Date.now() + 15 * 60 * 1000),
          role: decodedRefreshedToken.roles || token.role, // ロールも更新
          status: decodedRefreshedToken.status || token.status,
          error: undefined, // エラー状態をクリア
        };
        console.log("[JWT Callback] Returning updated token:", updatedToken); // DEBUG LOG
        return updatedToken;

      } catch (error) {
        console.error('[JWT Callback] Error during token refresh:', error); // DEBUG LOG
        return { ...token, error: "RefreshAccessTokenError" };
      }
    },
    async session({ session, token }) {
      console.log("[Session Callback] Invoked. Token:", token, "Existing Session:", session); // DEBUG LOG
      if (token && session.user) {
        session.user.id = token.id as string;
        session.user.email = token.email as string;
        session.user.name = token.name as string;
        session.user.status = token.status as string;

        const roles = Array.isArray(token.role)
          ? token.role as string[]
          : (typeof token.role === 'string' ? [token.role as string] : []);

        session.user.role = roles;
        session.user.isAdmin = roles.includes('admin_access');
        session.user.isTeacher = roles.includes('teacher');
        session.user.isStudent = roles.includes('student');

        session.accessToken = token.accessToken as string;
        session.error = token.error as string;
        console.log("[Session Callback] Session updated:", session); // DEBUG LOG
      }
      return session;
    },
    // authorized コールバックはミドルウェアに移行したため、ここでは不要な場合がある
    // もし残す場合は、ミドルウェアと重複しないように注意
    /*
    authorized({ auth, request }) {
      console.log("[Authorized Callback] Path:", request.nextUrl.pathname, "Auth:", auth); // DEBUG LOG
      const { pathname } = request.nextUrl;
      const isLoggedIn = !!auth?.user;

      const isAdminPath = pathname.startsWith('/admin');
      const authRequired = pathname.startsWith('/dashboard') ||
                           pathname.startsWith('/settings') ||
                           isAdminPath;
      const isAuthPage = pathname.startsWith('/login') || pathname.startsWith('/signup');

      if (isAdminPath) {
        const isAdmin = auth?.user?.role ?
          (Array.isArray(auth.user.role) ? auth.user.role.includes('admin') : auth.user.role === 'admin')
          : false;
        const authorized = isLoggedIn && isAdmin;
        console.log(`[Authorized Callback] Admin path access check: ${authorized}`); // DEBUG LOG
        return authorized;
      }

      if (isAuthPage) {
        const authorized = !isLoggedIn;
        console.log(`[Authorized Callback] Auth page access check: ${authorized}`); // DEBUG LOG
        return authorized;
      }

      if (authRequired) {
        console.log(`[Authorized Callback] Auth required path access check: ${isLoggedIn}`); // DEBUG LOG
        return isLoggedIn;
      }

      console.log("[Authorized Callback] Allowing access."); // DEBUG LOG
      return true;
    }
    */
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
    status?: string;
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number; // authorizeから渡すために追加
  }
  
  interface Session {
    user: {
      id: string;
      email: string;
      name?: string | null;
      role: string[];
      status: string;
      isAdmin: boolean;
      isTeacher: boolean;
      isStudent: boolean;
    };
    accessToken: string;
    error?: string;
  }

  interface JWT {
    id: string;
    email: string;
    name?: string | null;
    role: string[] | string;
    status: string;
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    error?: string;
  }
} 
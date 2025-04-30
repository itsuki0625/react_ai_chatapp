import NextAuth, { DefaultSession, NextAuthConfig, User as NextAuthUser, Account, Profile } from 'next-auth';
import { JWT } from 'next-auth/jwt';
import { AdapterUser } from "next-auth/adapters";
import CredentialsProvider from 'next-auth/providers/credentials';
import { Session } from "next-auth";
import { JWT as NextAuthJWT } from "next-auth/jwt";
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
  permissions?: string[];
  exp?: number;
  [key: string]: any; // Allow other claims
}

// 認証情報の型定義
interface Credentials {
  email: string;
  password: string;
}

// Userインターフェースの拡張 (next-auth.d.tsで定義済みならここでは不要かも)
interface User extends NextAuthUser {
  role?: string | string[]; // ★ role を string | string[] に変更
  status?: string;
  permissions?: string[];
  isTeacher?: boolean;
  grade?: string;
  prefecture?: string;
  accessToken?: string;
  refreshToken?: string;
  accessTokenExpires?: number;
}

export const authConfig: NextAuthConfig = {
  // 追加: シークレットとホストチェック無効化（ステージング用）
  secret: process.env.NEXTAUTH_SECRET,
  trustHost: true,
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "メールアドレス", type: "email" },
        password: { label: "パスワード", type: "password" }
      },
      async authorize(credentials): Promise<User | null> {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        const { email, password } = credentials;
        console.debug('[Authorize] Attempting authorization for:', email); // DEBUG LOG

        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: email, password }),
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error(`[Authorize] API login failed for ${email}:`, response.status, errorData);
            throw new Error(errorData.detail || 'Authentication failed');
          }

          const data = await response.json(); // LoginResponse 形式を期待
          console.log('[Authorize] API login successful, data received:', data); // DEBUG LOG

          if (!data || !data.token || !data.token.access_token || !data.user) {
            console.error('[Authorize] API response missing required fields (token or user)');
            throw new Error('Invalid API response');
          }

          // BackendのUser型とToken型をNextAuthのUser型にマッピング
          // ★注意: バックエンドのUserResponse型とNextAuthのUser型のフィールドを合わせる
          const user: User = {
              id: data.user.id,
              name: data.user.full_name, // Backendのfull_nameをnameに
              email: data.user.email,
              // image: data.user.profile_image_url, // 必要なら追加
              role: data.user.role, // Backendのroleをそのまま利用
              status: data.user.status, // Backendのstatusを利用
              // permissions: data.user.permissions, // permissionsはtokenに含まれる想定
              // isTeacher: data.user.role === '講師', // session callbackで設定するので不要かも
              grade: data.user.grade, // ★ grade を追加 (LoginResponseのuserに含まれている想定)
              prefecture: data.user.prefecture, // ★ prefecture を追加 (LoginResponseのuserに含まれている想定)
              accessToken: data.token.access_token, // token情報をUser型に含める
              refreshToken: data.token.refresh_token,
              accessTokenExpires: Date.now() + data.token.expires_in * 1000,
          };
          console.debug("Authorize Callback: User object created", { userId: user.id, role: user.role, grade: user.grade }); // ★ logger を console.debug に変更
          return user;
        } catch (error) {
          console.error("[Authorize] Error in authorize callback:", error);
          return null;
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account, profile, trigger, isNewUser, session }: {
        token: JWT;
        user?: User | AdapterUser; // ★ user の型を修正
        account?: Account | null; // ★ account の型を修正
        profile?: Profile; // ★ profile の型を修正
        trigger?: "signIn" | "signUp" | "update"; // ★ trigger を追加
        isNewUser?: boolean;
        session?: any; // ★ session を追加
    }): Promise<JWT> {
        console.debug("JWT Callback: Start", { tokenId: token?.jti, userId: user?.id, trigger });

        // update トリガーの場合 (例: useSession().update() 呼び出し)
        if (trigger === "update" && session) {
            console.debug("JWT Callback: Update trigger detected", { sessionData: session });
            // セッションデータでトークンを更新 (必要なフィールドのみ)
            token.name = session.user?.name;
            token.grade = session.user?.grade; // 例: gradeを更新
            token.prefecture = session.user?.prefecture; // 例: prefectureを更新
            // 他にも更新したいフィールドがあれば追加
            return token;
        }

        // 初回ログイン時 (user オブジェクトが存在する場合)
        if (user && (trigger === 'signIn' || trigger === 'signUp')) {
            console.debug(`JWT Callback: ${trigger} trigger (user object present)`, { userId: user.id });
            // authorize コールバックからの User オブジェクトを想定
            const authUser = user as User;

            // アクセストークンの有効期限を計算 (秒単位で)
            const defaultExpireMinutes = process.env.ACCESS_TOKEN_EXPIRE_MINUTES ? parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES) : 15;
            const expiresAt = authUser.accessTokenExpires
                ? Math.floor(authUser.accessTokenExpires / 1000)
                : Math.floor(Date.now() / 1000) + defaultExpireMinutes * 60;

            // token オブジェクトを拡張
            const extendedToken: JWT = {
                ...token,
                id: String(authUser.id),
                name: authUser.name,
                email: authUser.email,
                picture: authUser.image,
                role: authUser.role, // authorizeから渡されたrole (string | string[] の可能性あり)
                status: authUser.status,
                permissions: token.permissions || authUser.permissions, // 維持 or マージ
                isTeacher: authUser.isTeacher,
                grade: authUser.grade,
                prefecture: authUser.prefecture,
                accessToken: authUser.accessToken,
                refreshToken: authUser.refreshToken,
                accessTokenExpires: expiresAt,
                iat: Math.floor(Date.now() / 1000),
                exp: expiresAt,
                jti: crypto.randomUUID()
            };
            console.debug("JWT Callback: Initial token population", { token: extendedToken });
            return extendedToken;
        }

        // アクセストークンの有効期限チェック
        if (token.accessTokenExpires && Date.now() < token.accessTokenExpires * 1000) {
            console.debug("JWT Callback: Access token is valid", { tokenId: token.jti });
            return token;
        }

        // アクセストークンが無効、または期限切れの場合：リフレッシュ
        console.info("JWT Callback: Access token expired or invalid, attempting refresh", { tokenId: token.jti });
        if (!token.refreshToken) {
            console.error("JWT Callback: No refresh token available, cannot refresh. Returning error.", { tokenId: token.jti });
            return { ...token, error: "RefreshAccessTokenError" };
        }

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/refresh-token`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: token.refreshToken }),
            });

            const refreshedTokens = await response.json();

            if (!response.ok) {
                console.error("JWT Callback: Failed to refresh token from API", { status: response.status, error: refreshedTokens });
                const errorDetail = refreshedTokens?.detail || "Refresh token failed";
                throw new Error(errorDetail);
            }
            const defaultExpireMinutesOnRefresh = process.env.ACCESS_TOKEN_EXPIRE_MINUTES ? parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES) : 15;
            const newExpiresAt = Math.floor(Date.now() / 1000) + (refreshedTokens.expires_in || defaultExpireMinutesOnRefresh * 60);
            const refreshedTokenData: JWT = {
                ...token,
                accessToken: refreshedTokens.access_token,
                refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
                accessTokenExpires: newExpiresAt,
                iat: Math.floor(Date.now() / 1000),
                exp: newExpiresAt,
                jti: crypto.randomUUID(),
                error: undefined,
                grade: token.grade, // 維持
                prefecture: token.prefecture, // 維持
            };

            console.info("JWT Callback: Token refreshed successfully", { newTokenId: refreshedTokenData.jti });
            return refreshedTokenData;
        } catch (error: any) {
            console.error("JWT Callback: Error refreshing access token", {
                errorMessage: error.message,
                errorDetails: error,
                refreshTokenUsed: token.refreshToken?.substring(0, 10) + '...'
            });
            return {
                ...token,
                error: "RefreshAccessTokenError",
            };
        }
    },
    async session({ session, token }: { session: Session; token: JWT }): Promise<Session> {
      console.debug("Session Callback: Start", { userId: token?.id, tokenJti: token?.jti });
      // エラーがあればセッションにエラー情報をセット
      if (token.error) {
        session.error = token.error;
        console.warn("Session Callback: Token error detected, returning session with error", { error: token.error, sessionId: session?.user?.id });
        // エラー時はユーザー情報をクリアするなど検討
        // session.user = { id: '', name: null, email: null }; // 例
        return session;
      }

      // token から session.user に必要な情報を移す
      // Roleの正規化や追加の処理を行う
      const normalizeRole = (roleInput: string | string[] | undefined): string => {
        let roleName: string | undefined;
        if (Array.isArray(roleInput)) {
            roleName = roleInput[0]; // 配列の場合は最初の要素を使用 (必要に応じてロジック変更)
        } else {
            roleName = roleInput;
        }
        const lowerCaseRole = roleName?.toLowerCase();
        if (lowerCaseRole === 'admin' || lowerCaseRole === '管理者') return '管理者';
        if (lowerCaseRole === 'teacher' || lowerCaseRole === '教師') return '教師';
        return '生徒'; // デフォルト
      };

      const userRole = normalizeRole(token.role);
      // ★ 新しい役割判定ロジック ★
      const isAdmin = userRole === '管理者';
      const isTeacher = userRole === '教師';
      const isStudent = !isAdmin && !isTeacher; // 管理者でも教師でもなければ生徒

      // セッションオブジェクトを構築 (next-auth.d.ts の Session['user'] に合わせる)
      session.user = {
        id: token.id ?? '',
        name: token.name,
        email: token.email,
        image: token.picture,
        role: userRole, // 正規化されたロール (表示用などに)
        status: token.status ?? 'pending',
        permissions: token.permissions,
        isAdmin: isAdmin, // 計算結果を代入
        isTeacher: isTeacher, // 計算結果を代入
        isStudent: isStudent, // 計算結果を代入
        grade: token.grade,
        prefecture: token.prefecture,
      };
      session.accessToken = token.accessToken ?? ''; // ★ token.accessToken が undefined の場合は空文字
      // session.expires は token.exp があれば設定
      if (token.exp) {
          session.expires = new Date(token.exp * 1000).toISOString();
      } else {
          // token.exp がない場合、デフォルトの有効期限を設定するか、エラー処理
          console.warn("Session Callback: token.exp not found, session.expires may be inaccurate.");
          // session.expires = new Date(Date.now() + 15 * 60 * 1000).toISOString(); // 例: 15分後
      }

      console.debug("Session Callback: Session data populated", { userId: session.user.id, role: session.user.role });

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

// --- Type Definitions ---
// 以下の declare module ブロックは next-auth.d.ts に定義を移動したため削除します。
/*
declare module "next-auth" {
  // ... (User, Session, JWT interface definitions)
}
*/ 
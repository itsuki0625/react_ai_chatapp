import NextAuth, { DefaultSession, NextAuthConfig, User as NextAuthUser, Account, Profile } from 'next-auth';
import { JWT } from 'next-auth/jwt';
import { AdapterUser } from "next-auth/adapters";
import CredentialsProvider from 'next-auth/providers/credentials';
import { Session } from "next-auth";
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

// Userインターフェースの拡張
interface User extends NextAuthUser {
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

export const authConfig: NextAuthConfig = {
  // 追加: シークレットとホストチェック無効化（ステージング用）
  secret: process.env.NEXTAUTH_SECRET,
  trustHost: true,
  pages: {
    signIn: '/login',
    error: '/login', // エラー時もログインページに戻す
  },
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "メールアドレス", type: "email" },
        password: { label: "パスワード", type: "password" }
      },
      async authorize(credentials): Promise<User | null> {
        console.log('=== NEXTAUTH AUTHORIZE START ===');
        console.log('受信した認証情報:', credentials);
        
        if (!credentials?.email || !credentials?.password) {
          console.warn('[Authorize] Missing email or password');
          return null;
        }
        // ★ 型アサーションを追加して email と password が string であることを保証
        const email = credentials.email as string;
        const password = credentials.password as string;
        console.debug('[Authorize] Attempting authorization for:', email); // DEBUG LOG

        // ★ サーバーサイド用の内部API URLを使用
        const apiUrl = `${process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/login`;
        // (INTERNAL_API_BASE_URL が未定義の場合のフォールバックとして NEXT_PUBLIC も残しておく)
        console.log('>>> [Authorize] API URL:', apiUrl);
        console.log('>>> [Authorize] 環境変数確認:');
        console.log('   INTERNAL_API_BASE_URL:', process.env.INTERNAL_API_BASE_URL);
        console.log('   NEXT_PUBLIC_API_BASE_URL:', process.env.NEXT_PUBLIC_API_BASE_URL);

        try {
          console.log('[Authorize] リクエスト準備中...');
          
          // データ形式を application/x-www-form-urlencoded に変更
          const body = new URLSearchParams();
          body.append('username', email);
          body.append('password', password);

          console.log('[Authorize] リクエストボディ準備完了');
          console.log('[Authorize] APIリクエスト送信中...');

          const response = await fetch(apiUrl, { // ★ apiUrl を使用
            method: 'POST',
            headers: { 
              'Content-Type': 'application/x-www-form-urlencoded',
              'Accept': 'application/json',
            }, 
            body: body, // ★ URLSearchParams オブジェクトを送信
            // ★ タイムアウトとエラーハンドリングを追加
            signal: AbortSignal.timeout(10000), // 10秒タイムアウト
          });

          console.log('[Authorize] レスポンス受信:', {
            status: response.status,
            statusText: response.statusText,
            url: response.url,
            headers: Object.fromEntries(response.headers.entries())
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error(`[Authorize] API login failed for ${email}:`, response.status, errorData);
            // ★ より詳細なエラーログ
            console.error(`[Authorize] Response headers:`, Object.fromEntries(response.headers.entries()));
            throw new Error(errorData.detail || `Authentication failed (${response.status})`);
          }

          const data = await response.json(); // LoginResponse 形式を期待
          console.log('[Authorize] API login successful, data received:', data); // DEBUG LOG

          if (!data || !data.token || !data.token.access_token || !data.user) {
            console.error('[Authorize] API response missing required fields (token or user)');
            throw new Error('Invalid API response format');
          }

          // BackendのUser型とToken型をNextAuthのUser型にマッピング
          const user: User = {
              id: data.user.id,
              name: data.user.full_name,
              email: data.user.email,
              image: data.user.profile_image_url,
              role: data.user.role,
              status: data.user.status,
              grade: data.user.grade,
              prefecture: data.user.prefecture,
              profile_image_url: data.user.profile_image_url,
              accessToken: data.token.access_token,
              refreshToken: data.token.refresh_token,
              accessTokenExpires: Date.now() + data.token.expires_in * 1000,
          };
          console.debug("Authorize Callback: User object created", { userId: user.id, role: user.role }); // ★ ログ追加
          console.log('=== NEXTAUTH AUTHORIZE SUCCESS ===');
          return user;
        } catch (error: any) { // ★ エラーの型を any にして詳細をログ出力
          console.error("=== NEXTAUTH AUTHORIZE ERROR ===");
          console.error("[Authorize] Error in authorize callback:", error);
          // ★ ネットワークエラーと他のエラーを区別
          if (error.name === 'AbortError') {
            console.error("[Authorize] Request timeout");
          } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
            console.error("[Authorize] Network connection error");
          }
          // ★ エラーの原因 (cause) もログ出力してみる
          if (error.cause) {
            console.error("[Authorize] Error Cause:", error.cause);
          }
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

        // 1. 初回ログイン時 (user オブジェクトが存在する場合)
        if (user && (trigger === 'signIn' || trigger === 'signUp')) {
            console.debug(`JWT Callback: ${trigger} trigger (user object present)`, { userId: user.id });
            const authUser = user as User;

            // --- アクセストークンをデコードして情報を取得 ---
            let decodedAccessToken: DecodedToken = {};
            let tokenPermissions: string[] | undefined = undefined;
            let tokenRoles: string[] | undefined = undefined; // <<< roles を配列で受け取る準備

            try {
              if(authUser.accessToken) {
                decodedAccessToken = jwtDecode<DecodedToken>(authUser.accessToken);
                tokenPermissions = decodedAccessToken.permissions;
                tokenRoles = decodedAccessToken.roles; // <<< デコード結果から roles を取得
                console.debug("JWT Callback: Decoded access token", { roles: tokenRoles, permissions: tokenPermissions });
              }
            } catch (e) {
              console.error("JWT Callback: Failed to decode access token", e);
              // デコード失敗しても処理は続ける（一部情報が欠ける可能性あり）
            }
            // --- ここまで追加 ---

            const defaultExpireMinutes = process.env.ACCESS_TOKEN_EXPIRE_MINUTES ? parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES) : 15;
            const expiresAt = authUser.accessTokenExpires
                ? Math.floor(authUser.accessTokenExpires / 1000)
                : Math.floor(Date.now() / 1000) + defaultExpireMinutes * 60;

            const extendedToken: JWT = {
                ...token,
                id: String(authUser.id),
                name: authUser.name,
                email: authUser.email,
                picture: authUser.image,
                profile_image_url: authUser.profile_image_url,
                // --- role と permissions をデコード結果から設定 ---
                role: tokenRoles || authUser.role, // デコードした roles (配列) を優先、なければ authorize の role
                permissions: tokenPermissions,      // デコードした permissions を設定
                // --- ここまで修正 ---
                status: authUser.status,
                isTeacher: authUser.isTeacher, // isTeacherは authorize で設定したもので良いか要検討
                grade: authUser.grade,
                prefecture: authUser.prefecture,
                accessToken: authUser.accessToken,
                refreshToken: authUser.refreshToken,
                accessTokenExpires: expiresAt,
                iat: Math.floor(Date.now() / 1000),
                exp: expiresAt,
                jti: crypto.randomUUID()
            };
            console.debug("JWT Callback: Initial token population", { userId: extendedToken.id, role: extendedToken.role, profile_image_url: extendedToken.profile_image_url }); // ★ ログ追加
            return extendedToken;
        }

        // 2. トークンがまだ有効な場合 (リフレッシュ不要)
        if (token.accessTokenExpires && Date.now() < (token.accessTokenExpires * 1000 - 60 * 1000)) {
            // 有効期限の60秒前までは何もしない
            console.debug("JWT Callback: Access token is still valid", { tokenId: token.jti });
            return token;
        }

        // 3. トークンが無効または有効期限が近い場合 (リフレッシュ実行)
        console.info("JWT Callback: Access token expired or nearing expiry, attempting refresh", { tokenId: token.jti });
        
        if (!token.refreshToken) {
            console.error("JWT Callback: No refresh token available", { tokenId: token.jti });
            return { ...token, error: "RefreshAccessTokenError" };
        }

        // 既にエラー状態の場合は再リフレッシュを試行しない（無限ループ防止）
        const failureCount = (token.refreshFailureCount as number) || 0;
        if (failureCount >= 3) {
            console.error("JWT Callback: Too many refresh failures", { tokenId: token.jti, failureCount });
            return {
                ...token,
                error: "RefreshAccessTokenError",
                errorDetail: "Too many refresh failures",
                accessToken: undefined,
                refreshToken: undefined,
                accessTokenExpires: 0,
            };
        }

        try {
            console.debug("JWT Callback: Attempting to refresh token...");
            const refreshUrl = `${process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/refresh-token`;
            
            const response = await fetch(refreshUrl, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body: JSON.stringify({ refresh_token: token.refreshToken }),
                credentials: 'include',
                signal: AbortSignal.timeout(10000), // 10秒タイムアウト
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error("JWT Callback: Failed to refresh token", { 
                    status: response.status, 
                    error: errorData
                });
                
                // 463エラー（トークン無効）の場合は完全にセッションを破棄
                if (response.status === 463) {
                    console.warn("JWT Callback: 463 error - refresh token invalid");
                    return { 
                        ...token, 
                        error: "RefreshAccessTokenError",
                        errorDetail: "Refresh token is invalid or expired (463)",
                        accessToken: undefined,
                        refreshToken: undefined,
                        accessTokenExpires: 0,
                    };
                }
                
                return { 
                    ...token, 
                    error: "RefreshAccessTokenError", 
                    errorDetail: errorData?.detail || `Refresh failed (${response.status})`,
                    refreshFailureCount: failureCount + 1,
                };
            }

            const refreshedTokens = await response.json();

            // リフレッシュ成功時の処理
            let refreshedDecoded: DecodedToken = {};
            let refreshedRoles: string[] | undefined = undefined;
            let refreshedPermissions: string[] | undefined = undefined;
            
            try {
                refreshedDecoded = jwtDecode<DecodedToken>(refreshedTokens.access_token);
                refreshedRoles = refreshedDecoded.roles;
                refreshedPermissions = refreshedDecoded.permissions;
                console.debug("JWT Callback: Successfully decoded refreshed token");
            } catch(e) {
                console.error("JWT Callback: Failed to decode refreshed access token", e);
            }

            const defaultExpireMinutes = parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES || '15');
            const newExpiresInSeconds = refreshedTokens.expires_in || defaultExpireMinutes * 60;
            const newExpiresAt = Math.floor(Date.now() / 1000) + newExpiresInSeconds;

            const refreshedTokenData: JWT = {
                ...token,
                accessToken: refreshedTokens.access_token,
                refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
                accessTokenExpires: newExpiresAt,
                role: refreshedRoles || token.role,
                permissions: refreshedPermissions || token.permissions,
                iat: Math.floor(Date.now() / 1000),
                exp: newExpiresAt,
                jti: crypto.randomUUID(),
                error: undefined,
                errorDetail: undefined,
                refreshFailureCount: 0, // 成功時はリセット
            };

            console.info("JWT Callback: Token refreshed successfully", { newTokenId: refreshedTokenData.jti });
            return refreshedTokenData;

        } catch (error: any) {
            console.error("JWT Callback: Error during token refresh", {
                errorMessage: error.message,
                errorName: error.name,
            });
            
            let errorDetail = "Network error during token refresh";
            if (error.name === 'AbortError') {
                errorDetail = "Request timeout during token refresh";
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorDetail = "Network connection error during token refresh";
            } else if (error.message) {
                errorDetail = error.message;
            }
            
            return {
                ...token,
                error: "RefreshAccessTokenError",
                errorDetail: errorDetail,
                refreshFailureCount: failureCount + 1,
            };
        }
    },
    async session({ session, token }: { session: Session; token: JWT }): Promise<Session> {
      console.debug("Session Callback: Start", { userId: token?.id, tokenJti: token?.jti });

      // エラーがあればセッションにエラー情報をセット
      if (token.error) {
        console.error("Session Callback: Token contains error", { error: token.error, errorDetail: token.errorDetail });
        session.error = token.error;
        session.errorDetail = token.errorDetail;
        
        // エラー時はデフォルト値を持つユーザーオブジェクトを設定
        session.user = {
          id: String(token.id ?? ''),
          name: null,
          email: null,
          image: null,
          role: '不明',
          status: 'error',
          isAdmin: false,
          isTeacher: false,
          isStudent: false,
          permissions: [],
          grade: undefined,
          prefecture: undefined,
          profile_image_url: undefined,
        };
        return session;
      }

      // トークンからセッションに情報をコピー
      if (token && session.user) {
        // role の正規化
        const normalizeRole = (roleInput: string | string[] | undefined): string => {
            if (Array.isArray(roleInput) && roleInput.length > 0) {
                return roleInput[0]; // 配列の場合、最初の要素を返す
            }
            if (typeof roleInput === 'string') {
                return roleInput;
            }
            return '不明';
        };
        
        const userRole = normalizeRole(token.role);
        const isAdmin = userRole === '管理者';
        const isTeacher = userRole === '教員';
        const isStudent = !isAdmin && !isTeacher;

        session.user = {
            ...session.user,
            id: String(token.id || token.sub),
            name: token.name ?? null,
            email: token.email ?? null,
            image: token.picture ?? null,
            role: userRole,
            isAdmin: isAdmin,
            isTeacher: isTeacher,
            isStudent: isStudent,
            status: (token.status as string | undefined) ?? 'pending',
            permissions: token.permissions as string[] | undefined,
            grade: token.grade as string | undefined,
            prefecture: token.prefecture as string | undefined,
            profile_image_url: token.profile_image_url as string | null | undefined,
            accessToken: token.accessToken as string | undefined,
            refreshToken: token.refreshToken as string | undefined,
            accessTokenExpires: token.accessTokenExpires as number | undefined
        };
        
        console.debug("Session Callback: Session populated", { userId: session.user.id, role: session.user.role });
      } else {
        console.warn("Session Callback: Token or session.user is missing");
        
        if (!session.user) {
             session.user = {
                id: String(token?.id ?? ''),
                name: null,
                email: null,
                image: null,
                role: '不明',
                status: 'error',
                isAdmin: false,
                isTeacher: false,
                isStudent: false,
                permissions: [],
                grade: undefined,
                prefecture: undefined,
                profile_image_url: undefined,
            };
        }
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
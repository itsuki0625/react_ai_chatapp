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
        // ★ 型アサーションを追加して email と password が string であることを保証
        const email = credentials.email as string;
        const password = credentials.password as string;
        console.debug('[Authorize] Attempting authorization for:', email); // DEBUG LOG

        // ★ サーバーサイド用の内部API URLを使用
        const apiUrl = `${process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/login`;
        // (INTERNAL_API_BASE_URL が未定義の場合のフォールバックとして NEXT_PUBLIC も残しておく)
        console.log('>>> [Authorize] Attempting to fetch internal API:', apiUrl); // ログも修正

        try {
          // データ形式を application/x-www-form-urlencoded に変更
          const body = new URLSearchParams();
          body.append('username', email);
          body.append('password', password);

          const response = await fetch(apiUrl, { // ★ apiUrl を使用
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, // ★ ヘッダーを変更
            body: body, // ★ URLSearchParams オブジェクトを送信
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
          console.debug("Authorize Callback: User object created", { userId: user.id, role: user.role, grade: user.grade, profile_image_url: user.profile_image_url }); // ★ ログ追加
          return user;
        } catch (error: any) { // ★ エラーの型を any にして詳細をログ出力
          console.error("[Authorize] Error in authorize callback:", error);
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
            return token; // Return early if valid
        }

        // 3. トークンが無効または有効期限が近い場合 (リフレッシュ実行)
        console.info("JWT Callback: Access token expired or nearing expiry, attempting refresh", { tokenId: token.jti });
        if (!token.refreshToken) {
            console.error("JWT Callback: No refresh token available, cannot refresh. Returning error.", { tokenId: token.jti });
            return { ...token, error: "RefreshAccessTokenError" };
        }

        try {
            console.debug("JWT Callback: Sending request to refresh token endpoint...");
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/refresh-token`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: token.refreshToken }),
                credentials: 'include',
            });

            const refreshedTokens = await response.json();

            if (!response.ok) {
                 console.error("JWT Callback: Failed to refresh token from API", { status: response.status, error: refreshedTokens });
                 const errorDetail = refreshedTokens?.detail || "Refresh token failed";
                 return { ...token, error: "RefreshAccessTokenError", errorDetail: errorDetail };
            }

            // リフレッシュ成功
            // --- リフレッシュ後のトークンもデコード ---
            let refreshedDecoded: DecodedToken = {};
            let refreshedRoles: string[] | undefined = undefined;
            let refreshedPermissions: string[] | undefined = undefined;
            try {
               refreshedDecoded = jwtDecode<DecodedToken>(refreshedTokens.access_token);
               refreshedRoles = refreshedDecoded.roles;
               refreshedPermissions = refreshedDecoded.permissions;
               console.debug("JWT Callback: Decoded refreshed token", { roles: refreshedRoles, permissions: refreshedPermissions });
            } catch(e) {
                console.error("JWT Callback: Failed to decode refreshed access token", e);
            }
            // --- ここまで追加 ---

            const defaultExpireMinutesOnRefresh = process.env.ACCESS_TOKEN_EXPIRE_MINUTES ? parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES) : 15;
            const newExpiresInSeconds = refreshedTokens.expires_in || defaultExpireMinutesOnRefresh * 60;
            const newExpiresAt = Math.floor(Date.now() / 1000) + newExpiresInSeconds;

            const refreshedTokenData: JWT = {
                ...token,
                accessToken: refreshedTokens.access_token,
                refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
                accessTokenExpires: newExpiresAt,
                // --- デコード結果を反映 ---
                role: refreshedRoles || token.role, // デコードした roles (配列) を優先、なければ以前の role
                permissions: refreshedPermissions || token.permissions, // デコードした permissions を優先
                // --- ここまで修正 ---
                profile_image_url: token.profile_image_url,
                iat: Math.floor(Date.now() / 1000),
                exp: newExpiresAt,
                jti: crypto.randomUUID(),
                error: undefined,
                errorDetail: undefined,
            };

            console.info("JWT Callback: Token refreshed successfully", { newTokenId: refreshedTokenData.jti, newRole: refreshedTokenData.role, profile_image_url: refreshedTokenData.profile_image_url }); // ★ ログ追加
            return refreshedTokenData;

        } catch (error: any) {
            console.error("JWT Callback: Catch block error during refresh token fetch", {
                errorMessage: error.message,
                errorDetails: error,
                refreshTokenUsed: token.refreshToken?.substring(0, 10) + '...'
            });
            return {
                ...token,
                error: "RefreshAccessTokenError",
                errorDetail: error.message || "Network error or failed to parse response",
            };
        }
    },
    async session({ session, token }: { session: Session; token: JWT }): Promise<Session> {
      console.debug("Session Callback: Start", { userId: token?.id, tokenJti: token?.jti, tokenRole: token.role }); // token.role をログに追加

      // エラーがあればセッションにエラー情報をセット (エラー詳細も)
      if (token.error) {
        console.error("Session Callback: Token contains error, propagating to session", { error: token.error, errorDetail: token.errorDetail });
        session.error = token.error;
        // @ts-ignore // 拡張エラー情報をセッションに追加
        session.errorDetail = token.errorDetail;
        // ★ エラー時は必須プロパティにデフォルト値を設定したオブジェクトにする
        session.user = {
          id: String(token.id ?? ''),
          name: null,
          email: null,
          image: null,
          role: '不明', // または適切なデフォルトロール
          status: 'error', // エラー状態を示すステータス
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
        session.user.id = typeof token.id === 'string' ? token.id : String(token.id ?? ''); 
        session.user.name = token.name ?? null; 
        session.user.email = token.email ?? null; 
        session.user.image = token.picture ?? null; 

        // --- ロール正規化処理 ---
        const normalizeRole = (roleInput: string | string[] | undefined): string => {
          if (Array.isArray(roleInput) && roleInput.length > 0) {
            return roleInput[0];
          } else if (typeof roleInput === 'string') {
            return roleInput;
          }
          return '生徒'; // デフォルトロール
        };
        const userRole = normalizeRole(token.role); // 正規化されたロールを取得
        session.user.role = userRole;
        // --- ここまで ---

        // --- isAdmin, isTeacher, isStudent の計算を追加 --- 
        session.user.isAdmin = userRole === '管理者';
        session.user.isTeacher = userRole === '教師';
        session.user.isStudent = userRole !== '管理者' && userRole !== '教師';
        // --- ここまで追加 ---

        session.user.status = token.status ?? 'pending'; 
        session.user.permissions = token.permissions as string[] | undefined;
        session.user.grade = token.grade as string | undefined; 
        session.user.prefecture = token.prefecture as string | undefined; 
        session.user.profile_image_url = token.profile_image_url as string | undefined;
        session.accessToken = token.accessToken as string | undefined; 
      } else {
        console.warn("Session Callback: Token or session.user is missing, cannot populate session user data.");
        // ★ エラー時と同様にデフォルト値を持つ user オブジェクトを設定
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

      console.debug("Session Callback: Session data populated", { userId: session.user?.id, role: session.user?.role, profile_image_url: session.user?.profile_image_url }); // ★ ログ追加
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
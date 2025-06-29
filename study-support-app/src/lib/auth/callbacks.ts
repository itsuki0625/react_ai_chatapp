import { JWT } from 'next-auth/jwt';
import { Session, Account, Profile } from 'next-auth';
import { AdapterUser } from 'next-auth/adapters';
import { ExtendedUser } from './types';
import { AUTH_CONFIG } from './config';
import { 
  normalizeRole, 
  getUserPermissions, 
  decodeAuthToken, 
  isTokenExpired,
  getErrorType 
} from './utils';
import { refreshToken } from './handlers';

/**
 * JWT コールバック関数
 */
export const jwtCallback = async ({
  token,
  user,
  account,
  profile,
  trigger,
  isNewUser,
  session,
}: {
  token: JWT;
  user?: ExtendedUser | AdapterUser;
  account?: Account | null;
  profile?: Profile;
  trigger?: "signIn" | "signUp" | "update";
  isNewUser?: boolean;
  session?: any;
}): Promise<JWT> => {
  console.debug("JWT Callback: Start", { 
    tokenId: token?.jti, 
    userId: user?.id, 
    trigger 
  });

  // update トリガーの場合 (例: useSession().update() 呼び出し)
  if (trigger === "update" && session) {
    console.debug("JWT Callback: Update trigger detected", { sessionData: session });
    // セッションデータでトークンを更新 (必要なフィールドのみ)
    token.name = session.user?.name;
    token.grade = session.user?.grade;
    token.prefecture = session.user?.prefecture;
    return token;
  }

  // 1. 初回ログイン時 (user オブジェクトが存在する場合)
  if (user && (trigger === 'signIn' || trigger === 'signUp')) {
    console.debug(`JWT Callback: ${trigger} trigger (user object present)`, { 
      userId: user.id 
    });
    
    const authUser = user as ExtendedUser;
    return await createInitialToken(token, authUser);
  }

  // 2. トークンがまだ有効な場合 (リフレッシュ不要)
  if (!isTokenExpired(token.accessTokenExpires, AUTH_CONFIG.tokenSafetyMargin)) {
    console.debug("JWT Callback: Access token is still valid", { tokenId: token.jti });
    return token;
  }

  // 3. トークンが無効または有効期限が近い場合 (リフレッシュ実行)
  console.info("JWT Callback: Access token expired or nearing expiry, attempting refresh", { 
    tokenId: token.jti 
  });

  return await handleTokenRefresh(token);
};

/**
 * 初回ログイン時のトークン作成
 */
const createInitialToken = async (token: JWT, authUser: ExtendedUser): Promise<JWT> => {
  // アクセストークンをデコードして情報を取得
  let tokenPermissions: string[] | undefined = undefined;
  let tokenRoles: string[] | undefined = undefined;

  if (authUser.accessToken) {
    const { roles, permissions } = decodeAuthToken(authUser.accessToken);
    tokenPermissions = permissions;
    tokenRoles = roles;
    console.debug("JWT Callback: Decoded access token", { 
      roles: tokenRoles, 
      permissions: tokenPermissions 
    });
  }

  const expiresAt = authUser.accessTokenExpires
    ? Math.floor(authUser.accessTokenExpires / 1000)
    : Math.floor(Date.now() / 1000) + AUTH_CONFIG.defaultExpireMinutes * 60;

  const extendedToken: JWT = {
    ...token,
    id: String(authUser.id),
    name: authUser.name,
    email: authUser.email,
    picture: authUser.image,
    profile_image_url: authUser.profile_image_url,
    role: tokenRoles || authUser.role,
    permissions: tokenPermissions,
    status: authUser.status,
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

  console.debug("JWT Callback: Initial token population", { 
    userId: extendedToken.id, 
    role: extendedToken.role, 
    profile_image_url: extendedToken.profile_image_url 
  });
  
  return extendedToken;
};

/**
 * トークンリフレッシュ処理
 */
const handleTokenRefresh = async (token: JWT): Promise<JWT> => {
  if (!token.refreshToken) {
    console.error("JWT Callback: No refresh token available", { tokenId: token.jti });
    return { ...token, error: "RefreshAccessTokenError" };
  }

  // 既にエラー状態の場合は再リフレッシュを試行しない（無限ループ防止）
  const failureCount = (token.refreshFailureCount as number) || 0;
  if (failureCount >= AUTH_CONFIG.maxRefreshAttempts) {
    console.error("JWT Callback: Too many refresh failures", { 
      tokenId: token.jti, 
      failureCount 
    });
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
    const refreshedTokens = await refreshToken(token.refreshToken as string);

    // リフレッシュ成功時の処理
    let refreshedRoles: string[] | undefined = undefined;
    let refreshedPermissions: string[] | undefined = undefined;
    
    if (refreshedTokens.access_token) {
      const { roles, permissions } = decodeAuthToken(refreshedTokens.access_token);
      refreshedRoles = roles;
      refreshedPermissions = permissions;
      console.debug("JWT Callback: Successfully decoded refreshed token");
    }

    const newExpiresInSeconds = refreshedTokens.expires_in || AUTH_CONFIG.defaultExpireMinutes * 60;
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

    console.info("JWT Callback: Token refreshed successfully", { 
      newTokenId: refreshedTokenData.jti 
    });
    return refreshedTokenData;

  } catch (error: any) {
    console.error("JWT Callback: Error during token refresh", {
      errorMessage: error.message,
      errorName: error.name,
    });

    // 463エラー（無効なリフレッシュトークン）の特別処理
    if (error.message.includes('INVALID_REFRESH_TOKEN')) {
      return { 
        ...token, 
        error: "RefreshAccessTokenError",
        errorDetail: "Refresh token is invalid or expired (463)",
        accessToken: undefined,
        refreshToken: undefined,
        accessTokenExpires: 0,
      };
    }
    
    const errorDetail = getErrorType(error);
    
    return {
      ...token,
      error: "RefreshAccessTokenError",
      errorDetail,
      refreshFailureCount: failureCount + 1,
    };
  }
};

/**
 * Session コールバック関数
 */
export const sessionCallback = async ({ 
  session, 
  token 
}: { 
  session: Session; 
  token: JWT 
}): Promise<Session> => {
  console.debug("Session Callback: Start", { 
    userId: token?.id, 
    tokenJti: token?.jti 
  });

  // エラーがあればセッションにエラー情報をセット
  if (token.error) {
    console.error("Session Callback: Token contains error", { 
      error: token.error, 
      errorDetail: token.errorDetail 
    });
    
    session.error = token.error;
    session.errorDetail = token.errorDetail;
    
    // エラー時はデフォルト値を持つユーザーオブジェクトを設定
    session.user = createErrorUserSession(token);
    return session;
  }

  // トークンからセッションに情報をコピー
  if (token && session.user) {
    session.user = createUserSession(token);
    console.debug("Session Callback: Session populated", { 
      userId: session.user.id, 
      role: session.user.role 
    });
  } else {
    console.warn("Session Callback: Token or session.user is missing");
    session.user = createErrorUserSession(token);
  }

  return session;
};

/**
 * エラー時のユーザーセッション作成
 */
const createErrorUserSession = (token: JWT) => ({
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
});

/**
 * 正常時のユーザーセッション作成
 */
const createUserSession = (token: JWT) => {
  const userRole = normalizeRole(token.role);
  const { isAdmin, isTeacher, isStudent } = getUserPermissions(userRole);

  return {
    id: String(token.id || token.sub),
    name: token.name ?? null,
    email: token.email ?? null,
    image: token.picture ?? null,
    role: userRole,
    isAdmin,
    isTeacher,
    isStudent,
    status: (token.status as string | undefined) ?? 'pending',
    permissions: token.permissions as string[] | undefined,
    grade: token.grade as string | undefined,
    prefecture: token.prefecture as string | undefined,
    profile_image_url: token.profile_image_url as string | null | undefined,
    accessToken: token.accessToken as string | undefined,
    refreshToken: token.refreshToken as string | undefined,
    accessTokenExpires: token.accessTokenExpires as number | undefined
  };
}; 
import { JWT } from 'next-auth/jwt';
import { Session, Account, Profile } from 'next-auth';
import { AdapterUser } from 'next-auth/adapters';
import { ExtendedUser, DecodedToken } from './types';
import { AUTH_CONFIG } from './config';
import { isTokenExpired } from './utils';
import { refreshToken } from './handlers';

/**
 * JWT コールバック - 簡素化版
 */
export const jwtCallback = async ({
  token,
  user,
  account,
  profile,
  trigger,
  session,
}: {
  token: JWT;
  user?: ExtendedUser | AdapterUser;
  account?: Account | null;
  profile?: Profile;
  trigger?: "signIn" | "signUp" | "update";
  session?: any;
}): Promise<JWT> => {
  
  // プロフィール更新時
  if (trigger === "update" && session) {
    return {
      ...token,
      name: session.user?.name || token.name,
      grade: session.user?.grade || token.grade,
      prefecture: session.user?.prefecture || token.prefecture,
    };
  }

  // 初回ログイン時
  if (user && (trigger === 'signIn' || trigger === 'signUp')) {
    const authUser = user as ExtendedUser;
    const expiresAt = authUser.accessTokenExpires
      ? Math.floor(authUser.accessTokenExpires / 1000)
      : Math.floor(Date.now() / 1000) + AUTH_CONFIG.defaultExpireMinutes * 60;

    return {
      ...token,
      id: String(authUser.id),
      name: authUser.name,
      email: authUser.email,
      picture: authUser.image,
      profile_image_url: authUser.profile_image_url,
      role: authUser.role,
      status: authUser.status,
      permissions: authUser.permissions, // 権限情報を追加
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
  }

  // トークンが有効な場合はそのまま返す
  if (!isTokenExpired(token.accessTokenExpires, AUTH_CONFIG.tokenSafetyMargin)) {
    return token;
  }

  // トークンリフレッシュ
  if (!token.refreshToken) {
    return { ...token, error: "RefreshAccessTokenError" };
  }

  try {
    const refreshedTokens = await refreshToken(token.refreshToken as string);
    const newExpiresAt = Math.floor(Date.now() / 1000) + (refreshedTokens.expires_in || AUTH_CONFIG.defaultExpireMinutes * 60);

    // 新しいアクセストークンから権限情報を抽出
    let updatedPermissions = token.permissions; // 既存の権限をフォールバックとして保持
    let updatedRole = token.role;
    let updatedStatus = token.status;
    
    try {
      const tokenParts = refreshedTokens.access_token.split('.');
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1])) as DecodedToken;
        updatedPermissions = payload.permissions || token.permissions;
        updatedRole = payload.roles?.[0] || token.role;
        updatedStatus = payload.status || token.status;
        console.log('[JWT Refresh] Updated permissions from new token:', updatedPermissions);
      }
    } catch (decodeError) {
      console.warn('[JWT Refresh] Failed to extract permissions from refreshed token:', decodeError);
    }

    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
      accessTokenExpires: newExpiresAt,
      permissions: updatedPermissions, // 更新された権限情報を設定
      role: updatedRole, // 更新されたロール情報を設定
      status: updatedStatus, // 更新されたステータス情報を設定
      iat: Math.floor(Date.now() / 1000),
      exp: newExpiresAt,
      jti: crypto.randomUUID(),
      error: undefined,
    };
  } catch (error: any) {
    console.error("トークンリフレッシュに失敗:", error.message);
    return { 
      ...token, 
      error: "RefreshAccessTokenError",
      accessToken: undefined,
      refreshToken: undefined,
      accessTokenExpires: 0,
    };
  }
};

/**
 * Session コールバック - 簡素化版
 */
export const sessionCallback = async ({ 
  session, 
  token 
}: { 
  session: Session; 
  token: JWT 
}): Promise<Session> => {
  
  // エラー時の処理
  if (token.error) {
    session.error = token.error;
    session.user = {
      id: String(token.id || ''),
      name: token.name || '',
      email: token.email || '',
      image: null,
      role: '不明',
      status: 'error',
      isAdmin: false,
      isTeacher: false,
      isStudent: false,
      accessToken: undefined,
    };
    return session;
  }

  // 正常時のセッション作成
  if (token && session.user) {
    const role = Array.isArray(token.role) ? token.role[0] || '不明' : token.role || '不明';
    const status = token.status || 'active';
    const permissions = Array.isArray(token.permissions) ? token.permissions : [];
    
    console.log('[Session Callback] Token permissions:', token.permissions);
    console.log('[Session Callback] Processed permissions:', permissions);
    console.log('[Session Callback] User role:', role, 'Status:', status);
    
    session.user = {
      id: String(token.id),
      name: token.name,
      email: token.email,
      image: token.picture,
      profile_image_url: token.profile_image_url,
      role: role,
      status: status,
      permissions: permissions, // 権限情報を追加
      isAdmin: role === '管理者',
      isTeacher: token.isTeacher || role === '教員',
      isStudent: role !== '管理者' && role !== '教員',
      grade: token.grade,
      prefecture: token.prefecture,
      accessToken: token.accessToken,
    };
    
    console.log('[Session Callback] Final session user permissions:', session.user.permissions);
  }

  return session;
}; 
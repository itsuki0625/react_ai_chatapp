import { 
  Credentials, 
  ExtendedUser, 
  LoginResponse, 
  RefreshTokenResponse 
} from './types';
import { 
  getAuthApiUrl, 
  AUTH_ENDPOINTS, 
  AUTH_CONFIG 
} from './config';
import { 
  createAuthHeaders, 
  createFormData, 
  getErrorType 
} from './utils';

/**
 * ユーザー認証を行うハンドラー
 */
export const authorizeUser = async (credentials: Credentials): Promise<ExtendedUser | null> => {
  console.log('=== NEXTAUTH AUTHORIZE START ===');
  console.log('受信した認証情報:', credentials);

  if (!credentials?.email || !credentials?.password) {
    console.warn('[Authorize] Missing email or password');
    return null;
  }

  const { email, password } = credentials;
  console.debug('[Authorize] Attempting authorization for:', email);

  const apiUrl = `${getAuthApiUrl()}${AUTH_ENDPOINTS.login}`;
  console.log('>>> [Authorize] API URL:', apiUrl);

  try {
    console.log('[Authorize] リクエスト準備中...');
    
    const body = createFormData(email, password);
    console.log('[Authorize] リクエストボディ準備完了');
    console.log('[Authorize] APIリクエスト送信中...');

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: createAuthHeaders('application/x-www-form-urlencoded'),
      body: body,
      signal: AbortSignal.timeout(AUTH_CONFIG.requestTimeout),
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
      console.error(`[Authorize] Response headers:`, Object.fromEntries(response.headers.entries()));
      throw new Error(errorData.detail || `Authentication failed (${response.status})`);
    }

    const data: LoginResponse = await response.json();
    console.log('[Authorize] API login successful, data received:', data);

    if (!data || !data.token || !data.token.access_token || !data.user) {
      console.error('[Authorize] API response missing required fields (token or user)');
      throw new Error('Invalid API response format');
    }

    // BackendのUser型とToken型をNextAuthのUser型にマッピング
    const user: ExtendedUser = {
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

    console.debug("Authorize Callback: User object created", { 
      userId: user.id, 
      role: user.role 
    });
    console.log('=== NEXTAUTH AUTHORIZE SUCCESS ===');
    return user;

  } catch (error: any) {
    console.error("=== NEXTAUTH AUTHORIZE ERROR ===");
    console.error("[Authorize] Error in authorize callback:", error);
    
    const errorType = getErrorType(error);
    console.error("[Authorize] Error type:", errorType);
    
    if (error.cause) {
      console.error("[Authorize] Error Cause:", error.cause);
    }
    return null;
  }
};

/**
 * トークンをリフレッシュするハンドラー
 */
export const refreshToken = async (refreshTokenValue: string): Promise<RefreshTokenResponse> => {
  console.debug("Token refresh: Attempting to refresh token...");
  
  const refreshUrl = `${getAuthApiUrl()}${AUTH_ENDPOINTS.refresh}`;
  
  const response = await fetch(refreshUrl, {
    method: "POST",
    headers: createAuthHeaders(),
    body: JSON.stringify({ refresh_token: refreshTokenValue }),
    credentials: 'include',
    signal: AbortSignal.timeout(AUTH_CONFIG.requestTimeout),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error("Token refresh: Failed to refresh token", { 
      status: response.status, 
      error: errorData
    });
    
    // 463エラー（トークン無効）の場合は特別な処理
    if (response.status === 463) {
      console.warn("Token refresh: 463 error - refresh token invalid");
      throw new Error(`INVALID_REFRESH_TOKEN:${response.status}`);
    }
    
    throw new Error(errorData?.detail || `Refresh failed (${response.status})`);
  }

  const refreshedTokens: RefreshTokenResponse = await response.json();
  console.info("Token refresh: Token refreshed successfully");
  
  return refreshedTokens;
}; 
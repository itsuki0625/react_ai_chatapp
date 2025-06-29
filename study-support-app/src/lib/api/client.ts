import axios, { AxiosRequestHeaders } from 'axios';
import { API_BASE_URL } from '@/lib/config';
import { getSession } from 'next-auth/react';

// セッション型定義
interface SessionWithToken {
  accessToken?: string;
  user?: {
    accessToken?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

// 統一されたAPIクライアント
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
  timeout: 30000,
});

// リクエストインターセプター - 認証トークン自動付与
apiClient.interceptors.request.use(
  async (config) => {
    // クライアントサイドでのみ実行
    if (typeof window !== 'undefined') {
      try {
        const session = await getSession() as SessionWithToken | null;
        console.log('[ApiClient] Session fetched:', session);

        const accessToken = session?.accessToken || session?.user?.accessToken;

        if (accessToken) {
          if (!config.headers) {
            config.headers = {} as AxiosRequestHeaders;
          }
          config.headers.Authorization = `Bearer ${accessToken}`;
          console.log('[ApiClient] Authorization header added');
        } else {
          console.warn('[ApiClient] No access token found in session');
          if (config.url) {
            console.warn(`[ApiClient] Request to ${config.url} without token`);
          }
        }
      } catch (error) {
        console.error('[ApiClient] Failed to get session:', error);
      }
    }
    return config;
  },
  (error) => {
    console.error('[ApiClient] Request Error:', error);
    return Promise.reject(error);
  }
);

// レスポンスインターセプター - 認証エラー自動処理
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      console.error('[ApiClient] 401 Unauthorized - Session expired');
      
      // クライアントサイドでの認証エラー処理
      if (typeof window !== 'undefined') {
        const authErrorEvent = new CustomEvent('auth-error', {
          detail: {
            status: 401,
            error: 'Unauthorized',
            originalError: error
          }
        });
        window.dispatchEvent(authErrorEvent);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient; 
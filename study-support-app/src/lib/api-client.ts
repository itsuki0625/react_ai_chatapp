import axios from 'axios';
import { API_BASE_URL } from '@/lib/config';
import { auth } from '@/auth';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // 重要: CORSでクッキーを送信するために必要
  headers: {
    'Content-Type': 'application/json',
  },
});

// リクエストインターセプター - サーバーコンポーネント用のセッション取得は事前に行う
// 非同期処理はインターセプター内で実行せず、必要なセッションは別途取得
apiClient.interceptors.request.use(
  (config) => {
    try {
      // JWTは自動的にクッキーで送信されるため、
      // クライアントサイドではAuthorizationヘッダーを追加する必要はない
      return config;
    } catch (error) {
      console.error('リクエストインターセプターエラー:', error);
      return config;
    }
  },
  (error) => Promise.reject(error)
);

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 認証エラー時の処理
      // リフレッシュトークンの使用は auth.ts で行われるため
      // ここではログインページへのリダイレクトのみ
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// サーバーコンポーネント用のAuthorizationヘッダー付きリクエスト関数
export const withAuth = async (config: any) => {
  if (typeof window === 'undefined') {
    const session = await auth();
    if (session?.accessToken) {
      if (!config.headers) {
        config.headers = {};
      }
      config.headers.Authorization = `Bearer ${session.accessToken}`;
    }
  }
  return config;
}; 
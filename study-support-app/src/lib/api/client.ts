import axios, { AxiosRequestConfig, InternalAxiosRequestConfig, AxiosRequestHeaders } from 'axios';
import { API_BASE_URL } from '@/lib/config'; // config からインポート
import { getSession } from 'next-auth/react'; // getSession をインポート

// APIのベースURLを直接指定する代わりに config から読み込む
// const baseURL = 'http://localhost:5050/api/v1'; 

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`, // API_BASE_URL に /api/v1 を追加
  withCredentials: true, // 参照ファイルに合わせて追加
  headers: {
    'Content-Type': 'application/json',
  },
});

// 認証トークンをヘッダーに付与するインターセプター
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig | Promise<InternalAxiosRequestConfig> => {
    config.headers = config.headers || {} as AxiosRequestHeaders;

    if (typeof window !== 'undefined') {
      // getSession は非同期なので、即座に config を返すことは難しい
      // Promise を返すパターンで実装する
      return getSession().then(session => {
        const accessToken = (session as any)?.accessToken || (session?.user as any)?.accessToken;
        if (accessToken) {
          config.headers.Authorization = `Bearer ${accessToken}`;
          console.log("Authorization header set with token from session.");
        } else {
          console.log("No access token found in session.");
        }
        return config; // Promise 内で config を返す
      }).catch(error => {
        console.error('Failed to get session or attach token:', error);
        return config; // エラー時も config を返す (またはエラーを再スロー)
      });
    }
    // サーバーサイドなど、window がない場合はそのまま config を返す
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター (例: 401エラー時のリダイレクト)
/*
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // ログインページへリダイレクトなどの処理
      console.error("Unauthorized, redirecting to login...");
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
*/ 
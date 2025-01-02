import axios from 'axios';
import { API_BASE_URL } from '@/lib/config';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // 重要: CORSでクッキーを送信するために必要
  headers: {
    'Content-Type': 'application/json',
  },
});

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 認証エラー時の処理
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
); 
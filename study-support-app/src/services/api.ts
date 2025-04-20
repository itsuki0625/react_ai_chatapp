import { Content } from '@/types/content';
import axios from 'axios';
import { getSession } from 'next-auth/react';

// ブラウザ環境かサーバー環境かによって適切なAPIのベースURLを取得
const getApiBaseUrl = () => {
  return typeof window !== 'undefined'
    ? process.env.NEXT_PUBLIC_BROWSER_API_URL || 'http://localhost:5050'
    : process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:5050';
};

// 認証情報付きのaxios設定を取得
const getAxiosConfig = async (requireAuth = true) => {
  const config: {
    withCredentials: boolean;
    headers: Record<string, string>;
  } = {
    withCredentials: true, // クッキーを含める
    headers: {}
  };

  // 認証が必要な場合はセッションを取得
  if (requireAuth && typeof window !== 'undefined') {
    try {
      const session = await getSession();
      if (session) {
        // セッショントークンがあれば追加
        config.headers['X-Session-Token'] = 'true';
        
        // ユーザー情報をヘッダーに追加（バックエンドでの認証に使用）
        if (session.user?.email) {
          config.headers['X-User-Email'] = session.user.email;
        }
        if (session.user?.name) {
          config.headers['X-User-Name'] = session.user.name;
        }
      }
    } catch (error) {
      console.error('セッション取得エラー:', error);
    }
  }

  return config;
};

// 既存のコードに追加
export const contentAPI = {
  getContents: async (contentType?: string) => {
    try {
      const params = contentType ? `?content_type=${contentType}` : '';
      const config = await getAxiosConfig(true);
      const response = await axios.get(
        `${getApiBaseUrl()}/api/v1/contents/${params}`,
        config
      );
      return response.data;
    } catch (error) {
      console.error('コンテンツの取得に失敗しました:', error);
      throw new Error('Failed to fetch contents');
    }
  },

  getContent: async (id: string) => {
    try {
      const config = await getAxiosConfig(true);
      const response = await axios.get(
        `${getApiBaseUrl()}/api/v1/contents/${id}`,
        config
      );
      return response.data;
    } catch (error) {
      console.error(`コンテンツID: ${id} の取得に失敗しました:`, error);
      throw new Error('Failed to fetch content');
    }
  },

  createContent: async (content: Omit<Content, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      const config = await getAxiosConfig(true);
      const response = await axios.post(
        `${getApiBaseUrl()}/api/v1/contents/`,
        content,
        config
      );
      return response.data;
    } catch (error) {
      console.error('コンテンツの作成に失敗しました:', error);
      throw new Error('Failed to create content');
    }
  },

  updateContent: async (id: string, content: Partial<Content>) => {
    try {
      const config = await getAxiosConfig(true);
      const response = await axios.put(
        `${getApiBaseUrl()}/api/v1/contents/${id}`,
        content,
        config
      );
      return response.data;
    } catch (error) {
      console.error(`コンテンツID: ${id} の更新に失敗しました:`, error);
      throw new Error('Failed to update content');
    }
  },

  deleteContent: async (id: string) => {
    try {
      const config = await getAxiosConfig(true);
      const response = await axios.delete(
        `${getApiBaseUrl()}/api/v1/contents/${id}`,
        config
      );
      return response.data;
    } catch (error) {
      console.error(`コンテンツID: ${id} の削除に失敗しました:`, error);
      throw new Error('Failed to delete content');
    }
  },
}; 
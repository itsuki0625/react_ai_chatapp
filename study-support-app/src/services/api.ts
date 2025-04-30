import { Content } from '@/types/content';
import { getSession } from 'next-auth/react';
import { fetchWithAuth } from '@/lib/fetchWithAuth';

// ブラウザ環境かサーバー環境かによって適切なAPIのベースURLを取得
export const getApiBaseUrl = () => {
  return typeof window !== 'undefined'
    ? process.env.NEXT_PUBLIC_BROWSER_API_URL || 'http://localhost:5050'
    : process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:5050';
};

// 認証付き・未認証リクエストの共通設定を取得します
export const getAxiosConfig = async (requireAuth = true) => {
  const config: { withCredentials: boolean; headers: Record<string, string> } = {
    withCredentials: true,
    headers: {}
  };
  if (requireAuth && typeof window !== 'undefined') {
    try {
      const session = await getSession();
      if (session?.accessToken) {
        config.headers['Authorization'] = `Bearer ${session.accessToken}`;
      } else {
        console.warn('API Service: 認証トークンが見つかりません');
      }
    } catch (error) {
      console.error('API Service: セッション取得エラー', error);
    }
  }
  return config;
};

// 既存のコードに追加
export const contentAPI = {
  getContents: async (contentType?: string): Promise<Content[]> => {
    try {
      const params = contentType ? `?content_type=${contentType}` : '';
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/contents/${params}`
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (!Array.isArray(data)) {
        console.error('Invalid data format received for contents', data);
        throw new Error('Invalid data format received');
      }
      return data as Content[];
    } catch (error) {
      console.error('コンテンツの取得に失敗しました:', error);
      throw error;
    }
  },

  getContent: async (id: string): Promise<Content> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/contents/${id}`
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      return await response.json() as Content;
    } catch (error) {
      console.error(`コンテンツID: ${id} の取得に失敗しました:`, error);
      throw error;
    }
  },

  createContent: async (content: Omit<Content, 'id' | 'created_at' | 'updated_at'>): Promise<Content> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/contents/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(content),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      return await response.json() as Content;
    } catch (error) {
      console.error('コンテンツの作成に失敗しました:', error);
      throw error;
    }
  },

  updateContent: async (id: string, content: Partial<Content>): Promise<Content> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/contents/${id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(content),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      return await response.json() as Content;
    } catch (error) {
      console.error(`コンテンツID: ${id} の更新に失敗しました:`, error);
      throw error;
    }
  },

  deleteContent: async (id: string): Promise<void> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/contents/${id}`,
        {
          method: 'DELETE',
        }
      );
      if (!response.ok && response.status !== 204) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error(`コンテンツID: ${id} の削除に失敗しました:`, error);
      throw error;
    }
  },
}; 
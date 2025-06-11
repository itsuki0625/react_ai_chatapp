import { Content } from '@/types/content';
import { getSession } from 'next-auth/react';
import { fetchWithAuth } from '@/lib/fetchWithAuth';
import { ContentCategoryInfo, ContentCategoryCreate, ContentCategoryUpdate } from '@/types/content';

// ブラウザ環境かサーバー環境かによって適切なAPIのベースURLを取得
export const getApiBaseUrl = () => {
  return typeof window !== 'undefined'
    ? '' // ブラウザ側では相対パス（Next.jsのrewritesを使用）
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
      if (session?.user?.accessToken) {
        config.headers['Authorization'] = `Bearer ${session.user.accessToken}`;
      } else if (session) {
        config.headers['X-Session-Token'] = 'true';
        if (typeof session.user?.email === 'string') {
          config.headers['X-User-Email'] = session.user.email;
        }
        if (typeof session.user?.name === 'string') {
          config.headers['X-User-Name'] = encodeURIComponent(session.user.name);
        }
        console.warn('API Service: Session found but no accessToken. Using custom headers as fallback.');
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

  getAllContentCategories: async (params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<ContentCategoryInfo[]> => {
    try {
      const queryParams = new URLSearchParams();
      if (params?.skip !== undefined) queryParams.append('skip', String(params.skip));
      if (params?.limit !== undefined) queryParams.append('limit', String(params.limit));
      if (params?.is_active !== undefined) queryParams.append('is_active', String(params.is_active));
      const queryString = queryParams.toString();
      
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/content-categories/${queryString ? '?' + queryString : ''}`
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (!Array.isArray(data)) {
        console.error('Invalid data format received for content categories (admin)', data);
        throw new Error('Invalid data format received for content categories (admin)');
      }
      return data as ContentCategoryInfo[];
    } catch (error) {
      console.error('コンテンツカテゴリー(管理用)の取得に失敗しました:', error);
      throw error;
    }
  },

  getContentCategoryById: async (id: string): Promise<ContentCategoryInfo> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/content-categories/${id}`
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      return await response.json() as ContentCategoryInfo;
    } catch (error) {
      console.error(`コンテンツカテゴリーID: ${id} の取得に失敗しました:`, error);
      throw error;
    }
  },

  createContentCategory: async (categoryData: ContentCategoryCreate): Promise<ContentCategoryInfo> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/content-categories/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(categoryData),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      return await response.json() as ContentCategoryInfo;
    } catch (error) {
      console.error('コンテンツカテゴリーの作成に失敗しました:', error);
      throw error;
    }
  },

  updateContentCategory: async (id: string, categoryData: ContentCategoryUpdate): Promise<ContentCategoryInfo> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/content-categories/${id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(categoryData),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      return await response.json() as ContentCategoryInfo;
    } catch (error) {
      console.error(`コンテンツカテゴリーID: ${id} の更新に失敗しました:`, error);
      throw error;
    }
  },

  deleteContentCategory: async (id: string): Promise<void> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/content-categories/${id}`,
        {
          method: 'DELETE',
        }
      );
      if (!response.ok && response.status !== 204) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error(`コンテンツカテゴリーID: ${id} の削除に失敗しました:`, error);
      throw error;
    }
  },

  getContentCategories: async (): Promise<ContentCategoryInfo[]> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/contents/categories/`
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (!Array.isArray(data)) {
        console.error('Invalid data format received for content categories', data);
        throw new Error('Invalid data format received for content categories');
      }
      return data as ContentCategoryInfo[];
    } catch (error) {
      console.error('コンテンツカテゴリーの取得に失敗しました:', error);
      throw error;
    }
  },
};

// チャット関連のAPI機能
export const chatAPI = {
  generateSessionTitle: async (sessionId: string): Promise<{ title: string; session_id: string }> => {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/api/v1/chat/sessions/${sessionId}/generate-title`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`セッションID: ${sessionId} のタイトル生成に失敗しました:`, error);
      throw error;
    }
  },
}; 
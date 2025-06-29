import { Content } from '@/types/content';
import { ContentCategoryInfo, ContentCategoryCreate, ContentCategoryUpdate } from '@/types/content';
import { apiClient } from '../client';

// コンテンツ関連のAPI機能
export const contentAPI = {
  getContents: async (contentType?: string): Promise<Content[]> => {
    try {
      const params = contentType ? `?content_type=${contentType}` : '';
      const response = await apiClient.get(`/api/v1/contents/${params}`);
      if (!Array.isArray(response.data)) {
        console.error('Invalid data format received for contents', response.data);
        throw new Error('Invalid data format received');
      }
      return response.data as Content[];
    } catch (error) {
      console.error('コンテンツの取得に失敗しました:', error);
      throw error;
    }
  },

  getContent: async (id: string): Promise<Content> => {
    try {
      const response = await apiClient.get(`/api/v1/contents/${id}`);
      return response.data as Content;
    } catch (error) {
      console.error(`コンテンツID: ${id} の取得に失敗しました:`, error);
      throw error;
    }
  },

  createContent: async (content: Omit<Content, 'id' | 'created_at' | 'updated_at'>): Promise<Content> => {
    try {
      const response = await apiClient.post('/api/v1/contents/', content);
      return response.data as Content;
    } catch (error) {
      console.error('コンテンツの作成に失敗しました:', error);
      throw error;
    }
  },

  updateContent: async (id: string, content: Partial<Content>): Promise<Content> => {
    try {
      const response = await apiClient.put(`/api/v1/contents/${id}`, content);
      return response.data as Content;
    } catch (error) {
      console.error(`コンテンツID: ${id} の更新に失敗しました:`, error);
      throw error;
    }
  },

  deleteContent: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/api/v1/contents/${id}`);
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
      
      const response = await apiClient.get(`/api/v1/content-categories/${queryString ? '?' + queryString : ''}`);
      const data = response.data;
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
      const response = await apiClient.get(`/api/v1/content-categories/${id}`);
      return response.data as ContentCategoryInfo;
    } catch (error) {
      console.error(`コンテンツカテゴリーID: ${id} の取得に失敗しました:`, error);
      throw error;
    }
  },

  createContentCategory: async (categoryData: ContentCategoryCreate): Promise<ContentCategoryInfo> => {
    try {
      const response = await apiClient.post('/api/v1/content-categories/', categoryData);
      return response.data as ContentCategoryInfo;
    } catch (error) {
      console.error('コンテンツカテゴリーの作成に失敗しました:', error);
      throw error;
    }
  },

  updateContentCategory: async (id: string, categoryData: ContentCategoryUpdate): Promise<ContentCategoryInfo> => {
    try {
      const response = await apiClient.put(`/api/v1/content-categories/${id}`, categoryData);
      return response.data as ContentCategoryInfo;
    } catch (error) {
      console.error(`コンテンツカテゴリーID: ${id} の更新に失敗しました:`, error);
      throw error;
    }
  },

  deleteContentCategory: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/api/v1/content-categories/${id}`);
    } catch (error) {
      console.error(`コンテンツカテゴリーID: ${id} の削除に失敗しました:`, error);
      throw error;
    }
  },

  getContentCategories: async (): Promise<ContentCategoryInfo[]> => {
    try {
      const response = await apiClient.get('/api/v1/contents/categories/');
      const data = response.data;
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
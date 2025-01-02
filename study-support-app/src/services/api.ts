import { Content } from '@/types/content';

// 既存のコードに追加
export const contentAPI = {
  getContents: async (contentType?: string) => {
    const params = contentType ? `?content_type=${contentType}` : '';
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/contents/${params}`, {
      credentials: 'include',
    });
    if (!response.ok) throw new Error('Failed to fetch contents');
    return response.json();
  },

  getContent: async (id: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/contents/${id}`, {
      credentials: 'include',
    });
    if (!response.ok) throw new Error('Failed to fetch content');
    return response.json();
  },

  createContent: async (content: Omit<Content, 'id' | 'created_at' | 'updated_at'>) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/contents/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(content),
    });
    if (!response.ok) throw new Error('Failed to create content');
    return response.json();
  },

  updateContent: async (id: string, content: Partial<Content>) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/contents/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(content),
    });
    if (!response.ok) throw new Error('Failed to update content');
    return response.json();
  },

  deleteContent: async (id: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/contents/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!response.ok) throw new Error('Failed to delete content');
    return response.json();
  },
}; 
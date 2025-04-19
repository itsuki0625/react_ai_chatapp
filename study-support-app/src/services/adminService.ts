import axios from 'axios';
import { CampaignCode } from '@/types/subscription';

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL + "/api/v1" || 'http://localhost:5050/api/v1';

// Stripe商品の型定義
export interface StripeProduct {
  id: string;
  name: string;
  description: string | null;
  active: boolean;
  images: string[];
  created: number;
  updated: number;
}

// Stripe価格の型定義
export interface StripePrice {
  id: string;
  product: string;
  product_name?: string;
  active: boolean;
  currency: string;
  unit_amount: number;
  type: 'one_time' | 'recurring';
  recurring?: {
    interval: 'day' | 'week' | 'month' | 'year';
    interval_count: number;
  };
  created: number;
}

export const adminService = {
  // Stripe商品一覧取得
  getProducts: async (): Promise<StripeProduct[]> => {
    try {
      const response = await axios.get<StripeProduct[]>(`${API_URL}/admin/products`, {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error('商品の取得に失敗しました:', error);
      throw error;
    }
  },

  // Stripe商品作成
  createProduct: async (productData: {
    name: string;
    description?: string;
    active?: boolean;
  }): Promise<StripeProduct> => {
    const response = await axios.post<StripeProduct>(`${API_URL}/admin/products`, productData, {
      withCredentials: true
    });
    return response.data;
  },

  // Stripe商品削除
  deleteProduct: async (productId: string): Promise<void> => {
    await axios.delete(`${API_URL}/admin/products/${productId}`, {
      withCredentials: true
    });
  },

  // Stripe価格一覧取得
  getPrices: async (): Promise<StripePrice[]> => {
    const response = await axios.get<StripePrice[]>(`${API_URL}/admin/prices`, {
      withCredentials: true
    });
    return response.data;
  },

  // Stripe価格作成
  createPrice: async (priceData: {
    product: string;
    unit_amount: number;
    currency: string;
    recurring?: {
      interval: 'day' | 'week' | 'month' | 'year';
      interval_count: number;
    };
  }): Promise<StripePrice> => {
    const response = await axios.post<StripePrice>(`${API_URL}/admin/prices`, priceData, {
      withCredentials: true
    });
    return response.data;
  },

  // Stripe価格削除
  deletePrice: async (priceId: string): Promise<void> => {
    await axios.delete(`${API_URL}/admin/prices/${priceId}`, {
      withCredentials: true
    });
  },

  // キャンペーンコード一覧取得
  getCampaignCodes: async (skip = 0, limit = 20, ownerId?: string): Promise<CampaignCode[]> => {
    const params: any = { skip, limit };
    if (ownerId) params.owner_id = ownerId;
    
    const response = await axios.get<CampaignCode[]>(`${API_URL}/admin/campaign-codes`, {
      params,
      withCredentials: true
    });
    return response.data;
  },

  // キャンペーンコード作成
  createCampaignCode: async (campaignCode: {
    code: string;
    description?: string;
    owner_id?: string;
    discount_type: 'percentage' | 'fixed';
    discount_value: number;
    max_uses?: number;
    valid_from?: string;
    valid_until?: string;
    is_active?: boolean;
  }): Promise<CampaignCode> => {
    const response = await axios.post<CampaignCode>(`${API_URL}/admin/campaign-codes`, campaignCode, {
      withCredentials: true
    });
    return response.data;
  },

  // キャンペーンコード削除
  deleteCampaignCode: async (campaignCodeId: string): Promise<void> => {
    await axios.delete(`${API_URL}/admin/campaign-codes/${campaignCodeId}`, {
      withCredentials: true
    });
  }
}; 
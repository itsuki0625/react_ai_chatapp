import { apiClient } from './client'; // axiosクライアントなどを想定
import { 
    StripeProductWithPricesResponse, StripeProductCreate, StripeProductUpdate, StripeProductResponse,
    StripePriceUpdate, StripePriceResponse // 価格関連の型を追加
} from '@/types/stripe'; // 型定義
import { 
    DiscountTypeResponse, DiscountTypeCreate, DiscountTypeUpdate // ★ この行を追加
} from '@/types/subscription'; // ★ この行を追加

// 商品一覧取得 API
export const fetchProducts = async (): Promise<StripeProductWithPricesResponse[]> => {
  const response = await apiClient.get<StripeProductWithPricesResponse[]>('/admin/products');
  return response.data;
};

// 商品作成 API
export const createProduct = async (data: StripeProductCreate): Promise<StripeProductResponse> => {
  const response = await apiClient.post<StripeProductResponse>('/admin/products', data);
  return response.data;
};

// 商品更新 API
export const updateProduct = async (productId: string, data: StripeProductUpdate): Promise<StripeProductResponse> => {
  const response = await apiClient.put<StripeProductResponse>(`/admin/products/${productId}`, data);
  return response.data;
};

// 商品アーカイブ (非アクティブ化) API
export const archiveProduct = async (productId: string): Promise<StripeProductResponse> => {
  // DELETEリクエストだが、レスポンスボディにアーカイブされた商品情報が含まれる想定
  const response = await apiClient.delete<StripeProductResponse>(`/admin/products/${productId}`);
  return response.data;
};

// 価格更新 API
export const updatePrice = async (priceId: string, data: StripePriceUpdate): Promise<StripePriceResponse> => {
  const response = await apiClient.put<StripePriceResponse>(`/admin/prices/${priceId}`, data);
  return response.data;
};

// TODO: 商品更新、アーカイブ用のAPI関数もここに追加
// export const updateProduct = async (productId: string, data: ...) => { ... };
// export const archiveProduct = async (productId: string) => { ... };
// TODO: 価格作成、アーカイブ用のAPI関数もここに追加 

// --- Discount Type API --- //

// 割引タイプ一覧取得 API
export const fetchDiscountTypes = async (): Promise<DiscountTypeResponse[]> => {
    const response = await apiClient.get<DiscountTypeResponse[]>('/admin/discount-types');
    return response.data;
};

// 割引タイプ作成 API
export const createDiscountType = async (data: DiscountTypeCreate): Promise<DiscountTypeResponse> => {
    const response = await apiClient.post<DiscountTypeResponse>('/admin/discount-types', data);
    return response.data;
};

// 割引タイプ更新 API
export const updateDiscountType = async (discountTypeId: string, data: DiscountTypeUpdate): Promise<DiscountTypeResponse> => {
    const response = await apiClient.put<DiscountTypeResponse>(`/admin/discount-types/${discountTypeId}`, data);
    return response.data;
};

// 割引タイプ削除 API
export const deleteDiscountType = async (discountTypeId: string): Promise<void> => {
    await apiClient.delete(`/admin/discount-types/${discountTypeId}`);
}; 
import axios, { AxiosError } from 'axios';
import { CampaignCode } from '@/types/subscription';
import { getSession } from 'next-auth/react';
import { getApiBaseUrl, getAxiosConfig } from './api';
import { User, UserRole, AdminUser } from '@/types/user';
import { RoleRead } from '@/types/role';

// APIのベースURLを取得
const API_URL = getApiBaseUrl();

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
  nickname?: string;
  type: 'one_time' | 'recurring';
  recurring?: {
    interval: 'day' | 'week' | 'month' | 'year';
    interval_count: number;
  };
  created: number;
}

// セッション情報とアクセストークンの型 (NextAuthのデフォルトに合わせる)
interface ExtendedSession {
  accessToken?: string;
  user?: {
    id?: string;
    email?: string | null;
    name?: string | null;
    // 他のユーザー情報...
  };
  expires?: string;
}

// ユーザー一覧取得（管理者）
export interface AdminUserListResponse {
  total: number;
  users: AdminUser[];
  page: number;
  size: number;
}

// 新規：ユーザー作成・更新時のペイロード型 (バックエンドのスキーマに合わせる)
export type UserCreatePayload = {
  email: string;
  full_name: string; // バックエンドのフィールド名
  name?: string; // 後方互換用
  password: string; // 新規作成時は必須
  role: '管理者' | '教員' | '生徒'; // バックエンドのEnum値
  status: 'active' | 'inactive' | 'pending';
  // 他のフィールドも必要なら追加 (grade, class_number, etc.)
};

// 更新用ペイロード型
export type UserUpdatePayload = Partial<Omit<UserCreatePayload, 'password'>> & { password?: string }; // パスワードは任意

// 新規：ユーザー詳細取得レスポンス型 (AdminUser とほぼ同じだが明確化)
export type UserDetailsResponse = AdminUser;

/**
 * ユーザー一覧を取得します
 * @param params skip, limit, search, role, status をオプションで指定
 */
export const getUsers = async (params?: {
  skip?: number;
  limit?: number;
  search?: string;
  role?: string;
  status?: string;
}): Promise<AdminUserListResponse> => {
  const config = await getAxiosConfig(true);
  const query = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) query.append(key, String(val));
    });
  }
  const url = `${API_URL}/api/v1/admin/users?${query.toString()}`;
  const response = await axios.get<AdminUserListResponse>(url, config);
  return response.data;
};

/**
 * 新しいユーザーを作成します
 */
export const createUser = async (userData: UserCreatePayload): Promise<UserDetailsResponse> => {
  const config = await getAxiosConfig(true);
  const response = await axios.post<UserDetailsResponse>(`${API_URL}/api/v1/admin/users`, userData, config);
  return response.data;
};

/**
 * 特定のユーザーの詳細を取得します
 */
export const getUserDetails = async (userId: string): Promise<UserDetailsResponse> => {
  const config = await getAxiosConfig(true);
  const response = await axios.get<UserDetailsResponse>(`${API_URL}/api/v1/admin/users/${userId}`, config);
  return response.data;
};

/**
 * ユーザー情報を更新します
 * @param userId 更新するユーザーのID
 * @param userData 更新するユーザーデータ
 * @returns 更新後のユーザー詳細情報
 */
export const updateUser = async (userId: string, userData: UserUpdatePayload): Promise<UserDetailsResponse> => {
  console.log(`Updating user ${userId} at: ${API_URL}/api/v1/admin/users/${userId} with data:`, userData);
  try {
    const config = await getAxiosConfig(true);
    const response = await axios.put<UserDetailsResponse>(`${API_URL}/api/v1/admin/users/${userId}`, userData, config);
    console.log('Updated user:', response.data);
    return response.data; // 成功時はデータを返す
  } catch (error) {
    console.error('Error during user update request:', error); // エラー全体を出力

    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<any>; // エラーの型を明示
      if (axiosError.response) {
        // サーバーからのレスポンスがある場合 (4xx, 5xx エラー)
        console.error('Failed to update user - Status:', axiosError.response.status);
        console.error('Failed to update user - Raw Response Body:', axiosError.response.data); // 生のレスポンスボディを出力

        // --- 修正: detail配列の内容を展開して表示 ---
        const detail = axiosError.response.data?.detail;
        let errorMessage = `ユーザー更新に失敗しました (ステータス: ${axiosError.response.status})`;
        if (detail) {
          if (Array.isArray(detail)) {
            // 配列の場合は、各エラーの詳細を展開して表示
            const errorDetails = detail.map(err => {
              const loc = err.loc ? err.loc.join(' > ') : 'N/A';
              const msg = err.msg || 'Unknown error';
              const type = err.type || 'N/A';
              return `Field: ${loc}, Message: ${msg}, Type: ${type}`;
            }).join('\n');
            console.error('Validation Errors:\n', errorDetails);
            errorMessage = `入力内容にエラーがあります:\n${errorDetails}`; // より詳細なエラーメッセージ
          } else if (typeof detail === 'string') {
            // 文字列の場合はそのまま表示
            console.error('Error Detail:', detail);
            errorMessage = detail;
          } else {
             // その他の形式の場合 (オブジェクトなど)
             console.error('Error Detail (Object):', detail);
             errorMessage = JSON.stringify(detail); // JSON文字列として表示試行
          }
        }
        // ------------------------------------------
        throw new Error(errorMessage);

      } else if (axiosError.request) {
        // リクエストは送信されたが、レスポンスがない場合
        console.error('Failed to update user - No response received:', axiosError.request);
        throw new Error('サーバーから応答がありません。');
      } else {
        // リクエスト設定時のエラーなど
        console.error('Failed to update user - Request Setup Error:', axiosError.message);
        throw new Error(`リクエストエラー: ${axiosError.message}`);
      }
    } else {
      // Axios 以外のエラー
      console.error('Failed to update user - Non-Axios Error:', error);
      throw new Error('予期せぬエラーが発生しました。');
    }
    // throw error; // 元のエラーをそのまま投げてもよい
  }
};

/**
 * ユーザーを削除します
 * @param userId 削除するユーザーのID
 * @returns Promise<void>
 */
export const deleteUser = async (userId: string): Promise<void> => {
  const config = await getAxiosConfig(true);
  await axios.delete(`${API_URL}/api/v1/admin/users/${userId}`, config);
};

export const adminService = {
  // Stripe商品一覧取得
  getProducts: async (): Promise<StripeProduct[]> => {
    try {
      // 認証情報付きのaxios設定を取得
      const config = await getAxiosConfig(true);
      console.log('APIリクエスト用の設定:', config);
      
      const response = await axios.get<StripeProduct[]>(`${API_URL}/api/v1/admin/products`, config);
      
      // データが存在し、配列であるか確認
      if (response.data && Array.isArray(response.data)) {
        return response.data;
      } else {
        console.error('商品データが配列形式ではありません:', response.data);
        // 配列でない場合は空配列を返す
        return [];
      }
    } catch (error: any) {
      // Stripeエラーメッセージを確認して詳細なエラーメッセージを作成
      let errorMessage = '商品の取得に失敗しました';
      
      if (error.response) {
        // サーバーからのレスポンスがある場合
        const status = error.response.status;
        const responseData = error.response.data;
        
        if (status === 401) {
          errorMessage = '認証エラー: APIへのアクセス権限がありません';
        } else if (status === 400) {
          errorMessage = 'リクエストエラー: ' + (responseData.detail || '不正なリクエストです');
        } else if (status === 500) {
          errorMessage = 'サーバーエラー: ' + (responseData.detail || 'サーバー内部エラーが発生しました');
        }
        
        // Stripeエラーの詳細を確認
        if (responseData && responseData.error && responseData.error.message) {
          errorMessage += ` (Stripe: ${responseData.error.message})`;
        }
      }
      
      console.error(errorMessage, error);
      throw new Error(errorMessage);
    }
  },

  // Stripe商品作成
  createProduct: async (productData: {
    name: string;
    description?: string;
    active?: boolean;
  }): Promise<StripeProduct> => {
    const config = await getAxiosConfig(true);
    const response = await axios.post<StripeProduct>(`${API_URL}/api/v1/admin/products`, productData, config);
    return response.data;
  },

  // Stripe商品削除
  deleteProduct: async (productId: string): Promise<any> => {
    const config = await getAxiosConfig(true);
    const response = await axios.delete(`${API_URL}/api/v1/admin/products/${productId}`, config);
    return response.data;
  },

  // Stripe価格一覧取得
  getPrices: async (): Promise<StripePrice[]> => {
    try {
      const config = await getAxiosConfig(true);
      const response = await axios.get<StripePrice[] | { data: StripePrice[] }>(`${API_URL}/api/v1/admin/prices`, config);
      
      // データ構造を確認
      if (response.data) {
        // レスポンスが { data: [...] } 形式の場合
        if (typeof response.data === 'object' && 'data' in response.data && Array.isArray(response.data.data)) {
          return response.data.data;
        }
        // レスポンスが直接配列の場合
        else if (Array.isArray(response.data)) {
          return response.data;
        } else {
          console.error('価格データが予期せぬ形式です:', response.data);
          return [];
        }
      } else {
        console.error('価格データが存在しません');
        return [];
      }
    } catch (error: any) {
      // Stripeエラーメッセージを確認して詳細なエラーメッセージを作成
      let errorMessage = '価格の取得に失敗しました';
      
      if (error.response) {
        // サーバーからのレスポンスがある場合
        const status = error.response.status;
        const responseData = error.response.data;
        
        if (status === 401) {
          errorMessage = '認証エラー: APIへのアクセス権限がありません';
        } else if (status === 400) {
          errorMessage = 'リクエストエラー: ' + (responseData.detail || '不正なリクエストです');
        } else if (status === 500) {
          errorMessage = 'サーバーエラー: ' + (responseData.detail || 'サーバー内部エラーが発生しました');
        }
        
        // Stripeエラーの詳細を確認
        if (responseData && responseData.error && responseData.error.message) {
          errorMessage += ` (Stripe: ${responseData.error.message})`;
        }
      }
      
      console.error(errorMessage, error);
      throw new Error(errorMessage);
    }
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
    const config = await getAxiosConfig(true);
    const response = await axios.post<StripePrice>(`${API_URL}/api/v1/admin/prices`, priceData, config);
    return response.data;
  },

  // Stripe価格削除
  deletePrice: async (priceId: string): Promise<void> => {
    const config = await getAxiosConfig(true);
    await axios.delete(`${API_URL}/api/v1/admin/prices/${priceId}`, config);
  },

  // キャンペーンコード一覧取得
  getCampaignCodes: async (skip = 0, limit = 20, ownerId?: string): Promise<CampaignCode[]> => {
    const params: any = { skip, limit };
    if (ownerId) params.owner_id = ownerId;
    
    const config = await getAxiosConfig(true);
    config.params = params;
    
    const response = await axios.get<CampaignCode[]>(`${API_URL}/api/v1/admin/campaign-codes`, config);
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
    const config = await getAxiosConfig(true);
    const response = await axios.post<CampaignCode>(`${API_URL}/api/v1/admin/campaign-codes`, campaignCode, config);
    return response.data;
  },

  // キャンペーンコード削除
  deleteCampaignCode: async (campaignCodeId: string): Promise<void> => {
    const config = await getAxiosConfig(true);
    await axios.delete(`${API_URL}/api/v1/admin/campaign-codes/${campaignCodeId}`, config);
  }
}; 
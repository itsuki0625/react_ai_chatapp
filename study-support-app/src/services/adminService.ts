import { fetchWithAuth } from '@/lib/fetchWithAuth';
import { CampaignCode, CampaignCodeCreatePayload } from '@/types/subscription';
import { getApiBaseUrl } from './api';
import { AdminUser } from '@/types/user';

// APIのベースURLを取得
const API_URL = getApiBaseUrl();
const ADMIN_API_PREFIX = '/api/v1/admin'; // admin プレフィックスを定数化

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
// 未使用のためコメントアウト
// interface ExtendedSession {
//   accessToken?: string;
//   user?: {
//     id?: string;
//     email?: string | null;
//     name?: string | null;
//     // 他のユーザー情報...
//   };
//   expires?: string;
// }

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
  const query = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) query.append(key, String(val));
    });
  }
  const url = `${API_URL}${ADMIN_API_PREFIX}/users?${query.toString()}`;
  try {
    const response = await fetchWithAuth(url);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('getUsers error:', error);
    throw error;
  }
};

/**
 * 新しいユーザーを作成します
 */
export const createUser = async (userData: UserCreatePayload): Promise<UserDetailsResponse> => {
  const url = `${API_URL}${ADMIN_API_PREFIX}/users`;
  try {
    const response = await fetchWithAuth(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('createUser error:', error);
    throw error;
  }
};

/**
 * 特定のユーザーの詳細を取得します
 */
export const getUserDetails = async (userId: string): Promise<UserDetailsResponse> => {
  const url = `${API_URL}${ADMIN_API_PREFIX}/users/${userId}`;
  try {
    const response = await fetchWithAuth(url);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('getUserDetails error:', error);
    throw error;
  }
};

// エラー詳細の型定義
interface ValidationErrorDetail {
  loc: string[];
  msg: string;
  type: string;
}

type BackendErrorDetail = ValidationErrorDetail[] | string | Record<string, unknown>;

/**
 * ユーザー情報を更新します
 * @param userId 更新するユーザーのID
 * @param userData 更新するユーザーデータ
 * @returns 更新後のユーザー詳細情報
 */
export const updateUser = async (userId: string, userData: UserUpdatePayload): Promise<UserDetailsResponse> => {
  console.log(`Updating user ${userId} with data:`, userData);
  const url = `${API_URL}${ADMIN_API_PREFIX}/users/${userId}`;
  try {
    const response = await fetchWithAuth(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        let errorMessage = `ユーザー更新に失敗しました (ステータス: ${response.status})`;
        const detail = errorData?.detail;
        if (detail) {
            if (Array.isArray(detail)) {
                const errorDetails = detail.map((err: any) => {
                    const loc = err.loc ? err.loc.join(' > ') : 'N/A';
                    const msg = err.msg || 'Unknown error';
                    return `Field: ${loc}, Message: ${msg}`;
                }).join('\n');
                errorMessage = `入力内容にエラーがあります:\n${errorDetails}`;
            } else if (typeof detail === 'string') {
                errorMessage = detail;
            }
        }
        console.error('Update User Error:', errorMessage, errorData);
        throw new Error(errorMessage);
    }
    
    const updatedUser = await response.json();
    console.log('Updated user:', updatedUser);
    return updatedUser;
  } catch (error) {
    console.error('updateUser error (caught):', error);
    throw error;
  }
};

/**
 * ユーザーを削除します
 * @param userId 削除するユーザーのID
 * @returns Promise<void>
 */
export const deleteUser = async (userId: string): Promise<void> => {
  const url = `${API_URL}${ADMIN_API_PREFIX}/users/${userId}`;
  try {
    const response = await fetchWithAuth(url, {
      method: 'DELETE',
    });
    if (!response.ok && response.status !== 204) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
  } catch (error) {
      console.error('deleteUser error:', error);
      throw error;
  }
};

// StripeAPIエラーレスポンスの型
interface StripeErrorResponse {
  detail?: string;
  error?: {
    message: string;
    type?: string;
    code?: string;
  };
}

// キャンペーンコード一覧取得
const getCampaignCodes = async (): Promise<CampaignCode[]> => {
  const url = `${API_URL}${ADMIN_API_PREFIX}/campaign-codes`;
  try {
    const response = await fetchWithAuth(url);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('getCampaignCodes error:', error);
    throw error;
  }
};

// キャンペーンコードを作成 (インポートした型を使用)
const createCampaignCode = async (payload: CampaignCodeCreatePayload): Promise<CampaignCode> => {
  const url = `${API_URL}${ADMIN_API_PREFIX}/campaign-codes`;
  try {
    const response = await fetchWithAuth(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('createCampaignCode error:', error);
    throw error;
  }
};

// キャンペーンコードを削除
const deleteCampaignCode = async (campaignCodeId: string): Promise<void> => {
  const url = `${API_URL}${ADMIN_API_PREFIX}/campaign-codes/${campaignCodeId}`;
  try {
    const response = await fetchWithAuth(url, { method: 'DELETE' });
    if (!response.ok && response.status !== 204) {
      const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    console.error('deleteCampaignCode error:', error);
    throw error;
  }
};

export const adminService = {
  // Stripe商品関連
  getProducts: async (): Promise<StripeProduct[]> => {
    try {
      const response = await fetchWithAuth(`${API_URL}${ADMIN_API_PREFIX}/products`);
      
      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data)) {
          return data;
        } else {
          console.error('商品データが配列形式ではありません:', data);
          return [];
        }
      } else {
        console.error('商品の取得に失敗しました');
        throw new Error('商品の取得に失敗しました');
      }
    } catch (error) {
      let errorMessage = '商品の取得に失敗しました';
      
      if (error instanceof Error) {
        errorMessage = error.message;
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
    metadata?: Record<string, string>;
  }): Promise<StripeProduct> => {
    const response = await fetchWithAuth(`${API_URL}${ADMIN_API_PREFIX}/products`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(productData),
    });
    if (response.ok) {
      return await response.json();
    } else {
      console.error('商品の作成に失敗しました');
      throw new Error('商品の作成に失敗しました');
    }
  },

  // Stripe商品削除
  archiveProduct: async (productId: string): Promise<StripeProduct> => {
    const response = await fetchWithAuth(`${API_URL}${ADMIN_API_PREFIX}/products/${productId}`, {
      method: 'DELETE',
    });
    if (response.ok) {
      return await response.json();
    } else {
      console.error('商品のアーカイブに失敗しました');
      throw new Error('商品のアーカイブに失敗しました');
    }
  },

  // Stripe価格一覧取得
  getPrices: async (): Promise<StripePrice[]> => {
    try {
      const response = await fetchWithAuth(`${API_URL}${ADMIN_API_PREFIX}/prices`);
      
      if (response.ok) {
        const data = await response.json();
        if (typeof data === 'object' && 'data' in data && Array.isArray(data.data)) {
          return data.data;
        } else if (Array.isArray(data)) {
          return data;
        } else {
          console.error('価格データが予期せぬ形式です:', data);
          return [];
        }
      } else {
        console.error('価格の取得に失敗しました');
        throw new Error('価格の取得に失敗しました');
      }
    } catch (error) {
      let errorMessage = '価格の取得に失敗しました';
      
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      console.error(errorMessage, error);
      throw new Error(errorMessage);
    }
  },

  // Stripe価格作成
  createPrice: async (priceData: {
    product_id: string;
    unit_amount: number;
    currency: string;
    recurring?: {
      interval: 'day' | 'week' | 'month' | 'year';
      interval_count: number;
    };
    active?: boolean;
    metadata?: Record<string, string>;
    lookup_key?: string;
  }): Promise<StripePrice> => {
    const response = await fetchWithAuth(`${API_URL}${ADMIN_API_PREFIX}/prices`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(priceData),
    });
    if (response.ok) {
      return await response.json();
    } else {
      console.error('価格の作成に失敗しました');
      throw new Error('価格の作成に失敗しました');
    }
  },

  // Stripe価格削除
  archivePrice: async (priceId: string): Promise<StripePrice> => {
    const response = await fetchWithAuth(`${API_URL}${ADMIN_API_PREFIX}/prices/${priceId}`, {
      method: 'DELETE',
    });
    if (response.ok) {
      return await response.json();
    } else {
      console.error('価格のアーカイブに失敗しました');
      throw new Error('価格のアーカイブに失敗しました');
    }
  },

  // --- ★ キャンペーンコード関連を adminService に含める ---
  getCampaignCodes: getCampaignCodes,
  createCampaignCode: createCampaignCode,
  deleteCampaignCode: deleteCampaignCode,
  // --- ★ ここまで追加 ---

  // --- ★ ユーザー関連 --- // (重複しないようにここにまとめる)
  getUsers: getUsers,
  createUser: createUser,
  getUserDetails: getUserDetails,
  updateUser: updateUser,
  deleteUser: deleteUser,
};
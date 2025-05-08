import { fetchWithAuth } from '@/lib/fetchWithAuth';
import { getApiBaseUrl } from './api';
import { 
  StripeCouponCreate, 
  StripeCouponUpdate, 
  StripeCouponResponse 
} from '@/types/coupon'; // Assuming types are defined in coupon.ts

const API_BASE_URL = getApiBaseUrl();

// Helper function to handle API errors
const handleApiError = async (response: Response, defaultMessage: string): Promise<never> => {
    let errorDetail = defaultMessage;
    try {
        const errorData = await response.json();
        errorDetail = errorData?.detail || errorDetail;
    } catch (e) {
        // Failed to parse JSON, use default message or status text
        errorDetail = response.statusText || defaultMessage;
    }
    console.error(`API Error (${response.status}): ${errorDetail}`);
    throw new Error(errorDetail);
};

// --- DB 操作 ---
// DB クーポンリスト取得
export const listAdminDbCoupons = async (limit: number = 100): Promise<StripeCouponResponse[]> => {
  const url = `${API_BASE_URL}/api/v1/admin/stripe-coupons?limit=${limit}`;
  const response = await fetchWithAuth(url);
  if (!response.ok) {
    await handleApiError(response, 'クーポンリストの取得に失敗しました');
  }
  return (await response.json()) as StripeCouponResponse[];
};

// クーポン作成 (Stripe + DB)
export const createAndImportCoupon = async (data: StripeCouponCreate): Promise<StripeCouponResponse> => {
  const url = `${API_BASE_URL}/api/v1/admin/stripe-coupons`;
  const response = await fetchWithAuth(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    await handleApiError(response, 'クーポン作成に失敗しました');
  }
  return (await response.json()) as StripeCouponResponse;
};

// DB クーポン更新 (Stripe + DB)
export const updateDbCoupon = async (couponDbId: string, data: StripeCouponUpdate): Promise<StripeCouponResponse> => {
  const url = `${API_BASE_URL}/api/v1/admin/stripe-coupons/${couponDbId}`;
  const response = await fetchWithAuth(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    await handleApiError(response, 'クーポン更新に失敗しました');
  }
  return (await response.json()) as StripeCouponResponse;
};

// DB クーポン削除 (Stripe + DB)
export const deleteDbCoupon = async (couponDbId: string): Promise<void> => {
  const url = `${API_BASE_URL}/api/v1/admin/stripe-coupons/${couponDbId}`;
  const response = await fetchWithAuth(url, { method: 'DELETE' });
  if (!response.ok && response.status !== 204) {
    await handleApiError(response, 'クーポン削除に失敗しました');
  }
};

// Export the service object
export const couponAdminService = {
    listAdminDbCoupons,
    createAndImportCoupon,
    updateDbCoupon,
    deleteDbCoupon,
}; 
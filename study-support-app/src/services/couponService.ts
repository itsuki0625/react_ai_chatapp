import { 
  StripeCouponCreate, 
  StripeCouponUpdate, 
  StripeCouponResponse 
} from '@/types/coupon'; // Assuming types are defined in coupon.ts
import { apiClient } from '@/lib/api';

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
  try {
    console.log('Fetching admin DB coupons');
    const response = await apiClient.get(`/api/v1/admin/stripe-coupons`, { params: { limit } });
    return response.data as StripeCouponResponse[];
  } catch (error) {
    console.error('クーポンリストの取得に失敗しました:', error);
    throw error;
  }
};

// クーポン作成 (Stripe + DB)
export const createAndImportCoupon = async (data: StripeCouponCreate): Promise<StripeCouponResponse> => {
  try {
    console.log('Creating and importing coupon:', data);
    const response = await apiClient.post('/api/v1/admin/stripe-coupons', data);
    return response.data as StripeCouponResponse;
  } catch (error) {
    console.error('クーポン作成に失敗しました:', error);
    throw error;
  }
};

// DB クーポン更新 (Stripe + DB)
export const updateDbCoupon = async (couponDbId: string, data: StripeCouponUpdate): Promise<StripeCouponResponse> => {
  try {
    console.log(`Updating DB coupon ${couponDbId}:`, data);
    const response = await apiClient.put(`/api/v1/admin/stripe-coupons/${couponDbId}`, data);
    return response.data as StripeCouponResponse;
  } catch (error) {
    console.error('クーポン更新に失敗しました:', error);
    throw error;
  }
};

// DB クーポン削除 (Stripe + DB)
export const deleteDbCoupon = async (couponDbId: string): Promise<void> => {
  try {
    console.log(`Deleting DB coupon: ${couponDbId}`);
    await apiClient.delete(`/api/v1/admin/stripe-coupons/${couponDbId}`);
  } catch (error) {
    console.error('クーポン削除に失敗しました:', error);
    throw error;
  }
};

// Export the service object
export const couponAdminService = {
    listAdminDbCoupons,
    createAndImportCoupon,
    updateDbCoupon,
    deleteDbCoupon,
}; 
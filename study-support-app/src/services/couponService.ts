import { fetchWithAuth } from '@/lib/fetchWithAuth';
import { getApiBaseUrl } from './api';
import { 
  StripeCouponCreate, 
  StripeCouponUpdate, 
  StripeCouponResponse 
} from '@/types/coupon'; // Assuming types are defined in coupon.ts
import { ListResponse } from '@/types/api'; // Assuming a generic ListResponse type exists

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

// --- Stripe Coupon Admin Service Functions ---

/**
 * GET /admin/stripe/coupons
 * List Stripe Coupons from the backend (which proxies Stripe API).
 */
export const listAdminStripeCoupons = async (params?: {
    limit?: number;
    starting_after?: string;
    ending_before?: string;
    created_lt?: number;
    created_lte?: number;
    created_gt?: number;
    created_gte?: number;
}): Promise<ListResponse<StripeCouponResponse>> => {
    const queryParams = new URLSearchParams(params as Record<string, string>).toString();
    const url = `${API_BASE_URL}/api/v1/admin/stripe/coupons${queryParams ? '?' + queryParams : ''}`;
    console.log(`[Admin Coupon Service] Fetching coupons from: ${url}`);
    
    const response = await fetchWithAuth(url, { method: 'GET' });

    if (!response.ok) {
        await handleApiError(response, 'Failed to fetch Stripe coupons');
    }
    
    // Assuming the backend returns a simple list for now.
    // Adjust if the backend returns a paginated structure like ListResponse<T>
    const data: StripeCouponResponse[] = await response.json(); 
    console.log(`[Admin Coupon Service] Received ${data.length} coupons.`);
    // Wrap in ListResponse if needed, otherwise return data directly
    // For now, returning a simple list and adapting ListResponse structure
    return {
        items: data,
        total: data.length, // Placeholder, backend should provide total for pagination
        page: 1, // Placeholder
        size: data.length // Placeholder
    };
};

/**
 * POST /admin/stripe/coupons
 * Create a new Stripe Coupon via the backend.
 */
export const createAdminStripeCoupon = async (couponData: StripeCouponCreate): Promise<StripeCouponResponse> => {
    const url = `${API_BASE_URL}/api/v1/admin/stripe/coupons`;
    console.log(`[Admin Coupon Service] Creating coupon at: ${url} with data:`, couponData);
    
    const response = await fetchWithAuth(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(couponData),
    });

    if (!response.ok) {
        await handleApiError(response, 'Failed to create Stripe coupon');
    }

    const createdCoupon = await response.json();
    console.log('[Admin Coupon Service] Created coupon:', createdCoupon);
    return createdCoupon;
};

/**
 * GET /admin/stripe/coupons/{coupon_id}
 * Retrieve a specific Stripe Coupon via the backend.
 */
export const retrieveAdminStripeCoupon = async (couponId: string): Promise<StripeCouponResponse> => {
    const url = `${API_BASE_URL}/api/v1/admin/stripe/coupons/${couponId}`;
    console.log(`[Admin Coupon Service] Retrieving coupon from: ${url}`);
    
    const response = await fetchWithAuth(url, { method: 'GET' });

    if (!response.ok) {
        await handleApiError(response, 'Failed to retrieve Stripe coupon');
    }

    const coupon = await response.json();
    console.log('[Admin Coupon Service] Retrieved coupon:', coupon);
    return coupon;
};

/**
 * PUT /admin/stripe/coupons/{coupon_id}
 * Update a Stripe Coupon (e.g., name, metadata) via the backend.
 */
export const updateAdminStripeCoupon = async (couponId: string, updateData: StripeCouponUpdate): Promise<StripeCouponResponse> => {
    const url = `${API_BASE_URL}/api/v1/admin/stripe/coupons/${couponId}`;
    console.log(`[Admin Coupon Service] Updating coupon at: ${url} with data:`, updateData);
    
    const response = await fetchWithAuth(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData),
    });

    if (!response.ok) {
        await handleApiError(response, 'Failed to update Stripe coupon');
    }

    const updatedCoupon = await response.json();
    console.log('[Admin Coupon Service] Updated coupon:', updatedCoupon);
    return updatedCoupon;
};

/**
 * DELETE /admin/stripe/coupons/{coupon_id}
 * Delete a Stripe Coupon via the backend.
 */
export const deleteAdminStripeCoupon = async (couponId: string): Promise<void> => {
    const url = `${API_BASE_URL}/api/v1/admin/stripe/coupons/${couponId}`;
    console.log(`[Admin Coupon Service] Deleting coupon at: ${url}`);
    
    const response = await fetchWithAuth(url, { method: 'DELETE' });

    // DELETE typically returns 204 No Content on success
    if (response.status === 204) {
        console.log(`[Admin Coupon Service] Successfully deleted coupon ${couponId}.`);
        return; // Success
    }

    // Handle other potential success codes if necessary, otherwise treat as error
    if (!response.ok) {
        await handleApiError(response, 'Failed to delete Stripe coupon');
    } else {
        // Handle unexpected success codes with body if applicable
        console.warn(`[Admin Coupon Service] Delete request returned unexpected status ${response.status}`);
    }
};

// Export the service object
export const couponAdminService = {
    listAdminStripeCoupons,
    createAdminStripeCoupon,
    retrieveAdminStripeCoupon,
    updateAdminStripeCoupon,
    deleteAdminStripeCoupon,
}; 
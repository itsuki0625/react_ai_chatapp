import axios from 'axios';
import { 
  SubscriptionPlan, 
  Subscription, 
  PaymentHistory, 
  CampaignCode,
  VerifyCampaignCodeResponse,
  CheckoutSession,
  CreateCheckoutRequest,
  ManageSubscriptionRequest
} from '../types/subscription';

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL + "/api/v1" || 'http://localhost:5050/api/v1';

export const subscriptionService = {
  // サブスクリプションプラン一覧取得 - 認証不要
  getSubscriptionPlans: async (): Promise<SubscriptionPlan[]> => {
    const response = await axios.get<SubscriptionPlan[]>(`${API_URL}/subscriptions/plans/public`);
    return response.data;
  },

  // ユーザーのアクティブなサブスクリプション取得 - 認証必要
  getUserSubscription: async (): Promise<Subscription | null> => {
    const response = await axios.get<Subscription | null>(`${API_URL}/subscriptions/user-subscription`, {
      withCredentials: true
    });
    return response.data;
  },

  // 支払い履歴取得 - 認証必要
  getPaymentHistory: async (skip = 0, limit = 10): Promise<PaymentHistory[]> => {
    const response = await axios.get<PaymentHistory[]>(`${API_URL}/subscriptions/payment-history`, {
      params: { skip, limit },
      withCredentials: true
    });
    return response.data;
  },

  // キャンペーンコード検証 - 認証は任意
  verifyCampaignCode: async (code: string, planId: string, requireAuth = false): Promise<VerifyCampaignCodeResponse> => {
    const config = requireAuth ? { withCredentials: true } : {};
    const response = await axios.post<VerifyCampaignCodeResponse>(
      `${API_URL}/subscriptions/verify-campaign-code`,
      { code, plan_id: planId },
      config
    );
    return response.data;
  },

  // チェックアウトセッション作成 - 認証必要
  createCheckoutSession: async (data: CreateCheckoutRequest): Promise<CheckoutSession> => {
    const response = await axios.post<CheckoutSession>(
      `${API_URL}/subscriptions/create-checkout`,
      data,
      { withCredentials: true }
    );
    return response.data;
  },

  // カスタマーポータルセッション作成 - 認証必要
  createPortalSession: async (returnUrl: string): Promise<{ url: string }> => {
    const response = await axios.post<{ url: string }>(
      `${API_URL}/subscriptions/create-portal-session`,
      { return_url: returnUrl },
      { withCredentials: true }
    );
    return response.data;
  },

  // サブスクリプション管理（キャンセル、再開、更新など） - 認証必要
  manageSubscription: async (data: ManageSubscriptionRequest): Promise<any> => {
    const response = await axios.post(
      `${API_URL}/subscriptions/manage-subscription`,
      data,
      { withCredentials: true }
    );
    return response.data;
  },

  // キャンペーンコード一覧取得 - 認証必要
  getCampaignCodes: async (skip = 0, limit = 20, ownerId?: string): Promise<CampaignCode[]> => {
    const params: any = { skip, limit };
    if (ownerId) params.owner_id = ownerId;
    
    const response = await axios.get<CampaignCode[]>(`${API_URL}/subscriptions/campaign-codes`, {
      params,
      withCredentials: true
    });
    return response.data;
  }
}; 
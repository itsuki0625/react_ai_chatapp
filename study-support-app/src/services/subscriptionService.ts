import axios from 'axios';
// Axiosの型定義
type AxiosResponseData<T = any> = {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  config: any;
};

type AxiosErrorType = Error & {
  isAxiosError: boolean;
  response?: {
    status?: number;
    data?: { detail?: string } & Record<string, any>;
    headers?: Record<string, string>;
  };
};

import { 
  SubscriptionPlan, 
  Subscription, 
  PaymentHistory, 
  CampaignCode,
  VerifyCampaignCodeResponse,
  CheckoutSession,
  CreateCheckoutRequest,
  ManageSubscriptionRequest,
  CampaignCodeVerificationResult
} from '../types/subscription';
import { getSession } from 'next-auth/react';

// ブラウザ環境かサーバー環境かによって適切なAPIのベースURLを使用
const API_URL = typeof window !== 'undefined' 
  ? `${process.env.NEXT_PUBLIC_BROWSER_API_URL || 'http://localhost:5050'}/api/v1`
  : `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:5050'}/api/v1`;

// axios リクエスト用の共通設定
const getAxiosConfig = async (requireAuth = true) => {
  const config: {
    withCredentials: boolean;
    headers: Record<string, string>;
    params?: Record<string, any>;
  } = {
    withCredentials: true, // クッキーを含める
    headers: {}
  };

  // 認証が必要な場合はセッションを取得
  if (requireAuth && typeof window !== 'undefined') {
    try {
      const session = await getSession();
      if (session?.accessToken) { // accessToken を確認
        config.headers['Authorization'] = `Bearer ${session.accessToken}`; // Authorization ヘッダーを設定
      } else if (session) {
        // 以前のカスタムヘッダーロジック（警告付き）
        config.headers['X-Session-Token'] = 'true';
        if (session.user?.email) {
          config.headers['X-User-Email'] = session.user.email;
        }
        if (session.user?.name) {
          // ユーザー名をURLエンコード
          config.headers['X-User-Name'] = encodeURIComponent(session.user.name);
        }
        console.warn('Subscription Service: Session found but no accessToken. Using custom headers.');
      } else {
         console.warn('Subscription Service: No active session found for authenticated request.');
      }
    } catch (error) {
      console.error('セッション取得エラー:', error);
    }
  }

  return config;
};

// axiosエラーの型ガード関数
const isAxiosError = (error: unknown): error is AxiosErrorType => {
  return (
    typeof error === 'object' && 
    error !== null && 
    'isAxiosError' in error && 
    (error as any).isAxiosError === true
  );
};

export const subscriptionService = {
  // サブスクリプションプラン一覧取得 - Stripeから直接取得
  getSubscriptionPlans: async (): Promise<SubscriptionPlan[]> => {
    try {
      // Stripeから価格情報を取得
      const response = await axios.get<SubscriptionPlan[]>(
        `${API_URL}/subscriptions/stripe-plans`,
        await getAxiosConfig(false) // 認証不要
      );
      
      // Stripeのレスポンスを適切な形式に変換
      if (response.data && Array.isArray(response.data)) {
        return response.data.map(plan => ({
          ...plan,
          // Stripe価格IDをプランIDとして使用
          id: plan.price_id,
        }));
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to fetch subscription plans from Stripe:', error);
      throw error;
    }
  },

  // ユーザーのアクティブなサブスクリプション取得 - 認証必要
  getUserSubscription: async (): Promise<Subscription | null> => {
    try {
      const config = await getAxiosConfig(true);
      const response = await axios.get<Subscription | null>(
        `${API_URL}/subscriptions/user-subscription`, 
        config
      );
      return response.data;
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        console.warn('認証エラー: ユーザーサブスクリプション取得できません');
        return null;
      }
      throw error;
    }
  },

  // 支払い履歴取得 - 認証必要、Stripeから直接取得
  getPaymentHistory: async (skip = 0, limit = 10): Promise<PaymentHistory[]> => {
    try {
      const config = await getAxiosConfig(true);
      if (!config.params) config.params = {};
      config.params.skip = skip;
      config.params.limit = limit;
      
      const response = await axios.get<PaymentHistory[]>(
        `${API_URL}/subscriptions/payment-history`, 
        config
      );
      return response.data;
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        console.warn('認証エラー: 支払い履歴を取得できません');
        return [];
      }
      throw error;
    }
  },

  // キャンペーンコード検証 - 認証は任意
  verifyCampaignCode: async (code: string, planId: string, requireAuth = false): Promise<VerifyCampaignCodeResponse> => {
    try {
      const config = await getAxiosConfig(requireAuth);
      const response = await axios.post<VerifyCampaignCodeResponse>(
        `${API_URL}/subscriptions/verify-campaign-code`,
        { code, price_id: planId }, // plan_idの代わりにprice_idを使用
        config
      );
      return response.data;
    } catch (error) {
      console.error('キャンペーンコード検証エラー:', error);
      throw error;
    }
  },

  // チェックアウトセッション作成 - 認証必要、Stripeに直接連携
  createCheckoutSession: async (
    price_id: string,
    success_url: string,
    cancel_url: string,
    metadata?: { [key: string]: string },
    discountInfo?: {
      campaign_code: string;
      discount_type: string;
      discount_value: number;
    }
  ): Promise<string> => {
    try {
      // 認証状態を確認
      const session = await getSession();
      if (!session) {
        console.error('チェックアウトセッション作成失敗: ユーザーが認証されていません');
        throw new Error('認証されていません。ログインしてください。');
      }

      const data: CreateCheckoutRequest = {
        price_id: price_id,
        // plan_idはprice_idと同じ値を使用（Stripeの価格IDがプランIDとなる）
        plan_id: price_id,
        success_url,
        cancel_url,
        campaign_code: discountInfo?.campaign_code
      };

      console.log('チェックアウトセッションリクエストデータ:', data);

      const config = await getAxiosConfig(true);
      // デバッグ情報を追加
      config.headers['X-Request-Info'] = 'checkout-session-creation';
      
      try {
        const response = await axios.post<CheckoutSession>(
          `${API_URL}/subscriptions/create-checkout`,
          data,
          config
        );
        
        if (!response.data || !response.data.url) {
          console.error('チェックアウトURLがレスポンスに含まれていません', response.data);
          throw new Error('チェックアウトURLが取得できませんでした');
        }
        
        return response.data.url;
      } catch (axiosError) {
        if (isAxiosError(axiosError)) {
          // 詳細なエラー情報をログに出力
          console.error('API エラー詳細:', {
            status: axiosError.response?.status,
            data: axiosError.response?.data,
            headers: axiosError.response?.headers
          });
          
          if (axiosError.response?.status === 401) {
            throw new Error('認証セッションが無効です。再ログインしてください。');
          } else if (axiosError.response?.status === 400) {
            throw new Error(axiosError.response.data?.detail || 'リクエストが不正です。');
          } else if (axiosError.response?.status === 500) {
            throw new Error('サーバーエラーが発生しました。後ほど再試行してください。');
          }
        }
        throw axiosError;
      }
    } catch (error) {
      console.error('チェックアウトセッション作成エラー:', error);
      if (error instanceof Error) {
        throw error;
      } else {
        throw new Error('チェックアウトセッションの作成に失敗しました。');
      }
    }
  },

  // カスタマーポータルセッション作成 - 認証必要
  createPortalSession: async (returnUrl: string): Promise<{ url: string }> => {
    try {
      const config = await getAxiosConfig(true);
      const response = await axios.post<{ url: string }>(
        `${API_URL}/subscriptions/create-portal-session`,
        { return_url: returnUrl },
        config
      );
      return response.data;
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        throw new Error('認証セッションが無効です。再ログインしてください。');
      }
      throw error;
    }
  },

  // サブスクリプション管理（キャンセル、再開、更新など） - 認証必要
  manageSubscription: async (data: ManageSubscriptionRequest): Promise<any> => {
    try {
      // price_idをplan_idとして使用するように修正
      const requestData = {
        ...data,
        price_id: data.plan_id,
      };
      
      const config = await getAxiosConfig(true);
      const response = await axios.post(
        `${API_URL}/subscriptions/manage-subscription`,
        requestData,
        config
      );
      return response.data;
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        throw new Error('認証セッションが無効です。再ログインしてください。');
      }
      throw error;
    }
  },

  // キャンペーンコード一覧取得 - 認証必要
  getCampaignCodes: async (skip = 0, limit = 20, ownerId?: string): Promise<CampaignCode[]> => {
    try {
      const config = await getAxiosConfig(true);
      if (!config.params) config.params = {};
      config.params.skip = skip;
      config.params.limit = limit;
      if (ownerId) config.params.owner_id = ownerId;
      
      const response = await axios.get<CampaignCode[]>(
        `${API_URL}/subscriptions/campaign-codes`, 
        config
      );
      return response.data;
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        console.warn('認証エラー: キャンペーンコードを取得できません');
        return [];
      }
      throw error;
    }
  }
}; 
import axios from 'axios';
// 未使用のため、コメントアウト
// type AxiosResponseData<T = unknown> = {
//   data: T;
//   status: number;
//   statusText: string;
//   headers: Record<string, string>;
//   config: Record<string, unknown>;
// };

type AxiosErrorType = Error & {
  isAxiosError: boolean;
  response?: {
    status?: number;
    data?: { detail?: string } & Record<string, unknown>;
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
  ManageSubscriptionRequest
  // 未使用のため削除
  // CampaignCodeVerificationResult
} from '../types/subscription';
import { getSession } from 'next-auth/react';

// StripeProductWithPricesResponse のインポートは、以下の新しい型定義を使うため不要になるか、
// APIの型として別途定義するならそちらに合わせます。
// import { StripeProductWithPricesResponse } from '@/types/stripe'; 

// ブラウザ環境かサーバー環境かによって適切なAPIのベースURLを使用
const API_URL = typeof window !== 'undefined' 
  ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050'}/api/v1` // ブラウザ側では直接バックエンドにアクセス
  : `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:5050'}/api/v1`;

// axios リクエスト用の共通設定
const getAxiosConfig = async (requireAuth = true) => {
  const config: {
    withCredentials: boolean;
    headers: Record<string, string>;
    params?: Record<string, string | number>;
  } = {
    withCredentials: true, // クッキーを含める
    headers: {}
  };

  // 認証が必要な場合はセッションを取得
  if (requireAuth && typeof window !== 'undefined') {
    try {
      const session = await getSession();
      if (session?.user?.accessToken) {
        config.headers['Authorization'] = `Bearer ${session.user.accessToken}`;
      } else if (session) {
        // 以前のカスタムヘッダーロジック（警告付き）
        config.headers['X-Session-Token'] = 'true';
        if (typeof session.user?.email === 'string') {
          config.headers['X-User-Email'] = session.user.email;
        }
        if (typeof session.user?.name === 'string') {
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
    (error as { isAxiosError: boolean }).isAxiosError === true
  );
};

export const subscriptionService = {
  // サブスクリプションプラン一覧取得 - Stripeから直接取得
  getSubscriptionPlans: async (): Promise<SubscriptionPlan[]> => {
    try {
      type APIRawPlan = {
        id: string; 
        name: string;
        description: string | null;
        price_id: string; 
        amount: number;
        currency: string;
        interval: string; 
        is_active: boolean;
        created_at: string; 
        updated_at: string; 
        features?: string[];
      };

      const response = await axios.get<APIRawPlan[]>(
        `${API_URL}/subscriptions/stripe-plans`,
        await getAxiosConfig(false)
      );

      if (response.data && Array.isArray(response.data)) {
        const plans: SubscriptionPlan[] = response.data.map(apiPlan => {
          return {
            id: apiPlan.id || apiPlan.price_id,
            name: apiPlan.name,
            description: apiPlan.description,
            price_id: apiPlan.price_id,
            amount: apiPlan.amount,
            currency: apiPlan.currency,
            interval: apiPlan.interval,
            interval_count: 1,
            is_active: apiPlan.is_active,
            created_at: apiPlan.created_at,
            updated_at: apiPlan.updated_at,
            features: apiPlan.features || [],
          };
        });
        console.log("subscriptionService.ts getSubscriptionPlans (corrected):", plans);
        return plans;
      }
      console.warn("getSubscriptionPlans: No data or data is not an array", response.data);
      return [];
    } catch (error) {
      console.error('Failed to fetch subscription plans in subscriptionService:', error);
      if (isAxiosError(error)) {
        console.error('Axios error details:', {
          message: error.message,
          status: error.response?.status,
          data: error.response?.data,
        });
      } else {
        console.error('Non-Axios error details:', error);
      }
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
        { code, price_id: planId }, 
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
    metadata?: Record<string, string>,
    stripeCouponId?: string // Optional: Stripe Coupon ID
  ): Promise<string | { url: string }> => {
    try {
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
        coupon_id: stripeCouponId // ★ coupon_id として stripeCouponId を渡す
      };

      console.log('チェックアウトセッションリクエストデータ:', data);

      const config = await getAxiosConfig(true);
      // デバッグ情報を追加
      config.headers['X-Request-Info'] = 'checkout-session-creation';
      
      try {
        const response = await axios.post<CheckoutSession>(
          `${API_URL}/subscriptions/create-checkout`,
          data, // ★ 修正したリクエストデータ
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

  // 顧客ポータルセッション作成 - 認証必要
  createPortalSession: async (return_url: string): Promise<{ url: string }> => {
    try {
      const session = await getSession();
      if (!session) {
        console.error('ポータルセッション作成失敗: ユーザーが認証されていません');
        throw new Error('認証されていません。ログインしてください。');
      }

      const config = await getAxiosConfig(true); // 認証ヘッダーを取得
      const response = await axios.post<{ url: string }>(
        `${API_URL}/subscriptions/create-portal-session`,
        { return_url }, // リクエストボディに return_url を含める
        config
      );

      if (!response.data || !response.data.url) {
        console.error('ポータルセッションURLがレスポンスに含まれていません', response.data);
        throw new Error('ポータルセッションURLが取得できませんでした');
      }
      return response.data; // { url: "..." } を返す
    } catch (error) {
      console.error('ポータルセッション作成エラー:', error);
      if (isAxiosError(error) && error.response?.status === 401) {
        throw new Error('認証セッションが無効です。再ログインしてください。');
      }
      // その他のエラーはそのままスローするか、カスタムエラーに変換
      throw error;
    }
  },

  // サブスクリプション管理 (プラン変更など) - 認証必要
  manageSubscription: async (data: ManageSubscriptionRequest): Promise<Subscription> => {
    try {
      const config = await getAxiosConfig(true);
      const response = await axios.post<Subscription>(
        `${API_URL}/subscriptions/manage-subscription`,
        data,
        config
      );
      return response.data;
    } catch (error) {
      console.error('サブスクリプション管理エラー:', error);
      if (isAxiosError(error) && error.response?.status === 401) {
        throw new Error('認証セッションが無効です。再ログインしてください。');
      }
      throw error;
    }
  },

  // 利用可能なキャンペーンコード一覧取得 (認証は任意、状況による)
  getAvailableCampaignCodes: async (requireAuth = false): Promise<CampaignCode[]> => {
    try {
      const config = await getAxiosConfig(requireAuth);
      const response = await axios.get<CampaignCode[]>(
        `${API_URL}/subscriptions/campaign-codes`,
        config
      );
      return response.data;
    } catch (error) {
      console.error('キャンペーンコード一覧取得エラー:', error);
      throw error;
    }
  },
};
/**
 * ユーザー情報インターフェース
 */
export interface User {
  id: string;
  email: string;
  name?: string;
  role?: string | string[] | { 
    permissions?: string[];
    name?: string;
  };
  created_at?: string;
  updated_at?: string;
}

/**
 * ユーザーサブスクリプション情報インターフェース
 */
export interface UserSubscription {
  id: string;
  user_id: string;
  plan_name: string;
  status: string;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at?: string;
  canceled_at?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
} 
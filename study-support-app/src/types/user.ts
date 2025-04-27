/**
 * ユーザー情報インターフェース
 */
export type UserRole = '管理者' | '教員' | '生徒' | string;

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: 'active' | 'inactive' | 'pending' | 'unpaid'; // 未決済ステータスを追加
  createdAt: string; // または Date 型
  lastLogin?: string; // または Date 型
  // 必要に応じて他のフィールドを追加
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
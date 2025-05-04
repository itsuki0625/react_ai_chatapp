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
  createdAt?: string; // ISO 8601 DateTime string
  lastLogin?: string; // ISO 8601 DateTime string or null
  prefecture?: string | null;
  profile_image_url?: string | null; // 追加
  // 必要に応じて他のフィールドを追加
}

/**
 * ユーザーサブスクリプション情報インターフェース
 */
export interface UserSubscription {
  id: string;
  user_id: string;
  plan_name: string;
  price_id?: string;
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

// BackendのAdminUserモデルに対応（例）
export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: string; // バックエンドからの文字列をそのまま受け取る
  status: string; // バックエンドからの文字列をそのまま受け取る
  created_at: string;
  last_login_at: string | null;
}

// Available user roles (adjust as needed)
// Remove the duplicate UserRole definition here
// export type UserRole = '管理者' | '教員' | '生徒'; // 日本語に変更

// Add these interfaces:
export interface UserSettings {
  email: string;
  full_name: string; // Add full_name based on API response
  name: string; // Keep for internal state/display mapping
  profile_image_url?: string | null; // ★ 追加 (Nullable string型)
  emailNotifications: boolean;
  browserNotifications: boolean;
  theme: string; // e.g., 'light' | 'dark'
  subscription?: SubscriptionInfo | null; // Make subscription optional and potentially null
}

export interface SubscriptionInfo {
  id: string;
  plan_name: string;
  status: string;
  current_period_end: string; // ISO 8601 DateTime string
} 
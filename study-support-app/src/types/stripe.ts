// バックエンドの app/schemas/stripe.py に対応する型定義

export interface StripeRecurring {
  interval: 'day' | 'week' | 'month' | 'year';
  interval_count: number;
}

export interface StripeProductMetadata {
  assigned_role?: string;
  features?: string;
  // 他のメタデータキーもここに追加可能
}

export interface StripeProductBase {
  name: string;
  description?: string | null;
  active: boolean;
  metadata?: StripeProductMetadata;
  images?: string[];
}

export type StripeProductCreate = StripeProductBase;

export interface StripeProductUpdate {
  name?: string;
  description?: string | null;
  active?: boolean;
  metadata?: StripeProductMetadata;
}

export interface StripeProductResponse extends StripeProductBase {
  id: string;
  created: number; // Unix timestamp
  updated: number; // Unix timestamp
  assigned_role_name?: string;
}

export interface StripePriceBase {
  unit_amount?: number | null; // 最小通貨単位 (円など)
  currency: string; // 例: 'jpy'
  recurring?: StripeRecurring | null; // nullの場合は都度払い
  active: boolean;
  metadata?: Record<string, string | number | boolean | null> | null;
  lookup_key?: string | null;
}

export interface StripePriceCreate extends StripePriceBase {
  product_id: string;
  unit_amount: number; // 作成時は必須
  recurring: StripeRecurring; // 作成時は必須
}

export interface StripePriceUpdate {
  active?: boolean | null;
  metadata?: Record<string, string | number | boolean | null> | null;
  lookup_key?: string | null;
}

export interface StripePriceResponse extends StripePriceBase {
  id: string;
  product: string; // Product ID
  created: number; // Unix timestamp
  livemode: boolean;
  type: 'recurring' | 'one_time';
}

// GET /admin/products のレスポンス型
export interface StripeProductWithPricesResponse extends StripeProductResponse {
  prices: StripePriceResponse[];
} 
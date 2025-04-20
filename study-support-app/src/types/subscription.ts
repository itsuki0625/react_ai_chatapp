export interface SubscriptionPlan {
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
}

export interface Subscription {
  id: string;
  user_id: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  status: string;
  plan_name: string;
  price_id: string;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at: string | null;
  canceled_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PaymentHistory {
  id: string;
  user_id: string;
  subscription_id: string | null;
  stripe_payment_intent_id: string | null;
  stripe_invoice_id: string | null;
  amount: number;
  currency: string;
  status: string;
  payment_method: string | null;
  payment_date: string;
  created_at: string;
  updated_at: string;
}

export interface CampaignCode {
  id: string;
  code: string;
  description: string | null;
  owner_id: string | null;
  discount_type: 'percentage' | 'fixed';
  discount_value: number;
  max_uses: number | null;
  used_count: number;
  valid_from: string | null;
  valid_until: string | null;
  is_active: boolean;
  is_valid: boolean;
  created_at: string;
  updated_at: string;
}

export interface VerifyCampaignCodeResponse {
  valid: boolean;
  message: string;
  discount_type: 'percentage' | 'fixed' | null;
  discount_value: number | null;
  original_amount: number | null;
  discounted_amount: number | null;
  campaign_code_id: string | null;
}

export interface CampaignCodeVerificationResult extends VerifyCampaignCodeResponse {
  is_valid: boolean;
}

export interface CheckoutSession {
  session_id: string;
  url: string;
}

export interface CreateCheckoutRequest {
  plan_id?: string;
  price_id: string;
  success_url: string;
  cancel_url: string;
  campaign_code?: string;
}

export interface ManageSubscriptionRequest {
  subscription_id: string;
  action: 'cancel' | 'reactivate' | 'update';
  plan_id?: string;
} 
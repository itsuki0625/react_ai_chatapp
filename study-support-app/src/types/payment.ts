// PaymentIntent関連の型定義
export interface PaymentIntentCreateRequest {
  price_id: string;
  plan_id?: string;
  coupon_id?: string;
}

export interface PaymentIntentResponse {
  client_secret: string;
  amount: number;
  currency: string;
  status: string;
}

export interface PaymentIntentConfirmRequest {
  payment_intent_id: string;
  payment_method_id: string;
}

export interface PaymentStatus {
  id: string;
  status: 'requires_payment_method' | 'requires_confirmation' | 'requires_action' | 'processing' | 'succeeded' | 'canceled';
  amount: number;
  currency: string;
  client_secret?: string;
}

export interface SubscriptionConfirmRequest {
  payment_intent_id: string;
  price_id: string;
}

export interface PaymentFormData {
  cardholderName: string;
  saveCard: boolean;
} 
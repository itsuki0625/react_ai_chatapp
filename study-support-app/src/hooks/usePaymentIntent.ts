import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { PaymentIntentCreateRequest, PaymentIntentResponse } from '@/types/payment';

// API関数
const createPaymentIntent = async (data: PaymentIntentCreateRequest): Promise<PaymentIntentResponse> => {
  const response = await apiClient.post<PaymentIntentResponse>('/subscriptions/create-payment-intent', data);
  return response.data;
};

// PaymentIntentフック
export function usePaymentIntent() {
  const [paymentIntent, setPaymentIntent] = useState<PaymentIntentResponse | null>(null);

  const createPaymentIntentMutation = useMutation<
    PaymentIntentResponse,
    Error,
    PaymentIntentCreateRequest
  >({
    mutationFn: createPaymentIntent,
    onSuccess: (data) => {
      setPaymentIntent(data);
    },
    onError: (error) => {
      console.error('PaymentIntent creation failed:', error);
      setPaymentIntent(null);
    },
  });

  const clearPaymentIntent = () => {
    setPaymentIntent(null);
  };

  return {
    paymentIntent,
    createPaymentIntent: createPaymentIntentMutation.mutate,
    isCreating: createPaymentIntentMutation.isPending,
    createError: createPaymentIntentMutation.error,
    clearPaymentIntent,
  };
} 
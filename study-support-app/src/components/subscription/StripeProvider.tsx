'use client';

import React from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';

// Stripe公開キーの設定
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

interface StripeProviderProps {
  children: React.ReactNode;
  clientSecret?: string;
}

const stripeOptions = {
  appearance: {
    theme: 'stripe' as const,
    variables: {
      colorPrimary: 'hsl(221.2 83.2% 53.3%)', // Tailwind blue-600
      colorBackground: '#ffffff',
      colorText: '#1f2937', // Tailwind gray-800
      colorDanger: '#dc2626', // Tailwind red-600
      fontFamily: 'system-ui, -apple-system, sans-serif',
      spacingUnit: '4px',
      borderRadius: '6px',
    },
    rules: {
      '.Input': {
        border: '1px solid #d1d5db', // Tailwind gray-300
        borderRadius: '6px',
        padding: '12px',
        fontSize: '14px',
      },
      '.Input:focus': {
        border: '2px solid hsl(221.2 83.2% 53.3%)',
        boxShadow: '0 0 0 2px hsl(221.2 83.2% 53.3% / 0.1)',
      },
      '.Label': {
        fontSize: '14px',
        fontWeight: '500',
        color: '#374151', // Tailwind gray-700
        marginBottom: '6px',
      },
    },
  },
};

export function StripeProvider({ children, clientSecret }: StripeProviderProps) {
  const options = {
    ...stripeOptions,
    clientSecret,
  };

  return (
    <Elements stripe={stripePromise} options={clientSecret ? options : stripeOptions}>
      {children}
    </Elements>
  );
}

// 使用例:
// <StripeProvider clientSecret={paymentIntent.client_secret}>
//   <PaymentForm />
// </StripeProvider> 
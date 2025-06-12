'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api/client';
import { useToast } from '@/hooks/use-toast';

interface PaymentInfo {
  type: 'checkout' | 'payment_intent';
  id: string;
  amount?: number;
  currency?: string;
  status?: string;
}

export default function SubscriptionSuccess() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  
  const [paymentInfo, setPaymentInfo] = useState<PaymentInfo | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const [confirmationError, setConfirmationError] = useState<string | null>(null);

  useEffect(() => {
    // URLパラメータから決済情報を取得
    const sessionId = searchParams.get('session_id');
    const paymentIntentId = searchParams.get('payment_intent');

    if (sessionId) {
      setPaymentInfo({
        type: 'checkout',
        id: sessionId
      });
    } else if (paymentIntentId) {
      setPaymentInfo({
        type: 'payment_intent',
        id: paymentIntentId
      });
      // PaymentIntentの場合はサブスクリプション確定処理が必要
      handleConfirmSubscription(paymentIntentId);
    }

    // 5秒後にダッシュボードに遷移
    const timer = setTimeout(() => {
      router.push('/dashboard');
    }, 5000);

    return () => clearTimeout(timer);
  }, [searchParams, router]);

  const handleConfirmSubscription = async (paymentIntentId: string) => {
    setIsConfirming(true);
    setConfirmationError(null);

    try {
      // PaymentIntentからサブスクリプションを確定
      // 実際の実装では、PaymentIntentのメタデータからprice_idを取得する必要があります
      // ここでは簡略化のため、別途必要な情報を取得する処理を想定
      
      toast({
        title: "サブスクリプション作成中",
        description: "サブスクリプションを作成しています...",
        variant: "default"
      });

      // 実際の確定処理はWebhookで処理されることが多いので、
      // ここでは確認のみ行う場合もあります
      
    } catch (error) {
      console.error('Subscription confirmation error:', error);
      setConfirmationError('サブスクリプションの確定に失敗しました');
      
      toast({
        title: "エラー",
        description: "サブスクリプションの確定に失敗しました",
        variant: "destructive"
      });
    } finally {
      setIsConfirming(false);
    }
  };

  const getPaymentTypeText = () => {
    if (!paymentInfo) return "決済";
    
    switch (paymentInfo.type) {
      case 'checkout':
        return "Stripe Checkout決済";
      case 'payment_intent':
        return "カード決済";
      default:
        return "決済";
    }
  };

  const getSuccessMessage = () => {
    if (isConfirming) {
      return "サブスクリプションを作成中です...";
    }
    
    if (confirmationError) {
      return confirmationError;
    }
    
    return "サブスクリプションの購入ありがとうございます。";
  };

  const getSuccessIcon = () => {
    if (isConfirming) {
      return (
        <div className="rounded-full bg-blue-100 h-24 w-24 flex items-center justify-center mx-auto">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 text-blue-600 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </div>
      );
    }

    if (confirmationError) {
      return (
        <div className="rounded-full bg-red-100 h-24 w-24 flex items-center justify-center mx-auto">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 text-red-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </div>
      );
    }

    return (
      <div className="rounded-full bg-green-100 h-24 w-24 flex items-center justify-center mx-auto">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-12 w-12 text-green-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>
    );
  };

  return (
    <div className="max-w-md mx-auto mt-12 p-6 bg-white rounded-lg shadow-md">
      <div className="text-center">
        {getSuccessIcon()}
        
        <h1 className="text-2xl font-bold text-gray-800 mt-6">
          {confirmationError ? "エラーが発生しました" : "支払いが完了しました"}
        </h1>
        
        <p className="text-gray-600 mt-2">
          {getSuccessMessage()}
        </p>

        {!isConfirming && (
          <p className="text-sm text-gray-500 mt-2">
            自動的にダッシュボードに移動します。
          </p>
        )}
        
        {paymentInfo && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">
              <strong>決済方法:</strong> {getPaymentTypeText()}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              <strong>ID:</strong> {paymentInfo.id.substring(0, 20)}...
            </p>
          </div>
        )}
        
        <div className="mt-8">
          <Link
            href="/dashboard"
            className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            ダッシュボードへ
          </Link>
          
          {confirmationError && (
            <Link
              href="/subscription/plans"
              className="ml-2 px-4 py-2 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              プラン選択に戻る
            </Link>
          )}
        </div>
      </div>
    </div>
  );
} 
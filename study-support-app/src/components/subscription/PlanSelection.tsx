'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/common/Card';
import { useMutation } from '@tanstack/react-query';
import { useToast } from "@/hooks/use-toast";
import { apiClient } from '@/lib/api/client'; // API Client
import { SubscriptionPlanResponse, CheckoutSessionResponse, CreateCheckoutRequest } from '@/types/subscription'; 
import { useRouter } from 'next/navigation'; // Use next/navigation
import { usePaymentIntent } from '@/hooks/usePaymentIntent';
import { StripeProvider } from './StripeProvider';
import { PaymentForm } from './PaymentForm';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// API 関数を直接定義 (または api/subscription.ts などに分ける)
const fetchSubscriptionPlans = async (): Promise<SubscriptionPlanResponse[]> => {
  const response = await apiClient.get<SubscriptionPlanResponse[]>('/subscriptions/stripe-plans');
  return response.data;
};

const createCheckoutSession = async (data: CreateCheckoutRequest): Promise<CheckoutSessionResponse> => {
  const response = await apiClient.post<CheckoutSessionResponse>('/subscriptions/create-checkout', data);
  return response.data;
};

export function PlanSelection() {
  const [plans, setPlans] = useState<SubscriptionPlanResponse[]>([]);
  const [isLoadingPlans, setIsLoadingPlans] = useState(true);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [paymentMode, setPaymentMode] = useState<'checkout' | 'elements'>('elements'); // デフォルトをElementsに
  const { toast } = useToast();
  const router = useRouter(); // useRouter フックを使用

  // PaymentIntent用のフック
  const { 
    paymentIntent, 
    createPaymentIntent, 
    isCreating, 
    createError, 
    clearPaymentIntent 
  } = usePaymentIntent();

  useEffect(() => {
    const loadPlans = async () => {
      setIsLoadingPlans(true);
      setError(null);
      try {
        const fetchedPlans = await fetchSubscriptionPlans();
        setPlans(fetchedPlans);
      } catch (err) {
        console.error("プランの読み込みに失敗:", err);
        setError("プランの読み込みに失敗しました。");
        toast({ title: "エラー", description: "プラン情報の取得に失敗しました。", variant: "destructive" });
      } finally {
        setIsLoadingPlans(false);
      }
    };
    loadPlans();
  }, [toast]);

  // Stripe Checkout用のミューテーション
  const checkoutMutation = useMutation<
    CheckoutSessionResponse,
    Error,
    CreateCheckoutRequest
  >({
    mutationFn: createCheckoutSession,
    onSuccess: (data) => {
      if (data.url) {
        router.push(data.url);
      } else {
        toast({ title: "エラー", description: "決済ページへのリダイレクトに失敗しました。", variant: "destructive" });
      }
    },
    onError: (error) => {
      toast({ title: "エラー", description: `決済セッションの作成に失敗: ${error.message}`, variant: "destructive" });
    },
  });

  // Stripe Checkout用の処理
  const handleCheckoutSubscribe = (priceId: string) => {
    const currentUrl = window.location.href;
    const successUrl = `${window.location.origin}/subscription/success?session_id={CHECKOUT_SESSION_ID}`; 
    const cancelUrl = currentUrl; 

    checkoutMutation.mutate({
      price_id: priceId,
      success_url: successUrl,
      cancel_url: cancelUrl,
    });
  };

  // Stripe Elements用の処理
  const handleElementsSubscribe = (priceId: string) => {
    // PaymentIntentを作成
    createPaymentIntent({ price_id: priceId });
  };

  // 決済成功時の処理
  const handlePaymentSuccess = (paymentIntentResult: any) => {
    console.log('Payment succeeded:', paymentIntentResult);
    toast({ 
      title: "決済完了", 
      description: "サブスクリプションの支払いが完了しました", 
      variant: "default" 
    });
    // 成功ページへリダイレクト
    router.push(`/subscription/success?payment_intent=${paymentIntentResult.id}`);
  };

  // 決済エラー時の処理
  const handlePaymentError = (error: string) => {
    console.error('Payment error:', error);
    toast({ 
      title: "決済エラー", 
      description: error, 
      variant: "destructive" 
    });
  };

  if (isLoadingPlans) return <div>プランを読み込み中...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (plans.length === 0) return <div>利用可能なプランがありません。</div>;

  const selectedPlan = plans.find(plan => plan.price_id === selectedPlanId);

  return (
    <div className="container mx-auto py-12">
      <h2 className="text-3xl font-bold text-center mb-8">料金プラン</h2>
      
      {/* 決済方法選択タブ */}
      <div className="mb-8 flex justify-center">
        <Tabs value={paymentMode} onValueChange={(value) => setPaymentMode(value as 'checkout' | 'elements')}>
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="elements">カード決済 (推奨)</TabsTrigger>
            <TabsTrigger value="checkout">Stripe Checkout</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {plans.map((plan) => (
          <Card 
            key={plan.id} 
            className={`flex flex-col ${selectedPlanId === plan.price_id ? 'border-primary ring-2 ring-primary' : ''}`}
            onClick={() => setSelectedPlanId(plan.price_id)}
          >
            <CardHeader>
              <CardTitle>{plan.name}</CardTitle>
              <CardDescription>{plan.description || '詳細情報なし'}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow">
              <p className="text-4xl font-bold mb-4">
                ¥{plan.amount.toLocaleString()} 
                <span className="text-lg font-normal text-muted-foreground">
                  / {plan.interval === 'month' ? '月' : '年'}
                </span>
              </p>
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full" 
                onClick={() => {
                  if (paymentMode === 'checkout') {
                    handleCheckoutSubscribe(plan.price_id);
                  } else {
                    handleElementsSubscribe(plan.price_id);
                  }
                }}
                disabled={checkoutMutation.isPending || isCreating}
              >
                {(checkoutMutation.isPending && checkoutMutation.variables?.price_id === plan.price_id) || 
                 (isCreating) 
                  ? '処理中...' 
                  : 'このプランを選択'}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {/* PaymentIntent作成エラー表示 */}
      {createError && (
        <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">決済の準備に失敗しました: {createError.message}</p>
          <Button 
            variant="outline" 
            className="mt-2" 
            onClick={clearPaymentIntent}
          >
            再試行
          </Button>
        </div>
      )}

      {/* Stripe Elements決済フォーム */}
      {paymentIntent && (
        <div className="mt-12">
          <h3 className="text-2xl font-bold text-center mb-6">お支払い情報の入力</h3>
          <StripeProvider clientSecret={paymentIntent.client_secret}>
            <PaymentForm
              amount={paymentIntent.amount}
              currency={paymentIntent.currency}
              onSuccess={handlePaymentSuccess}
              onError={handlePaymentError}
            />
          </StripeProvider>
        </div>
      )}
    </div>
  );
} 
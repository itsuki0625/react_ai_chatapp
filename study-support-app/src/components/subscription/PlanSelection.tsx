'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/common/Card';
import { useMutation } from '@tanstack/react-query';
import { useToast } from "@/hooks/use-toast";
import { apiClient } from '@/lib/api/client'; // API Client
import { SubscriptionPlanResponse, CheckoutSessionResponse, CreateCheckoutRequest } from '@/types/subscription'; 
import { useRouter } from 'next/navigation'; // Use next/navigation

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
  const { toast } = useToast();
  const router = useRouter(); // useRouter フックを使用

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

  const checkoutMutation = useMutation<
    CheckoutSessionResponse,
    Error,
    CreateCheckoutRequest
  >({
    mutationFn: createCheckoutSession,
    onSuccess: (data) => {
      // Stripe Checkout ページにリダイレクト
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

  const handleSubscribe = (priceId: string) => {
    // 現在のURLを取得して success/cancel URL を生成
    const currentUrl = window.location.href;
    // Payment success/cancel pages might need to be created
    const successUrl = `${window.location.origin}/payment/success?session_id={CHECKOUT_SESSION_ID}`; 
    const cancelUrl = currentUrl; 

    checkoutMutation.mutate({
      price_id: priceId,
      success_url: successUrl,
      cancel_url: cancelUrl,
    });
  };

  if (isLoadingPlans) return <div>プランを読み込み中...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (plans.length === 0) return <div>利用可能なプランがありません。</div>;

  return (
    <div className="container mx-auto py-12">
      <h2 className="text-3xl font-bold text-center mb-8">料金プラン</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {plans.map((plan) => (
          <Card 
            key={plan.id} 
            className={`flex flex-col ${selectedPlanId === plan.price_id ? 'border-primary ring-2 ring-primary' : ''}`}
            onClick={() => setSelectedPlanId(plan.price_id)} // 選択機能（オプション）
          >
            <CardHeader>
              <CardTitle>{plan.name}</CardTitle>
              <CardDescription>{plan.description || '詳細情報なし'}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow">
              <p className="text-4xl font-bold mb-4">
                ¥{plan.amount.toLocaleString()} <span className="text-lg font-normal text-muted-foreground">/ {plan.interval === 'month' ? '月' : '年'}</span>
              </p>
              {/* 機能リストなど (必要に応じて追加) */}
              {/* 
              <ul className="space-y-2">
                <li className="flex items-center"><CheckCircle className="h-5 w-5 text-green-500 mr-2" /> 機能 A</li>
                <li className="flex items-center"><CheckCircle className="h-5 w-5 text-green-500 mr-2" /> 機能 B</li>
              </ul> 
              */}
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full" 
                onClick={() => handleSubscribe(plan.price_id)}
                disabled={checkoutMutation.isPending}
              >
                {checkoutMutation.isPending && checkoutMutation.variables?.price_id === plan.price_id 
                  ? '処理中...' 
                  : 'このプランを選択'}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
} 
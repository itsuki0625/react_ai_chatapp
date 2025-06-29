import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { StyledH1, StyledH2 } from '@/components/common/CustomHeadings';
import { SubscriptionPlan, Subscription, VerifyCampaignCodeResponse } from '@/types/subscription';
import { subscriptionService } from '@/services/subscriptionService';
import { CampaignCodeForm } from '@/components/feature/student/subscription/CampaignCodeForm';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { formatAmount } from '@/utils/formatting';
import { Button } from '@/components/ui/button';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";

const getIntervalText = (interval?: string, intervalCount?: number): string => {
  if (!interval) return '';
  const count = intervalCount && intervalCount > 1 ? intervalCount : '';
  switch (interval) {
    case 'day':
      return `/${count}日`;
    case 'week':
      return `/${count}週`;
    case 'month':
      return `/${count}月`;
    case 'year':
      return `/${count}年`;
    default:
      return `/${count}${interval}`;
  }
};

export const SubscriptionPlansPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  const { data: plans = [], isLoading: isLoadingPlans } = useQuery<SubscriptionPlan[]>({
    queryKey: ['subscriptionPlans'],
    queryFn: async () => {
      const fetchedPlans = await subscriptionService.getSubscriptionPlans();
      console.log('Fetched plans in SubscriptionPlansPage:', JSON.stringify(fetchedPlans, null, 2));
      return fetchedPlans;
    }
  });
  const { data: currentSubscription, isLoading: isLoadingSubscription, refetch: refetchUserSubscription } = useQuery<Subscription | null>({ queryKey: ['userSubscription'], queryFn: subscriptionService.getUserSubscription });

  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [isPageLoading, setIsPageLoading] = useState(true);
  const [campaignCode, setCampaignCode] = useState<string>('');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [campaignCodeVerificationResult, setCampaignCodeVerificationResult] = useState<VerifyCampaignCodeResponse | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const { toast } = useToast();

  const handleSelectPlan = useCallback((plan: SubscriptionPlan) => {
    console.log('[handleSelectPlan] Selecting:', plan.name);
    setSelectedPlan(plan);
    setCampaignCodeVerificationResult(null);
    setCampaignCode('');
    setError(null);
  }, [setSelectedPlan, setCampaignCodeVerificationResult, setCampaignCode, setError]);

  useEffect(() => {
    console.log('[Effect: Initial Plan Selection] Running. isLoadingPlans:', isLoadingPlans, 'plans.length:', plans.length, 'selectedPlan:', selectedPlan?.name);
    if (!isLoadingPlans && plans.length > 0 && !selectedPlan) {
      const planIdFromUrl = searchParams?.get('plan');
      console.log('[Effect: Initial Plan Selection] planIdFromUrl:', planIdFromUrl);
      const planToSelect = planIdFromUrl
        ? plans.find(p => p.id === planIdFromUrl || p.price_id === planIdFromUrl)
        : plans[0];

      if (planToSelect) {
        console.log('[Effect: Initial Plan Selection] Found planToSelect:', planToSelect.name);
        handleSelectPlan(planToSelect);
      } else {
        console.log('[Effect: Initial Plan Selection] No plan found to select initially.');
      }
    }
  }, [plans, isLoadingPlans, searchParams, handleSelectPlan, selectedPlan]);

  useEffect(() => {
    console.log('[Effect: Loading/Code] Running. isLoadingPlans:', isLoadingPlans, 'isLoadingSubscription:', isLoadingSubscription);
    setIsPageLoading(isLoadingPlans || isLoadingSubscription);
    const codeFromUrl = searchParams?.get('code');
    if (codeFromUrl && !campaignCode && !campaignCodeVerificationResult) {
      console.log('[Effect: Loading/Code] Setting campaign code from URL:', codeFromUrl);
      setCampaignCode(codeFromUrl);
    }
  }, [isLoadingPlans, isLoadingSubscription, searchParams, campaignCode, campaignCodeVerificationResult]);

  useEffect(() => {
    console.log('SubscriptionPlansPage - Authentication status changed:', session);
  }, [session]);

  const handleVerifyCampaignCode = useCallback(async (code: string): Promise<VerifyCampaignCodeResponse> => {
    if (!selectedPlan) {
      toast({ variant: 'destructive', title: "エラー", description: 'プランが選択されていません。' });
      throw new Error("Plan not selected");
    }
    try {
      const result = await subscriptionService.verifyCampaignCode(code, selectedPlan.price_id, true);
      setCampaignCodeVerificationResult(result);

      if (result.valid) {
          toast({ title: "成功", description: result.message || `コード「${code}」が適用されました。` });
      } else {
          toast({ variant: 'destructive', title: "無効なコード", description: result.message || 'コードが無効です。' });
      }
      return result;
    } catch (error) {
      console.error('Error verifying campaign code:', error);
      setCampaignCodeVerificationResult(null);
      const errorMessage = error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'response' in error && error.response && typeof error.response === 'object' && 'data' in error.response && typeof error.response.data === 'object' && error.response.data !== null && 'detail' in error.response.data && typeof error.response.data.detail === 'string'
          ? error.response.data.detail
          : 'キャンペーンコードの検証中にエラーが発生しました。';
      toast({ variant: 'destructive', title: "検証エラー", description: errorMessage });
      throw error;
    }
  }, [selectedPlan, toast]);

  const handleProceedToCheckout = async () => {
    if (!session) {
      toast({ variant: 'destructive', title: "エラー", description: 'ログインが必要です。' });
      router.push(`/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`);
      return;
    }
    setCheckoutLoading(true);
    setError(null);

    try {
      const priceId = selectedPlan?.price_id;
      if (!selectedPlan || !priceId) {
        toast({ variant: 'destructive', title: "エラー", description: 'プランが選択されていません。' });
        setCheckoutLoading(false);
        return;
      }

      const successUrl = `${window.location.origin}/subscription/success?session_id={CHECKOUT_SESSION_ID}`;
      const cancelUrl = window.location.href;

      const stripeCouponId = campaignCodeVerificationResult?.valid
        ? (campaignCodeVerificationResult.stripe_coupon_id ?? undefined)
        : undefined;

      try {
        const response = await subscriptionService.createCheckoutSession(
          priceId,
          successUrl,
          cancelUrl,
          undefined,
          stripeCouponId
        );

        let checkoutUrl: string | null = null;
        if (response && typeof response === 'string') {
             checkoutUrl = response;
        } else if (response && typeof response === 'object' && 'url' in response) {
            checkoutUrl = response.url;
        } else {
             console.error('Invalid checkout URL response:', response);
        }

        if (checkoutUrl) {
          window.location.href = checkoutUrl;
        } else {
          toast({ variant: 'destructive', title: "エラー", description: 'チェックアウトセッションの作成に失敗しました。(URL取得エラー)' });
          console.error('チェックアウトセッションの作成に失敗しました。URLがありません。 Response:', response);
        }
      } catch (apiError) {
        let errorMessage = 'チェックアウトセッションの作成中にエラーが発生しました。';
        if (apiError instanceof Error) {
          errorMessage = apiError.message || errorMessage;
          if (apiError.message.includes('認証') || apiError.message.includes('ログイン')) {
            toast({ variant: 'destructive', title: "エラー", description: '認証セッションが切れています。再ログインしてください。' });

            setTimeout(() => {
              const returnUrl = encodeURIComponent(`/subscription/plans?plan=${selectedPlan?.price_id || ''}${campaignCode ? `&code=${campaignCode}` : ''}`);
              router.push(`/login?redirect=${returnUrl}`);
            }, 2000);
            setCheckoutLoading(false);
            return;
          }
        } else if (typeof apiError === 'object' && apiError !== null && 
                   'response' in apiError && apiError.response && 
                   typeof apiError.response === 'object' && 
                   'data' in apiError.response && typeof apiError.response.data === 'object' && 
                   apiError.response.data !== null && 
                   'detail' in apiError.response.data && 
                   typeof apiError.response.data.detail === 'string') {
            errorMessage = apiError.response.data.detail;
        }
        console.error('Stripe Checkout Session Error:', apiError);
        toast({ variant: 'destructive', title: "APIエラー", description: errorMessage });
      }
    } catch (error) {
      console.error('チェックアウトセッション作成中の予期せぬエラー:', error);
      toast({ variant: 'destructive', title: "予期せぬエラー", description: 'チェックアウトセッションの作成に失敗しました。' });
    } finally {
      setCheckoutLoading(false);
    }
  };

  // デバッグ用のテスト関数
  const handleDebugTest = async () => {
    if (!session) {
      toast({ variant: 'destructive', title: "エラー", description: 'ログインが必要です。' });
      return;
    }

    try {
      console.log('[DEBUG] デバッグテスト開始');
      
      // subscriptionServiceを使って統一的にAPIコールする
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://stg-api.smartao.jp'}/api/v1/subscriptions/debug-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(session as any).accessToken}`, // 型キャストで解決
        },
      });
      
      const data = await response.json();
      
      console.log('[DEBUG] デバッグテスト結果:', data);
      
      if (response.ok) {
        toast({ title: "成功", description: `デバッグテスト成功: ユーザーID ${data.user_id}` });
      } else {
        toast({ variant: 'destructive', title: "エラー", description: `デバッグテスト失敗: ${data.detail || 'Unknown error'}` });
      }
    } catch (error) {
      console.error('[DEBUG] デバッグテストエラー:', error);
      toast({ variant: 'destructive', title: "エラー", description: `デバッグテストエラー: ${error instanceof Error ? error.message : 'Unknown error'}` });
    }
  };

  const handleCancelSubscription = async () => {
    if (!currentSubscription || !currentSubscription.stripe_subscription_id) {
      toast({ variant: "destructive", title: "エラー", description: "解約対象のサブスクリプションが見つかりません。" });
      return;
    }
    setIsCancelling(true);
    try {
      await subscriptionService.manageSubscription({
        action: "cancel",
        subscription_id: currentSubscription.stripe_subscription_id
      });
      toast({ title: "成功", description: "サブスクリプションの解約手続きを受け付けました。詳細はメールをご確認ください。" });
      refetchUserSubscription();
    } catch (error) {
      console.error("サブスクリプション解約エラー:", error);
      const errorMessage = error instanceof Error ? error.message : "サブスクリプションの解約に失敗しました。";
      toast({ variant: "destructive", title: "解約エラー", description: errorMessage });
    } finally {
      setIsCancelling(false);
      setShowCancelConfirm(false);
    }
  };

  console.log('[SubscriptionPlansPage] Rendering state:', {
    plans,
    selectedPlan,
    isLoadingPlans,
    isLoadingSubscription,
    currentSubscription,
    error,
    isPageLoading,
    checkoutLoading
  });

  if (isPageLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-10">
        <p className="text-red-500">{error}</p>
        <Button
          onClick={() => {
            setError(null);
            queryClient.invalidateQueries({ queryKey: ['subscriptionPlans'] });
            queryClient.invalidateQueries({ queryKey: ['userSubscription'] });
          }}
          className="mt-4"
        >
          再試行する
        </Button>
      </div>
    );
  }

  if (session && currentSubscription && currentSubscription.is_active) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <StyledH1 className="mb-6">サブスクリプション</StyledH1>
        <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
          <StyledH2 className="mb-4">現在のサブスクリプション</StyledH2>
          <p className="mb-2">
            <span className="font-semibold">プラン:</span> {session?.user?.role || currentSubscription.plan_name}
            {session?.user?.role && session.user.role !== currentSubscription.plan_name && (
              <span className="text-xs text-yellow-600 ml-2">
                (データ同期中)
              </span>
            )}
          </p>
          <p className="mb-2">
            <span className="font-semibold">ステータス:</span> {currentSubscription.status === 'active' ? '有効' : currentSubscription.status}
            {currentSubscription.cancel_at && <span className="text-yellow-600 ml-2">(解約処理中)</span>}
          </p>
          {currentSubscription.current_period_end && (
            <p className="mb-2">
              <span className="font-semibold">次回更新日:</span> {new Date(currentSubscription.current_period_end).toLocaleDateString('ja-JP')}
            </p>
          )}
          {currentSubscription.cancel_at && (
             <p className="mb-2 text-yellow-600">
               <span className="font-semibold">解約予定日:</span> {new Date(currentSubscription.cancel_at).toLocaleDateString('ja-JP')}
             </p>
           )}
          <p className="mt-4 text-gray-600">
            サブスクリプションの管理や解約は「マイページ」から行うことができます。
          </p>
          
          {!currentSubscription.cancel_at && currentSubscription.status === 'active' && (
            <AlertDialog open={showCancelConfirm} onOpenChange={setShowCancelConfirm}>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="destructive"
                  className="mt-4 w-full" 
                  disabled={isCancelling}
                >
                  {isCancelling ? <LoadingSpinner /> : "サブスクリプションを解約する"}
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>本当に解約しますか？</AlertDialogTitle>
                  <AlertDialogDescription>
                    現在の請求期間が終了すると、サブスクリプションは自動的に解約されます。
                    この操作は元に戻せませんが、期間終了までは引き続きサービスをご利用いただけます。
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel disabled={isCancelling}>キャンセル</AlertDialogCancel>
                  <AlertDialogAction onClick={handleCancelSubscription} disabled={isCancelling} className="bg-red-600 hover:bg-red-700">
                    {isCancelling ? "処理中..." : "解約する"}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
          {currentSubscription.cancel_at && (
            <p className="mt-4 p-3 bg-yellow-50 border border-yellow-300 text-yellow-700 rounded-md">
              このサブスクリプションは解約手続き済みです。 {new Date(currentSubscription.cancel_at).toLocaleDateString('ja-JP')} をもって終了します。
            </p>
          )}

          <Button
            onClick={() => router.push('/settings')}
            className="mt-6 w-full"
            variant="outline"
          >
            マイページへ
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <StyledH1 className="mb-0">サブスクリプションプラン</StyledH1>
        <Button
          onClick={() => router.push('/settings')}
          variant="outline"
          className="text-sm"
        >
          マイページへ
        </Button>
      </div>

      <div className="mb-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {(() => { console.log('[Render Debug] currentSubscription:', currentSubscription); return null; })()}

        {plans.map((plan) => {
           const isActiveSub = currentSubscription ? currentSubscription.is_active : false;
           const currentSubPriceId = currentSubscription?.price_id;
           const planPriceId = plan.price_id;
           const isCurrentPlan = isActiveSub && !!currentSubPriceId && currentSubPriceId === planPriceId;

           console.log(`[Render Debug] Plan: ${plan.name} (${planPriceId}), IsCurrent: ${isCurrentPlan}`);

           return (
             <div
               key={plan.id}
               className={`border rounded-lg p-6 cursor-pointer transition-all duration-300 ${
                 selectedPlan?.price_id === plan.price_id
                   ? 'border-blue-500 shadow-lg bg-blue-50'
                   : 'border-gray-200 hover:border-blue-300 hover:shadow'
               } ${isCurrentPlan ? '!border-green-500 !bg-green-50 !cursor-default' : ''}`}
               onClick={() => !isCurrentPlan && handleSelectPlan(plan)}
             >
               <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
               <p className="text-2xl font-bold mb-3">
                 {(() => {
                   console.log(`Formatting amount: plan.name = ${plan.name}, plan.amount = ${plan.amount}, type = ${typeof plan.amount}`);
                   return formatAmount(plan.amount);
                 })()}
                 <span className="text-sm font-normal">{getIntervalText(plan.interval, plan.interval_count)}</span>
               </p>
               <p className="text-gray-600 mb-4">{plan.description}</p>

               {isCurrentPlan && (
                 <div className="mb-4 text-center">
                   <span className="text-sm font-bold text-green-700 bg-green-100 px-3 py-1 rounded-full">
                     現在のプラン
                   </span>
                 </div>
               )}

               {plan.features && plan.features.length > 0 && (
                 <ul className="mb-4">
                   {plan.features.map((feature, index) => (
                     <li key={index} className="flex items-start mb-2">
                       <span className="text-green-500 mr-2">✓</span>
                       <span>{feature}</span>
                     </li>
                   ))}
                 </ul>
               )}

               {!isCurrentPlan && selectedPlan?.price_id !== plan.price_id && (
                 <Button
                   variant="outline"
                   className="w-full mt-4"
                   onClick={(e) => { e.stopPropagation(); handleSelectPlan(plan); }}
                   disabled={isPageLoading}
                 >
                   このプランを選択
                 </Button>
               )}
                  {!isCurrentPlan && selectedPlan?.price_id === plan.price_id && (
                    <Button
                      variant="default"
                      className="w-full mt-4 bg-blue-600 text-white"
                      disabled={true}
                    >
                      選択中
                    </Button>
                  )}
             </div>
           );
         })}
      </div>

      {selectedPlan && (!currentSubscription || !currentSubscription.is_active) && (
        <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
          <StyledH2 className="mb-4">選択したプラン</StyledH2>
          <div className="mb-4">
            <p className="text-xl font-semibold">{selectedPlan.name}</p>
            <p className="mt-1">
              <span className="font-semibold">料金:</span>{' '}
              {campaignCodeVerificationResult?.valid && typeof campaignCodeVerificationResult.discounted_amount === 'number' ? (
                <span>
                  <span className="line-through text-gray-500">{(() => {
                    console.log(`Formatting amount (discounted - original): selectedPlan.name = ${selectedPlan.name}, selectedPlan.amount = ${selectedPlan.amount}, type = ${typeof selectedPlan.amount}`);
                    return formatAmount(selectedPlan.amount);
                  })()}</span>{' '}
                  <span className="text-green-600 font-semibold">{(() => {
                    console.log(`Formatting amount (discounted - final): discounted_amount = ${campaignCodeVerificationResult.discounted_amount}, type = ${typeof campaignCodeVerificationResult.discounted_amount}`);
                    return formatAmount(campaignCodeVerificationResult.discounted_amount!);
                  })()}</span>
                  <span className="text-sm text-green-600 ml-1">
                    ({campaignCodeVerificationResult.discount_type === 'percentage'
                      ? `${campaignCodeVerificationResult.discount_value}%オフ`
                      : `${formatAmount(campaignCodeVerificationResult.discount_value || 0)}オフ`})
                  </span>
                </span>
              ) : (
                (() => {
                  console.log(`Formatting amount (no discount): selectedPlan.name = ${selectedPlan.name}, selectedPlan.amount = ${selectedPlan.amount}, type = ${typeof selectedPlan.amount}`);
                  return formatAmount(selectedPlan.amount);
                })()
              )}
              <span className="text-sm text-gray-600 ml-1">{getIntervalText(selectedPlan.interval, selectedPlan.interval_count)}</span>
            </p>
          </div>

          <div className="mb-6">
            <CampaignCodeForm
              onSubmit={handleVerifyCampaignCode}
              onCodeChange={setCampaignCode}
              initialCode={campaignCode}
              onApply={(result) => {
                console.log('Applying code:', result);
              }}
              currency={selectedPlan?.currency || "jpy"}
              isLoading={checkoutLoading}
            />
          </div>

          <button
            className={`w-full text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center transition-colors duration-200 ${
              session
                ? (checkoutLoading ? 'bg-gray-500 cursor-not-allowed' : 'bg-gradient-to-r from-purple-600 to-indigo-700 hover:from-purple-700 hover:to-indigo-800')
                : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700'
            }`}
            onClick={handleProceedToCheckout}
            disabled={checkoutLoading || !selectedPlan || isPageLoading}
          >
            {checkoutLoading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                処理中...
              </div>
            ) : session ? (
              'お支払いに進む'
            ) : (
              'ログインして続ける'
            )}
          </button>

          {/* デバッグ用ボタン（開発環境でのみ表示） */}
          {process.env.NODE_ENV === 'development' && session && (
            <Button
              onClick={handleDebugTest}
              variant="outline"
              className="w-full mt-2 text-xs"
              disabled={checkoutLoading || isPageLoading}
            >
              🔧 API接続テスト（デバッグ用）
            </Button>
          )}
        </div>
      )}
    </div>
  );
}; 
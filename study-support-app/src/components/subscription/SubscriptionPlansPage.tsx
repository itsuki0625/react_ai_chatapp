import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { StyledH1, StyledH2 } from '@/components/common/CustomHeadings';
import { SubscriptionPlan, CampaignCodeVerificationResult, Subscription, VerifyCampaignCodeResponse } from '@/types/subscription';
import { subscriptionService } from '@/services/subscriptionService';
import { CampaignCodeForm } from '@/components/subscription/CampaignCodeForm';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { formatAmount } from '@/utils/formatting';
import { Button } from '@/components/common/Button';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';

export const SubscriptionPlansPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  const { data: plans = [], isLoading: isLoadingPlans } = useQuery<SubscriptionPlan[]>({ queryKey: ['subscriptionPlans'], queryFn: subscriptionService.getSubscriptionPlans });
  const { data: currentSubscription, isLoading: isLoadingSubscription } = useQuery<Subscription | null>({ queryKey: ['userSubscription'], queryFn: subscriptionService.getUserSubscription });

  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [isPageLoading, setIsPageLoading] = useState(true);
  const [campaignCode, setCampaignCode] = useState<string>('');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [campaignCodeVerificationResult, setCampaignCodeVerificationResult] = useState<CampaignCodeVerificationResult | null>(null);

  const { toast } = useToast();

  const handleSelectPlan = useCallback((plan: SubscriptionPlan) => {
    setSelectedPlan(plan);
    setCampaignCodeVerificationResult(null);
    setCampaignCode('');
    setError(null);
  }, []);

  useEffect(() => {
    const planIdFromUrl = searchParams?.get('plan');
    const codeFromUrl = searchParams?.get('code');

    if (!isLoadingPlans && plans.length > 0) {
        const planToSelect = planIdFromUrl
            ? plans.find(p => p.id === planIdFromUrl || p.price_id === planIdFromUrl)
            : plans[0];

        if (planToSelect) {
            if (!selectedPlan || selectedPlan.price_id !== planToSelect.price_id) {
                handleSelectPlan(planToSelect);
            }
        }
    }

    if (codeFromUrl && !campaignCode && !campaignCodeVerificationResult) {
        setCampaignCode(codeFromUrl);
    }

    setIsPageLoading(isLoadingPlans || isLoadingSubscription);

  }, [plans, isLoadingPlans, isLoadingSubscription, searchParams, selectedPlan, campaignCode, campaignCodeVerificationResult, handleSelectPlan]);

  useEffect(() => {
    console.log('SubscriptionPlansPage - Authentication status changed:', session);
    if (session) {
        // fetchData();
    }
  }, [session]);

  const handleVerifyCampaignCode = useCallback(async (code: string): Promise<VerifyCampaignCodeResponse> => {
    if (!selectedPlan) {
      toast({ variant: 'destructive', title: "エラー", description: 'プランが選択されていません。' });
      throw new Error("Plan not selected");
    }
    try {
      const result = await subscriptionService.verifyCampaignCode(code, selectedPlan.price_id);
      const verificationResult: CampaignCodeVerificationResult = {
        is_valid: result.valid,
        valid: result.valid,
        campaign_code_id: null,
        message: result.message ?? '',
        discount_type: result.discount_type ?? null,
        discount_value: result.discount_value ?? null,
        original_amount: result.original_amount ?? null,
        discounted_amount: result.discounted_amount ?? null,
      };

      setCampaignCodeVerificationResult(verificationResult);

      if (verificationResult.is_valid) {
          toast({ title: "成功", description: verificationResult.message || `コード「${code}」が適用されました。` });
      } else {
          toast({ variant: 'destructive', title: "無効なコード", description: verificationResult.message || 'コードが無効です。' });
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

      const successUrl = `${window.location.origin}/payment/success?session_id={CHECKOUT_SESSION_ID}`;
      const cancelUrl = window.location.href;

      try {
        const response = await subscriptionService.createCheckoutSession(
          priceId,
          successUrl,
          cancelUrl,
          campaignCodeVerificationResult?.is_valid && campaignCode
            ? { campaign_code: campaignCode }
            : undefined
        );

        let checkoutUrl: string | null = null;
        if (response && typeof response === 'object') {
            const potentialUrl = (response as { url?: unknown }).url;
            if (typeof potentialUrl === 'string') {
                checkoutUrl = potentialUrl;
            }
        } else if (typeof response === 'string') {
             checkoutUrl = response;
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
            <span className="font-semibold">プラン:</span> {currentSubscription.plan_name}
          </p>
          <p className="mb-2">
            <span className="font-semibold">ステータス:</span> {currentSubscription.status === 'active' ? '有効' : currentSubscription.status}
          </p>
          {currentSubscription.current_period_end && (
            <p className="mb-2">
              <span className="font-semibold">次回更新日:</span> {new Date(currentSubscription.current_period_end).toLocaleDateString('ja-JP')}
            </p>
          )}
          {currentSubscription.cancel_at && (
             <p className="mb-2 text-yellow-600">
               <span className="font-semibold">キャンセル予定日:</span> {new Date(currentSubscription.cancel_at).toLocaleDateString('ja-JP')}
             </p>
           )}
          <p className="mt-4 text-gray-600">
            サブスクリプションの管理や解約は「マイページ」から行うことができます。
          </p>
          <Button
            onClick={() => router.push('/settings/profile')}
            className="mt-4"
          >
            マイページへ
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <StyledH1 className="mb-6">サブスクリプションプラン</StyledH1>

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
                 {formatAmount(plan.amount)} <span className="text-sm font-normal">/ 月</span>
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
                      variant="primary"
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
              {campaignCodeVerificationResult?.is_valid && typeof campaignCodeVerificationResult.discounted_amount === 'number' ? (
                <span>
                  <span className="line-through text-gray-500">{formatAmount(selectedPlan.amount)}</span>{' '}
                  <span className="text-green-600 font-semibold">{formatAmount(campaignCodeVerificationResult.discounted_amount)}</span>
                  <span className="text-sm text-green-600 ml-1">
                    ({campaignCodeVerificationResult.discount_type === 'percentage'
                      ? `${campaignCodeVerificationResult.discount_value}%オフ`
                      : `${formatAmount(campaignCodeVerificationResult.discount_value || 0)}オフ`})
                  </span>
                </span>
              ) : (
                formatAmount(selectedPlan.amount)
              )}
              <span className="text-sm text-gray-600 ml-1">/ 月</span>
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
        </div>
      )}
    </div>
  );
}; 
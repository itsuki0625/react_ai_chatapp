import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { StyledH1, StyledH2 } from '@/components/common/CustomHeadings';
import { SubscriptionPlan, CampaignCodeVerificationResult, Subscription, VerifyCampaignCodeResponse } from '@/types/subscription';
import { subscriptionService } from '@/services/subscriptionService';
import { CampaignCodeForm } from '@/components/subscription/CampaignCodeForm';
import { UserSubscription } from '@/types/user';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { formatAmount } from '@/utils/formatting';
import { Button } from '@/components/common/Button';
import toast from 'react-hot-toast';

export const SubscriptionPlansPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: session, status } = useSession();
  const isAuthenticated = status === 'authenticated';

  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<UserSubscription | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [campaignCode, setCampaignCode] = useState<string>('');
  const [campaignCodeVerificationResult, setCampaignCodeVerificationResult] = useState<CampaignCodeVerificationResult | null>(null);

  const [isPageLoading, setIsPageLoading] = useState(true);
  const [isLoadingPlans, setIsLoadingPlans] = useState(true);
  const [isLoadingSubscription, setIsLoadingSubscription] = useState(true);
  const [isCreatingCheckoutSession, setIsCreatingCheckoutSession] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === 'loading' || isLoadingPlans || isLoadingSubscription) {
      setIsPageLoading(true);
    } else {
      setIsPageLoading(false);
    }
  }, [status, isLoadingPlans, isLoadingSubscription]);

  useEffect(() => {
    const planId = searchParams?.get('plan');
    const code = searchParams?.get('code');
    
    if (code) {
      setCampaignCode(code);
    }
    
    // fetchData(); // fetchData は status 変更時に呼ばれる
    
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  useEffect(() => {
    console.log('SubscriptionPlansPage - Authentication status changed:', status);
    // status が 'loading' でない場合に fetchData を呼び出す（二重呼び出し防止）
    if (status !== 'loading') {
        fetchData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const fetchData = useCallback(async () => {
    setIsLoadingPlans(true);
    setIsLoadingSubscription(true);
    setError(null);
    setCurrentSubscription(null);

    try {
      const fetchedPlans = await subscriptionService.getSubscriptionPlans();
      console.log('Fetched Subscription Plans:', JSON.stringify(fetchedPlans, null, 2));
      setPlans(fetchedPlans);

      const planId = searchParams?.get('plan');
      if (planId && fetchedPlans.length > 0) {
        const plan = fetchedPlans.find(p => p.id === planId || p.price_id === planId);
        setSelectedPlan(plan || fetchedPlans[0]);
      } else if (fetchedPlans.length > 0) {
        setSelectedPlan(fetchedPlans[0]);
      }
      setIsLoadingPlans(false);

      if (status === 'authenticated') {
        console.log('User is authenticated, fetching user subscription...');
        try {
          const subscription = await subscriptionService.getUserSubscription();
          console.log('Fetched user subscription result:', subscription);
          if (subscription) {
             const subData = subscription as Subscription & { price_id?: string };
             const userSubscription: UserSubscription = {
               id: subData.id,
               user_id: subData.user_id,
               plan_name: subData.plan_name,
               price_id: subData.price_id,
               status: subData.status,
               stripe_customer_id: subData.stripe_customer_id || undefined,
               stripe_subscription_id: subData.stripe_subscription_id || undefined,
               current_period_start: subData.current_period_start || undefined,
               current_period_end: subData.current_period_end || undefined,
               cancel_at: subData.cancel_at || undefined,
               canceled_at: subData.canceled_at || undefined,
               is_active: subData.is_active,
               created_at: subData.created_at,
               updated_at: subData.updated_at
             };
             setCurrentSubscription(userSubscription);
             console.log('Set currentSubscription state:', userSubscription);
          } else {
            console.log('No active subscription found.');
          }
        } catch (subscriptionError) {
          console.error('Error fetching user subscription:', subscriptionError);
        } finally {
          setIsLoadingSubscription(false);
        }
      } else {
        console.log('User not authenticated, skipping subscription fetch.');
        setIsLoadingSubscription(false);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('データの取得中にエラーが発生しました。');
       setIsLoadingPlans(false);
       setIsLoadingSubscription(false);
    }
  }, [status]);

  const handleSelectPlan = (plan: SubscriptionPlan) => {
    setSelectedPlan(plan);
    setCampaignCodeVerificationResult(null);
    setCampaignCode('');
  };

  const handleVerifyCampaignCode = async (code: string, planId: string) => {
    try {
      const result = await subscriptionService.verifyCampaignCode(code, planId);
      const verificationResult: CampaignCodeVerificationResult = {
        ...result,
        is_valid: result.valid
      };
      setCampaignCodeVerificationResult(verificationResult);
      return verificationResult;
    } catch (error) {
      console.error('Error verifying campaign code:', error);
      setCampaignCodeVerificationResult(null);
      throw error;
    }
  };

  const handleApplyCampaignCode = (result: VerifyCampaignCodeResponse | CampaignCodeVerificationResult) => {
    console.log('キャンペーンコードが適用されました', result);
  };

  const handleProceedToCheckout = async () => {
    setCheckoutLoading(true);
    console.log('SubscriptionPlansPage - handleProceedToCheckout called', {
      status,
      selectedPlan
    });
    
    try {
      if (status !== 'authenticated') {
        console.log('SubscriptionPlansPage - User not authenticated, redirecting to login');
        const returnUrl = encodeURIComponent(`/subscription/plans?plan=${selectedPlan?.price_id || ''}`);
        window.location.href = `/login?redirect=${returnUrl}`;
        setCheckoutLoading(false);
        return;
      }

      if (!selectedPlan) {
        toast.error('プランが選択されていません。');
        setCheckoutLoading(false);
        return;
      }

      setError(null);

      const successUrl = `${window.location.origin}/subscription/success?session_id={CHECKOUT_SESSION_ID}`;
      const cancelUrl = `${window.location.origin}/subscription/plans`;

      const priceId = selectedPlan.price_id;
      
      console.log('チェックアウトセッション作成リクエスト:', {
        price_id: priceId,
        plan_id: priceId
      });

      try {
        const response = await subscriptionService.createCheckoutSession(
          priceId,
          successUrl,
          cancelUrl,
          {
            user_id: session?.user?.id || '',
            price_id: priceId
          },
          campaignCodeVerificationResult?.is_valid && campaignCode 
            ? { 
                campaign_code: campaignCode, 
                discount_type: campaignCodeVerificationResult.discount_type || 'percentage',
                discount_value: campaignCodeVerificationResult.discount_value || 0
              } 
            : undefined
        );

        if (response) {
          window.location.href = response;
        } else {
          toast.error('チェックアウトセッションの作成に失敗しました。');
          console.error('チェックアウトセッションの作成に失敗しました。URLがありません。');
        }
      } catch (apiError) {
        console.error('チェックアウトセッション作成APIエラー:', apiError);
        
        let errorMessage = 'チェックアウトセッションの作成に失敗しました。';
        
        if (apiError instanceof Error) {
          if (apiError.message.includes('認証') || apiError.message.includes('ログイン')) {
            toast.error('認証セッションが切れています。再ログインしてください。');
            
            setTimeout(() => {
              const returnUrl = encodeURIComponent(`/subscription/plans?plan=${selectedPlan?.price_id || ''}`);
              window.location.href = `/login?redirect=${returnUrl}`;
            }, 1500);
            return;
          }
          
          errorMessage = apiError.message;
        }
        
        toast.error(errorMessage);
      }
    } catch (error) {
      console.error('チェックアウトセッション作成中の予期せぬエラー:', error);
      toast.error('チェックアウトセッションの作成に失敗しました。');
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
            fetchData();
          }}
          className="mt-4"
        >
          再試行する
        </Button>
      </div>
    );
  }

  if (status === 'authenticated' && currentSubscription && currentSubscription.is_active) {
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
              {campaignCodeVerificationResult?.is_valid && campaignCodeVerificationResult.discounted_amount ? (
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
              onSubmit={(code) => handleVerifyCampaignCode(code, selectedPlan.price_id)}
              onApply={handleApplyCampaignCode}
              initialCode={campaignCode}
              onCodeChange={setCampaignCode}
              originalAmount={selectedPlan.amount}
              currency={selectedPlan.currency}
            />
          </div>

          <button
            className={`w-full text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center transition-colors duration-200 ${
              status === 'authenticated'
                ? (checkoutLoading ? 'bg-gray-500' : 'bg-gradient-to-r from-purple-600 to-indigo-700 hover:from-purple-700 hover:to-indigo-800')
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
            ) : status === 'authenticated' ? (
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
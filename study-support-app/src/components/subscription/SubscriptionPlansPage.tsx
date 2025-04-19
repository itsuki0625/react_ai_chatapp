import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SubscriptionPlan, Subscription, VerifyCampaignCodeResponse } from '@/types/subscription';
import { subscriptionService } from '@/services/subscriptionService';
import { PlanCard } from './PlanCard';
import { CampaignCodeForm } from './CampaignCodeForm';
import Link from 'next/link';

interface SubscriptionPlansPageProps {
  isAuthenticated?: boolean;
}

export const SubscriptionPlansPage: React.FC<SubscriptionPlansPageProps> = ({ isAuthenticated = false }) => {
  const router = useRouter();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<Subscription | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [campaignCode, setCampaignCode] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerifyCampaignCodeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        
        // サブスクリプションプランは認証不要で取得できるようにするとよい
        const plansData = await subscriptionService.getSubscriptionPlans();
        setPlans(plansData);
        
        // 認証済みユーザーの場合のみ現在のサブスクリプション情報を取得
        if (isAuthenticated) {
          try {
            const subscriptionData = await subscriptionService.getUserSubscription();
            setCurrentSubscription(subscriptionData);
          } catch (err) {
            // サブスクリプション情報の取得に失敗しても、プラン表示は継続
            console.error('Failed to fetch user subscription:', err);
          }
        }
      } catch (err) {
        console.error('Failed to fetch subscription plans:', err);
        setError('サブスクリプションプランの取得に失敗しました。');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated]);

  const handleSelectPlan = (planId: string) => {
    const plan = plans.find(p => p.id === planId);
    if (plan) {
      setSelectedPlan(plan);
      // 別のプランを選択したら、キャンペーンコードの適用状態をリセット
      setCampaignCode(null);
      setVerificationResult(null);
    }
  };

  const handleVerifyCampaignCode = async (code: string) => {
    if (!selectedPlan) return { valid: false, message: 'プランが選択されていません' } as VerifyCampaignCodeResponse;
    
    try {
      const result = await subscriptionService.verifyCampaignCode(code, selectedPlan.id);
      setCampaignCode(result.valid ? code : null);
      return result;
    } catch (err) {
      console.error('Failed to verify campaign code:', err);
      throw err;
    }
  };

  const handleApplyCampaignCode = (result: VerifyCampaignCodeResponse) => {
    setVerificationResult(result);
  };

  const handleProceedToCheckout = async () => {
    if (!selectedPlan) return;
    
    // 未認証ユーザーはログインページにリダイレクト
    if (!isAuthenticated) {
      // 現在のプランIDとキャンペーンコードをクエリパラメータとして保存
      const params = new URLSearchParams();
      params.set('plan_id', selectedPlan.id);
      if (campaignCode) {
        params.set('campaign_code', campaignCode);
      }
      params.set('redirect_to', 'subscription');
      
      router.push(`/login?${params.toString()}`);
      return;
    }
    
    try {
      setCheckoutLoading(true);
      
      // 成功・キャンセル時のリダイレクトURL設定
      const successUrl = `${window.location.origin}/app/subscription/success?session_id={CHECKOUT_SESSION_ID}`;
      const cancelUrl = `${window.location.origin}/subscription/plans`;
      
      const checkoutData = {
        plan_id: selectedPlan.id,
        success_url: successUrl,
        cancel_url: cancelUrl,
        campaign_code: campaignCode || undefined
      };
      
      const { url } = await subscriptionService.createCheckoutSession(checkoutData);
      
      // Stripeのチェックアウトページにリダイレクト
      window.location.href = url;
    } catch (err) {
      console.error('Failed to create checkout session:', err);
      setError('チェックアウトセッションの作成に失敗しました。');
      setCheckoutLoading(false);
    }
  };

  const renderSubscriptionInfo = () => {
    if (!isAuthenticated || !currentSubscription) return null;
    
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-medium text-blue-800">あなたの現在のサブスクリプション</h3>
        <div className="mt-2">
          <p><span className="font-medium">プラン:</span> {currentSubscription.plan_name}</p>
          <p>
            <span className="font-medium">ステータス:</span> 
            <span className={`ml-1 ${currentSubscription.status === 'active' ? 'text-green-600' : 'text-yellow-600'}`}>
              {currentSubscription.status === 'active' ? 'アクティブ' : currentSubscription.status}
            </span>
          </p>
          {currentSubscription.current_period_end && (
            <p>
              <span className="font-medium">次回更新日:</span> 
              {new Date(currentSubscription.current_period_end).toLocaleDateString('ja-JP')}
            </p>
          )}
        </div>
        
        <div className="mt-4">
          <button 
            className="text-blue-700 hover:text-blue-900 text-sm font-medium"
            onClick={async () => {
              try {
                const { url } = await subscriptionService.createPortalSession(window.location.href);
                window.location.href = url;
              } catch (err) {
                console.error('Failed to create customer portal session:', err);
                setError('カスタマーポータルの作成に失敗しました。');
              }
            }}
          >
            サブスクリプション管理ポータルへ
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">サブスクリプションプラン</h1>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}
      
      {renderSubscriptionInfo()}
      
      {isLoading ? (
        <div className="text-center py-12">
          <p>プラン情報を読み込み中...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {plans.map(plan => (
              <PlanCard
                key={plan.id}
                plan={plan}
                currentPlanId={currentSubscription?.id}
                onSelectPlan={handleSelectPlan}
                isLoading={isLoading}
              />
            ))}
          </div>
          
          {selectedPlan && (
            <div className="mt-8 border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">選択したプラン: {selectedPlan.name}</h2>
              
              {/* キャンペーンコード入力フォーム */}
              <CampaignCodeForm
                onSubmit={handleVerifyCampaignCode}
                onApply={handleApplyCampaignCode}
                originalAmount={selectedPlan.amount}
                currency={selectedPlan.currency}
              />
              
              <div className="flex justify-between items-center mt-6">
                <div>
                  <p className="text-lg font-medium">
                    合計金額: 
                    <span className="ml-2 text-xl">
                      {verificationResult?.valid && verificationResult.discounted_amount !== null
                        ? new Intl.NumberFormat('ja-JP', {
                            style: 'currency',
                            currency: selectedPlan.currency.toUpperCase(),
                            minimumFractionDigits: 0
                          }).format(verificationResult.discounted_amount)
                        : new Intl.NumberFormat('ja-JP', {
                            style: 'currency',
                            currency: selectedPlan.currency.toUpperCase(),
                            minimumFractionDigits: 0
                          }).format(selectedPlan.amount)
                      }
                    </span>
                  </p>
                  <p className="text-sm text-gray-500">
                    {selectedPlan.interval === 'month' ? '月額' : '年額'}
                  </p>
                </div>
                
                <button
                  onClick={handleProceedToCheckout}
                  disabled={checkoutLoading}
                  className={`px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    checkoutLoading ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {!isAuthenticated 
                    ? 'ログインして続ける' 
                    : checkoutLoading 
                      ? '処理中...' 
                      : '決済に進む'}
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}; 
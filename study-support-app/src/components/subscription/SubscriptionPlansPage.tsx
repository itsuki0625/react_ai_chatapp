import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { StyledH1, StyledH2 } from '@/components/common/CustomHeadings';
import { SubscriptionPlan, CampaignCodeVerificationResult, Subscription, VerifyCampaignCodeResponse } from '@/types/subscription';
import { subscriptionService } from '@/services/subscriptionService';
import { CampaignCodeForm } from '@/components/subscription/CampaignCodeForm';
import { UserSubscription } from '@/types/user';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { formatAmount } from '@/utils/formatting';
import { Button } from '@/components/common/Button';
import toast from 'react-hot-toast';

interface SubscriptionPlansPageProps {
  isAuthenticated?: boolean;
}

export const SubscriptionPlansPage: React.FC<SubscriptionPlansPageProps> = ({ isAuthenticated: initialIsAuthenticated = false }) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // 認証状態を内部でも管理（props更新にも反応できるように）
  const [isAuthenticated, setIsAuthenticated] = useState(initialIsAuthenticated);
  
  // 内部状態管理
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<UserSubscription | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [campaignCode, setCampaignCode] = useState<string>('');
  const [campaignCodeVerificationResult, setCampaignCodeVerificationResult] = useState<CampaignCodeVerificationResult | null>(null);

  // ローディング状態
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingPlans, setIsLoadingPlans] = useState(true);
  const [isLoadingSubscription, setIsLoadingSubscription] = useState(true);
  const [isCreatingCheckoutSession, setIsCreatingCheckoutSession] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  // エラー状態
  const [error, setError] = useState<string | null>(null);
  const [hasSessionCookie, setHasSessionCookie] = useState(false);
  const [prevAuthState, setPrevAuthState] = useState(initialIsAuthenticated);

  // 初期レンダリング時にpropsからの認証状態を設定
  useEffect(() => {
    // 前回の認証状態と同じ場合はスキップして無限ループを回避
    if (initialIsAuthenticated !== prevAuthState) {
      console.log('SubscriptionPlansPage - initialIsAuthenticated changed:', initialIsAuthenticated);
      console.log('SubscriptionPlansPage - Current isAuthenticated state:', isAuthenticated);
      
      setIsAuthenticated(initialIsAuthenticated);
      setPrevAuthState(initialIsAuthenticated);
    }
  }, [initialIsAuthenticated, isAuthenticated, prevAuthState]);

  // クライアントサイドでのみセッションクッキーをチェック
  const checkSessionCookie = useCallback(() => {
    if (typeof window === 'undefined') {
      return false;
    }
    
    try {
      const hasCookie = document.cookie
        .split(';')
        .map(cookie => cookie.trim())
        .some(cookie => cookie.startsWith('session='));
      
      console.log('SubscriptionPlansPage - checkSessionCookie result:', hasCookie);
      setHasSessionCookie(hasCookie);
      return hasCookie;
    } catch (error) {
      console.error('SubscriptionPlansPage - Error checking session cookie:', error);
      return false;
    }
  }, []);

  // マウント時にセッションクッキーを確認
  useEffect(() => {
    if (typeof window !== 'undefined') {
      checkSessionCookie();
    }
  }, [checkSessionCookie]);

  // セッションクッキーの変更を監視
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    // クッキー変更を検出するための定期チェック（頻度を下げて5秒ごと）
    const intervalId = setInterval(() => {
      const hasCookie = checkSessionCookie();
      
      // Cookieの状態が変わった場合にのみ認証状態を更新
      if (hasCookie && !isAuthenticated) {
        console.log('SubscriptionPlansPage - Cookie check: Session cookie exists but isAuthenticated is false, updating auth state');
        setIsAuthenticated(true);
        setPrevAuthState(true);
      } else if (!hasCookie && isAuthenticated && !initialIsAuthenticated) {
        // 親からの認証状態が優先。親がfalseの場合にのみ更新
        console.log('SubscriptionPlansPage - Cookie check: No session cookie but isAuthenticated is true, updating auth state');
        setIsAuthenticated(false);
        setPrevAuthState(false);
      }
    }, 5000); // 5秒間隔に変更
    
    return () => clearInterval(intervalId);
  }, [checkSessionCookie, isAuthenticated, initialIsAuthenticated]);

  // クエリパラメータから初期選択プランとキャンペーンコードを取得
  useEffect(() => {
    const planId = searchParams?.get('plan');
    const code = searchParams?.get('code');
    
    if (code) {
      setCampaignCode(code);
    }
    
    // 初期データ取得
    fetchData();
    
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // 認証状態が変わった時にデータを再取得
  useEffect(() => {
    console.log('SubscriptionPlansPage - Authentication state changed:', isAuthenticated);
    
    // 認証状態が変わった場合はデータを再取得
    fetchData();
    
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  // データ取得関数
  const fetchData = useCallback(async () => {
    try {
      // サブスクリプションプランの取得（認証不要）
      setIsLoadingPlans(true);
      const fetchedPlans = await subscriptionService.getSubscriptionPlans();
      
      // デバッグログ：取得したプランの詳細を表示
      console.log('Fetched Subscription Plans from Stripe:', JSON.stringify(fetchedPlans, null, 2));
      
      setPlans(fetchedPlans);
      
      // クエリパラメータで指定されたプランIDがあれば、対応するプランを選択
      const planId = searchParams?.get('plan');
      if (planId && fetchedPlans.length > 0) {
        // プランIDは価格IDと同じになるため、どちらでも検索できるように
        const plan = fetchedPlans.find(p => p.id === planId || p.price_id === planId);
        if (plan) {
          setSelectedPlan(plan);
        } else {
          // 指定されたプランIDが見つからない場合は最初のプランを選択
          setSelectedPlan(fetchedPlans[0]);
        }
      } else if (fetchedPlans.length > 0) {
        // クエリパラメータがない場合は最初のプランを選択
        setSelectedPlan(fetchedPlans[0]);
      }

      // ユーザーのサブスクリプション情報を取得（認証が必要）
      if (isAuthenticated) {
        setIsLoadingSubscription(true);
        try {
          const subscription = await subscriptionService.getUserSubscription();
          // SubscriptionからUserSubscriptionに変換
          if (subscription) {
            const userSubscription: UserSubscription = {
              id: subscription.id,
              user_id: subscription.user_id,
              plan_name: subscription.plan_name,
              status: subscription.status,
              stripe_customer_id: subscription.stripe_customer_id || undefined,
              stripe_subscription_id: subscription.stripe_subscription_id || undefined,
              current_period_start: subscription.current_period_start || undefined,
              current_period_end: subscription.current_period_end || undefined,
              cancel_at: subscription.cancel_at || undefined,
              canceled_at: subscription.canceled_at || undefined,
              is_active: subscription.is_active,
              created_at: subscription.created_at,
              updated_at: subscription.updated_at
            };
            setCurrentSubscription(userSubscription);
          } else {
            setCurrentSubscription(null);
          }
        } catch (subscriptionError) {
          console.error('Error fetching user subscription:', subscriptionError);
          // サブスクリプション取得エラーはユーザーエクスペリエンスを中断しない
        } finally {
          setIsLoadingSubscription(false);
        }
      } else {
        // 未認証の場合はサブスクリプション情報をクリア
        setCurrentSubscription(null);
        setIsLoadingSubscription(false);
      }
    } catch (error) {
      console.error('Error fetching subscription data:', error);
      setError('サブスクリプションデータの取得中にエラーが発生しました。');
    } finally {
      setIsLoadingPlans(false);
      setIsLoading(false);
    }
  }, [isAuthenticated, searchParams]);

  // プラン選択ハンドラ
  const handleSelectPlan = (plan: SubscriptionPlan) => {
    setSelectedPlan(plan);
    // 新しいプランを選択したらキャンペーンコード検証結果をリセット
    setCampaignCodeVerificationResult(null);
    setCampaignCode('');
  };

  // キャンペーンコード検証ハンドラ
  const handleVerifyCampaignCode = async (code: string, planId: string) => {
    try {
      const result = await subscriptionService.verifyCampaignCode(code, planId);
      // VerifyCampaignCodeResponseからCampaignCodeVerificationResultに変換
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

  // キャンペーンコード適用ハンドラ
  const handleApplyCampaignCode = (result: VerifyCampaignCodeResponse | CampaignCodeVerificationResult) => {
    // 必要に応じて処理を追加
    console.log('キャンペーンコードが適用されました', result);
  };

  // チェックアウトに進むハンドラ
  const handleProceedToCheckout = async () => {
    setCheckoutLoading(true);
    console.log('SubscriptionPlansPage - handleProceedToCheckout called', { 
      isAuthenticated, 
      selectedPlan
    });
    
    try {
      // isAuthenticatedプロップを信頼する（親コンポーネントで決定された認証状態）
      if (!isAuthenticated) {
        console.log('SubscriptionPlansPage - User not authenticated, redirecting to login');
        const returnUrl = encodeURIComponent(`/subscription/plans?plan=${selectedPlan?.id || ''}`);
        window.location.href = `/login?redirect=${returnUrl}`;
        return;
      }

      if (!selectedPlan) {
        toast.error('プランが選択されていません。');
        setCheckoutLoading(false);
        return;
      }

      setIsCreatingCheckoutSession(true);
      setError(null);

      // リダイレクトURLの設定
      const successUrl = `${window.location.origin}/subscription/success?session_id={CHECKOUT_SESSION_ID}`;
      const cancelUrl = `${window.location.origin}/subscription/plans`;

      // Stripeの価格IDを使用（プランIDと価格IDは同一になる）
      const priceId = selectedPlan.price_id;
      
      console.log('チェックアウトセッション作成リクエスト:', {
        price_id: priceId,
        // plan_idとprice_idは同じ値を使用（DBテーブルなし）
        plan_id: priceId
      });

      try {
        // チェックアウトセッションの作成
        const response = await subscriptionService.createCheckoutSession(
          priceId,
          successUrl,
          cancelUrl,
          {
            user_id: currentSubscription?.user_id || '',
            // メタデータとして保持する必要がある場合はprice_idを使用
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

        // 成功した場合、Stripeのチェックアウトページへリダイレクト
        if (response) {
          window.location.href = response;
        } else {
          toast.error('チェックアウトセッションの作成に失敗しました。');
          console.error('チェックアウトセッションの作成に失敗しました。URLがありません。');
        }
      } catch (apiError) {
        // API呼び出しのエラー処理
        console.error('チェックアウトセッション作成APIエラー:', apiError);
        
        // エラーメッセージを取得
        let errorMessage = 'チェックアウトセッションの作成に失敗しました。';
        
        if (apiError instanceof Error) {
          // 認証エラーの特別なハンドリング
          if (apiError.message.includes('認証') || apiError.message.includes('ログイン')) {
            toast.error('認証セッションが切れています。再ログインしてください。');
            
            // 少し待ってからログインページにリダイレクト
            setTimeout(() => {
              const returnUrl = encodeURIComponent(`/subscription/plans?plan=${selectedPlan?.id || ''}`);
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
      setIsCreatingCheckoutSession(false);
      setCheckoutLoading(false);
    }
  };

  // ローディング中の表示
  if (isLoadingPlans) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <LoadingSpinner />
      </div>
    );
  }

  // エラー時の表示
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

  // 現在のサブスクリプションがある場合の表示
  if (currentSubscription) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <StyledH1 className="mb-6">サブスクリプション</StyledH1>
        <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
          <StyledH2 className="mb-4">現在のサブスクリプション</StyledH2>
          <p className="mb-2">
            <span className="font-semibold">プラン:</span> {currentSubscription.plan_name}
          </p>
          <p className="mb-2">
            <span className="font-semibold">ステータス:</span> {currentSubscription.status === 'active' ? '有効' : '無効'}
          </p>
          {currentSubscription.current_period_end && (
            <p className="mb-2">
              <span className="font-semibold">次回更新日:</span> {new Date(currentSubscription.current_period_end).toLocaleDateString('ja-JP')}
            </p>
          )}
          <p className="mt-4 text-gray-600">
            サブスクリプションの管理や解約は「マイページ」から行うことができます。
          </p>
          <Button 
            onClick={() => router.push('/user/profile')}
            className="mt-4"
          >
            マイページへ
          </Button>
        </div>
      </div>
    );
  }

  // プランリストと選択されたプランの表示
  return (
    <div className="max-w-4xl mx-auto p-6">
      <StyledH1 className="mb-6">サブスクリプションプラン</StyledH1>

      {/* プラン選択部分 */}
      <div className="mb-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`border rounded-lg p-6 cursor-pointer transition-all duration-300 ${
              selectedPlan?.id === plan.id
                ? 'border-blue-500 shadow-lg bg-blue-50'
                : 'border-gray-200 hover:border-blue-300 hover:shadow'
            }`}
            onClick={() => handleSelectPlan(plan)}
          >
            <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
            <p className="text-2xl font-bold mb-3">
              {formatAmount(plan.amount)} <span className="text-sm font-normal">/ 月</span>
            </p>
            <p className="text-gray-600 mb-4">{plan.description}</p>
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
          </div>
        ))}
      </div>

      {/* 選択されたプラン情報と支払いボタン */}
      {selectedPlan && (
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

          {/* キャンペーンコードフォーム */}
          <div className="mb-6">
            <CampaignCodeForm
              onSubmit={(code) => handleVerifyCampaignCode(code, selectedPlan.id)}
              onApply={handleApplyCampaignCode}
              initialCode={campaignCode}
              onCodeChange={setCampaignCode}
              originalAmount={selectedPlan.amount}
              currency={selectedPlan.currency}
            />
          </div>

          {/* チェックアウトボタン */}
          <button
            className={`w-full text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center ${
              isAuthenticated 
                ? 'bg-gradient-to-r from-purple-600 to-indigo-700 hover:from-purple-700 hover:to-indigo-800' 
                : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700'
            }`}
            onClick={handleProceedToCheckout}
            disabled={checkoutLoading || !selectedPlan}
          >
            {checkoutLoading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                処理中...
              </div>
            ) : isAuthenticated ? (
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
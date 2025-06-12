'use client';

import React, { useState } from 'react';
import {
  PaymentElement,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/common/Card';
import { useToast } from '@/hooks/use-toast';
import { Loader2, CreditCard, Shield, AlertCircle } from 'lucide-react';

interface PaymentFormProps {
  amount: number;
  currency: string;
  onSuccess: (paymentIntent: any) => void;
  onError: (error: string) => void;
  loading?: boolean;
}

export function PaymentForm({ 
  amount, 
  currency, 
  onSuccess, 
  onError, 
  loading = false 
}: PaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requires3DSecure, setRequires3DSecure] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setRequires3DSecure(false);

    if (!stripe || !elements) {
      const errorMsg = 'Stripeの読み込みが完了していません。ページを再読み込みしてください。';
      setError(errorMsg);
      onError(errorMsg);
      return;
    }

    setIsProcessing(true);

    try {
      // PaymentElementを使用してconfirmPayment
      const { error: submitError } = await elements.submit();
      if (submitError) {
        throw submitError;
      }

      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/subscription/success`,
        },
        redirect: 'if_required' // 3Dセキュアが必要な場合のみリダイレクト
      });

      if (error) {
        // エラータイプ別の詳細処理
        console.error('Payment confirmation error:', error);
        
        let errorMessage = '決済処理中にエラーが発生しました';
        
        switch (error.type) {
          case 'card_error':
            errorMessage = error.message || 'カード情報に問題があります。カード番号、有効期限、セキュリティコードを確認してください。';
            break;
          case 'validation_error':
            errorMessage = 'カード情報の入力に不備があります。入力内容を確認してください。';
            break;
          case 'api_connection_error':
            errorMessage = 'ネットワーク接続に問題があります。しばらく待ってから再試行してください。';
            break;
          case 'api_error':
            errorMessage = 'システムエラーが発生しました。しばらく待ってから再試行してください。';
            break;
          case 'authentication_error':
            errorMessage = '認証に失敗しました。ページを再読み込みして再試行してください。';
            break;
          case 'rate_limit_error':
            errorMessage = 'リクエストが集中しています。しばらく待ってから再試行してください。';
            break;
          default:
            if (error.message) {
              errorMessage = error.message;
            }
        }
        
        setError(errorMessage);
        onError(errorMessage);
        
        toast({
          title: "決済エラー",
          description: errorMessage,
          variant: "destructive"
        });
      } else if (paymentIntent) {
        // 成功時の処理
        console.log('Payment succeeded:', paymentIntent);
        
        if (paymentIntent.status === 'succeeded') {
          setError(null);
          onSuccess(paymentIntent);
          
          toast({
            title: "決済完了",
            description: "お支払いが正常に処理されました",
            variant: "default"
          });
        } else if (paymentIntent.status === 'requires_action') {
          // 3Dセキュアなどの追加アクションが必要な場合
          setRequires3DSecure(true);
          
          toast({
            title: "認証が必要です",
            description: "カード認証を完了してください",
            variant: "default"
          });
        } else if (paymentIntent.status === 'processing') {
          toast({
            title: "決済処理中",
            description: "決済を処理しています。しばらくお待ちください",
            variant: "default"
          });
        } else {
          const statusError = `予期しない決済状態: ${paymentIntent.status}`;
          setError(statusError);
          onError(statusError);
          
          toast({
            title: "決済状態エラー",
            description: statusError,
            variant: "destructive"
          });
        }
      }
    } catch (err: any) {
      console.error('Unexpected error during payment:', err);
      
      let unexpectedError = '予期せぬエラーが発生しました';
      if (err?.message) {
        unexpectedError = err.message;
      }
      
      setError(unexpectedError);
      onError(unexpectedError);
      
      toast({
        title: "エラー",
        description: unexpectedError,
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          お支払い情報
        </CardTitle>
        <CardDescription>
          お支払い金額: {currency === 'jpy' ? '¥' : currency}{amount.toLocaleString()}
        </CardDescription>
        
        {/* 3Dセキュア説明 */}
        <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-2 rounded-lg">
          <Shield className="h-4 w-4" />
          <span>3Dセキュア認証に対応しており、安全に決済できます</span>
        </div>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* エラー表示 */}
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}

          {/* 3Dセキュア認証中表示 */}
          {requires3DSecure && (
            <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-3 rounded-lg border border-blue-200">
              <Shield className="h-4 w-4" />
              <span>3Dセキュア認証が進行中です。ポップアップまたはリダイレクト画面で認証を完了してください。</span>
            </div>
          )}

          {/* PaymentElement - Stripe ElementsのUI */}
          <div className="space-y-4">
            <PaymentElement 
              options={{
                layout: 'tabs',
                fields: {
                  billingDetails: {
                    name: 'auto',
                    email: 'auto',
                    phone: 'never',
                    address: 'auto',
                  }
                },
                wallets: {
                  applePay: 'auto',
                  googlePay: 'auto'
                }
              }}
            />
          </div>

          {/* セキュリティ情報 */}
          <div className="text-xs text-gray-500 space-y-1">
            <p>• カード情報は暗号化されて安全に処理されます</p>
            <p>• 3Dセキュア認証により不正利用を防止します</p>
            <p>• Stripe社による決済処理で安心してご利用いただけます</p>
          </div>

          {/* 送信ボタン */}
          <Button
            type="submit"
            className="w-full"
            disabled={!stripe || !elements || isProcessing || loading}
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {requires3DSecure ? '認証中...' : '処理中...'}
              </>
            ) : (
              <>
                <CreditCard className="mr-2 h-4 w-4" />
                ¥{amount.toLocaleString()}を支払う
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

// 3Dセキュア対応の実装ポイント:
// 1. confirmPayment() で自動的に3Dセキュア処理
// 2. redirect: 'if_required' で必要時のみリダイレクト
// 3. PaymentElementが3Dセキュア認証UIを自動表示
// 4. error.type による詳細なエラーハンドリング
// 5. paymentIntent.status による状態管理 
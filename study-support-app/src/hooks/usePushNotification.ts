import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

export const usePushNotification = () => {
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [isSupported, setIsSupported] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkPushSupport();
  }, []);

  const checkPushSupport = async () => {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        setIsSupported(false);
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      const existingSubscription = await registration.pushManager.getSubscription();
      setSubscription(existingSubscription);
      setIsSupported(true);
    } catch (err) {
      setError('プッシュ通知のサポート確認中にエラーが発生しました');
      console.error('Push support check error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const subscribe = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const registration = await navigator.serviceWorker.ready;
      const existingSubscription = await registration.pushManager.getSubscription();

      if (existingSubscription) {
        setSubscription(existingSubscription);
        return;
      }

      // VAPID公開鍵をサーバーから取得
      const { data: { publicKey } } = await apiClient.get('/push/vapid-public-key');

      const newSubscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: publicKey,
      });

      // サブスクリプション情報をサーバーに送信
      await apiClient.post('/push/subscriptions', {
        subscription: newSubscription.toJSON(),
      });

      setSubscription(newSubscription);
    } catch (err) {
      setError('プッシュ通知の登録中にエラーが発生しました');
      console.error('Push subscription error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const unsubscribe = async () => {
    try {
      setIsLoading(true);
      setError(null);

      if (!subscription) {
        return;
      }

      await subscription.unsubscribe();

      // サーバーからサブスクリプションを削除
      await apiClient.delete('/push/subscriptions', {
        data: { subscription: subscription.toJSON() },
      });

      setSubscription(null);
    } catch (err) {
      setError('プッシュ通知の解除中にエラーが発生しました');
      console.error('Push unsubscription error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    subscription,
    isSupported,
    isLoading,
    error,
    subscribe,
    unsubscribe,
  };
}; 
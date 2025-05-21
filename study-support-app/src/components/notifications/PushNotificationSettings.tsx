import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Bell } from 'lucide-react';
import { toast } from 'sonner';

export const PushNotificationSettings = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [isSubscribing, setIsSubscribing] = useState(false);

  // プッシュ通知のサブスクリプション状態を取得
  const { data: subscription, isLoading } = useQuery({
    queryKey: ['push-subscription'],
    queryFn: async () => {
      const response = await apiClient.get('/push/subscription');
      return response.data;
    },
  });

  // プッシュ通知のサブスクリプションを更新
  const updateSubscription = useMutation({
    mutationFn: async (subscription: PushSubscription | null) => {
      if (subscription) {
        await apiClient.post('/push/subscription', {
          subscription: subscription.toJSON(),
        });
      } else {
        await apiClient.delete('/push/subscription');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['push-subscription'] });
      toast.success(subscription ? 'プッシュ通知を無効化しました' : 'プッシュ通知を有効化しました');
    },
    onError: () => {
      setError('プッシュ通知の設定中にエラーが発生しました');
      toast.error('プッシュ通知の設定に失敗しました');
    },
  });

  const handleSubscribe = async () => {
    try {
      setIsSubscribing(true);
      setError(null);

      // プッシュ通知の権限を要求
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        throw new Error('プッシュ通知の権限が拒否されました');
      }

      // サービスワーカーを登録
      const registration = await navigator.serviceWorker.register('/service-worker.js');
      await navigator.serviceWorker.ready;

      // プッシュ通知のサブスクリプションを作成
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY,
      });

      // サブスクリプションをサーバーに送信
      await updateSubscription.mutateAsync(subscription);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'プッシュ通知の設定中にエラーが発生しました');
    } finally {
      setIsSubscribing(false);
    }
  };

  const handleUnsubscribe = async () => {
    try {
      setError(null);

      // 現在のサブスクリプションを取得
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        // サブスクリプションを解除
        await subscription.unsubscribe();
        await updateSubscription.mutateAsync(null);
      }
    } catch (err) {
      setError('プッシュ通知の解除中にエラーが発生しました');
    }
  };

  if (isLoading) {
    return <div>読み込み中...</div>;
  }

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">プッシュ通知</h3>
          <p className="text-sm text-muted-foreground mt-1">
            ブラウザでプッシュ通知を受け取ることができます。
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <p className="text-sm font-medium">
              {subscription ? 'プッシュ通知が有効です' : 'プッシュ通知が無効です'}
            </p>
            <p className="text-sm text-muted-foreground">
              {subscription
                ? 'ブラウザでプッシュ通知を受け取ります'
                : 'プッシュ通知を有効にすると、ブラウザで通知を受け取ることができます'}
            </p>
          </div>
          <Button
            onClick={subscription ? handleUnsubscribe : handleSubscribe}
            disabled={isSubscribing}
          >
            <Bell className="w-4 h-4 mr-2" />
            {subscription ? '無効化' : '有効化'}
          </Button>
        </div>
      </div>
    </Card>
  );
}; 
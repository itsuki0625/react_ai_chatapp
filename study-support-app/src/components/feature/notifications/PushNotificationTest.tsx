import { useState } from 'react';
import { usePushNotification } from '@/hooks/usePushNotification';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Bell } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

export const PushNotificationTest = () => {
  const { subscription, isSupported, isLoading, error: pushError } = usePushNotification();
  const [title, setTitle] = useState('テスト通知');
  const [message, setMessage] = useState('これはテスト通知です。');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleTest = async () => {
    if (!subscription) {
      setError('プッシュ通知が有効になっていません。');
      return;
    }

    try {
      setIsSending(true);
      setError(null);
      setSuccess(false);

      await apiClient.post('/push/test', {
        title,
        message,
        subscription: subscription.toJSON(),
      });

      setSuccess(true);
    } catch (err) {
      setError('テスト通知の送信中にエラーが発生しました。');
      console.error('Test notification error:', err);
    } finally {
      setIsSending(false);
    }
  };

  if (isLoading) {
    return <div>読み込み中...</div>;
  }

  if (!isSupported) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          お使いのブラウザはプッシュ通知をサポートしていません。
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">プッシュ通知テスト</h3>
          <p className="text-sm text-muted-foreground mt-1">
            プッシュ通知のテストを送信できます。
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="title">タイトル</Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="通知のタイトル"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="message">メッセージ</Label>
          <Input
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="通知のメッセージ"
          />
        </div>

        <Button
          onClick={handleTest}
          disabled={isSending || !subscription}
          className="w-full"
        >
          <Bell className="w-4 h-4 mr-2" />
          {isSending ? '送信中...' : 'テスト通知を送信'}
        </Button>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {pushError && (
          <Alert variant="destructive">
            <AlertDescription>{pushError}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert>
            <AlertDescription>
              テスト通知を送信しました。通知が届くまでお待ちください。
            </AlertDescription>
          </Alert>
        )}

        {!subscription && (
          <Alert variant="destructive">
            <AlertDescription>
              プッシュ通知を有効にしてください。
            </AlertDescription>
          </Alert>
        )}
      </div>
    </Card>
  );
}; 
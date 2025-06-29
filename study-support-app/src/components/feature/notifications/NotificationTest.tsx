import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Bell } from 'lucide-react';
import { toast } from 'sonner';

export const NotificationTest = () => {
  const [title, setTitle] = useState('テスト通知');
  const [message, setMessage] = useState('これはテスト通知です。');
  const [error, setError] = useState<string | null>(null);

  // テスト通知の送信
  const sendTestNotification = useMutation({
    mutationFn: async () => {
      await apiClient.post('/notifications/test', {
        title,
        message,
      });
    },
    onSuccess: () => {
      toast.success('テスト通知を送信しました');
    },
    onError: () => {
      setError('テスト通知の送信中にエラーが発生しました');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    sendTestNotification.mutate();
  };

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">通知テスト</h3>
          <p className="text-sm text-muted-foreground mt-1">
            通知のテストを送信できます。
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
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
            type="submit"
            disabled={sendTestNotification.isPending}
            className="w-full"
          >
            <Bell className="w-4 h-4 mr-2" />
            {sendTestNotification.isPending ? '送信中...' : 'テスト通知を送信'}
          </Button>
        </form>
      </div>
    </Card>
  );
}; 
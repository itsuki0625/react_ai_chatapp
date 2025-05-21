import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Bell, Mail, Clock } from 'lucide-react';
import { toast } from 'sonner';

interface NotificationSettings {
  email_notifications: boolean;
  browser_notifications: boolean;
  system_notifications: boolean;
  chat_notifications: boolean;
  document_notifications: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
}

export const NotificationSettings = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  // 通知設定の取得
  const { data: settings, isLoading } = useQuery<NotificationSettings>({
    queryKey: ['notification-settings'],
    queryFn: async () => {
      const response = await apiClient.get('/settings/notifications');
      return response.data;
    },
  });

  // 通知設定の更新
  const updateSettings = useMutation({
    mutationFn: async (newSettings: Partial<NotificationSettings>) => {
      await apiClient.patch('/settings/notifications', newSettings);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-settings'] });
      toast.success('通知設定を更新しました');
    },
    onError: () => {
      setError('通知設定の更新中にエラーが発生しました');
      toast.error('通知設定の更新に失敗しました');
    },
  });

  const handleToggle = (key: keyof NotificationSettings) => {
    if (!settings) return;

    const newValue = !settings[key];
    updateSettings.mutate({ [key]: newValue });
  };

  const handleTimeChange = (key: 'quiet_hours_start' | 'quiet_hours_end', value: string) => {
    if (!settings) return;

    updateSettings.mutate({ [key]: value });
  };

  if (isLoading) {
    return <div>読み込み中...</div>;
  }

  if (!settings) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          通知設定の取得に失敗しました。
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">通知設定</h3>
          <p className="text-sm text-muted-foreground mt-1">
            通知の種類と方法を設定できます。
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>メール通知</Label>
              <p className="text-sm text-muted-foreground">
                メールで通知を受け取ります
              </p>
            </div>
            <Switch
              checked={settings.email_notifications}
              onCheckedChange={() => handleToggle('email_notifications')}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>ブラウザ通知</Label>
              <p className="text-sm text-muted-foreground">
                ブラウザで通知を受け取ります
              </p>
            </div>
            <Switch
              checked={settings.browser_notifications}
              onCheckedChange={() => handleToggle('browser_notifications')}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>システム通知</Label>
              <p className="text-sm text-muted-foreground">
                システムからの通知を受け取ります
              </p>
            </div>
            <Switch
              checked={settings.system_notifications}
              onCheckedChange={() => handleToggle('system_notifications')}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>チャット通知</Label>
              <p className="text-sm text-muted-foreground">
                チャットメッセージの通知を受け取ります
              </p>
            </div>
            <Switch
              checked={settings.chat_notifications}
              onCheckedChange={() => handleToggle('chat_notifications')}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>ドキュメント通知</Label>
              <p className="text-sm text-muted-foreground">
                ドキュメント関連の通知を受け取ります
              </p>
            </div>
            <Switch
              checked={settings.document_notifications}
              onCheckedChange={() => handleToggle('document_notifications')}
            />
          </div>
        </div>

        <div className="pt-6 border-t">
          <div className="flex items-center justify-between mb-4">
            <div className="space-y-0.5">
              <Label>通知を一時停止</Label>
              <p className="text-sm text-muted-foreground">
                指定した時間帯に通知を受け取らないようにします
              </p>
            </div>
            <Switch
              checked={settings.quiet_hours_enabled}
              onCheckedChange={() => handleToggle('quiet_hours_enabled')}
            />
          </div>

          {settings.quiet_hours_enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>開始時間</Label>
                <input
                  type="time"
                  value={settings.quiet_hours_start}
                  onChange={(e) => handleTimeChange('quiet_hours_start', e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div className="space-y-2">
                <Label>終了時間</Label>
                <input
                  type="time"
                  value={settings.quiet_hours_end}
                  onChange={(e) => handleTimeChange('quiet_hours_end', e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}; 
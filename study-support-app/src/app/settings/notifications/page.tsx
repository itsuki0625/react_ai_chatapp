import { Metadata } from 'next';
import { NotificationSettings } from '@/components/notifications/NotificationSettings';
import { PushNotificationSettings } from '@/components/notifications/PushNotificationSettings';
import { NotificationTest } from '@/components/notifications/NotificationTest';

export const metadata: Metadata = {
  title: '通知設定 | Study Support',
  description: '通知設定を管理できます',
};

export default function NotificationSettingsPage() {
  return (
    <div className="container py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">通知設定</h1>
        <p className="text-muted-foreground mt-2">
          通知の設定を管理できます。
        </p>
      </div>

      <div className="grid gap-8">
        <NotificationSettings />
        <PushNotificationSettings />
        <NotificationTest />
      </div>
    </div>
  );
} 
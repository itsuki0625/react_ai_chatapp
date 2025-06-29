import { Metadata } from 'next';
import { NotificationHistory } from '@/components/feature/notifications/NotificationHistory';

export const metadata: Metadata = {
  title: '通知 | Study Support',
  description: '通知履歴を確認できます',
};

export default function NotificationsPage() {
  return (
    <div className="container py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">通知</h1>
        <p className="text-muted-foreground mt-2">
          通知履歴を確認できます。
        </p>
      </div>
      <NotificationHistory />
    </div>
  );
} 
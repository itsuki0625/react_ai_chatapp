import React from 'react';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { NotificationSettingsManagement } from '@/components/feature/admin/NotificationSettingsManagement'; // 作成したコンポーネントをインポート

const AdminNotificationSettingsPage = () => {
  return (
    <AdminLayout>
      <div className="container mx-auto py-6 px-4 md:px-6">
        <h1 className="text-2xl font-semibold mb-6">通知設定管理</h1>
        <NotificationSettingsManagement />
      </div>
    </AdminLayout>
  );
};

export default AdminNotificationSettingsPage; 
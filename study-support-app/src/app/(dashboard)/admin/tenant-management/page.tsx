'use client';

import SystemTenantManagement from '@/components/feature/admin/SystemTenantManagement';
import { AdminLayout } from '@/components/layout/AdminLayout';

export default function AdminTenantManagementPage() {
  return (
    <AdminLayout>
      <SystemTenantManagement />
    </AdminLayout>
  );
}

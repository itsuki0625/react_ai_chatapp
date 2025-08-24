'use client';

import AdminDashboard from '@/components/feature/admin/AdminDashboardPage';
import { AdminLayout } from '@/components/layout/AdminLayout';

export default function Page() {
  return (
    <AdminLayout>
      <AdminDashboard />
    </AdminLayout>
  );
}
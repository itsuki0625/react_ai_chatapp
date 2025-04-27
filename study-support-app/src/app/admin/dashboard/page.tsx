'use client';

import AdminDashboard from '@/components/admin/AdminDashboardPage';
import { AdminNavBar } from '@/components/common/AdminNavBar';

export default function Page() {
  return (
    <div>
      <AdminNavBar />
      <AdminDashboard />
    </div>
  );
}
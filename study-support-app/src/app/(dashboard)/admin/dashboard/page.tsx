'use client';

import AdminDashboard from '@/components/feature/admin/AdminDashboardPage';
import { AdminNavBar } from '@/components/feature/admin/AdminNavBar';

export default function Page() {
  return (
    <div>
      <AdminNavBar />
      <AdminDashboard />
    </div>
  );
}
'use client';

import React from 'react';
import { SubscriptionManagement } from '@/components/admin/SubscriptionManagement';
import { AdminNavBar } from '@/components/common/AdminNavBar';

export default function SubscriptionManagementPage() {
  return (
    <div>
      <AdminNavBar />
      <SubscriptionManagement />
    </div>
  );
} 
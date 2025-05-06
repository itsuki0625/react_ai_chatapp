'use client';

import React from 'react';
import { SubscriptionManagement } from '@/components/admin/SubscriptionManagement';
import { AdminNavBar } from '@/components/common/AdminNavBar';

export default function SubscriptionManagementPage() {
    return (
        <div className="p-4">
            <AdminNavBar />
            <div className="mt-6">
                <SubscriptionManagement />
            </div>
        </div>
    );
} 
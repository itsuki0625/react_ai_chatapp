'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SubscriptionManagement } from '@/components/admin/SubscriptionManagement';
import { useAuth } from '@/hooks/useAuth';

export default function SubscriptionManagementPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      const isAdmin = user && 
                     user.role && 
                     user.role.permissions && 
                     user.role.permissions.includes('admin');
      
      if (!isAdmin) {
        router.push('/');
      } else {
        setIsAuthorized(true);
      }
    }
  }, [user, isLoading, router]);

  if (isLoading || !isAuthorized) {
    return <div className="flex justify-center items-center h-screen">読み込み中...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">サブスクリプション管理</h1>
      <SubscriptionManagement />
    </div>
  );
} 
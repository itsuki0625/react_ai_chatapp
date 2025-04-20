'use client';

import React from 'react';
import { useSession } from 'next-auth/react';
import { SubscriptionPlansPage } from '@/components/subscription/SubscriptionPlansPage';

export default function SubscriptionPlans() {
  const { status } = useSession();
  const isAuthenticated = status === 'authenticated';

  return (
    <SubscriptionPlansPage isAuthenticated={isAuthenticated} />
  );
} 
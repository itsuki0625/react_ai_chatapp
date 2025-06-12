'use client';

import React from 'react';
import { PaymentHistoryTable } from '@/components/subscription/PaymentHistoryTable';

export default function PaymentHistoryPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">決済履歴</h1>
        <p className="text-gray-600">
          あなたの決済履歴とサブスクリプション取引を確認できます。
        </p>
      </div>
      
      <PaymentHistoryTable />
    </div>
  );
} 
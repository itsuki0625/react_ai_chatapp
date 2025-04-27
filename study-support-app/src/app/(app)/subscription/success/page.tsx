'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function SubscriptionSuccess() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    // セッションIDをURLから取得
    const session = searchParams.get('session_id');
    setSessionId(session);

    // 5秒後にダッシュボードに遷移
    const timer = setTimeout(() => {
      router.push('/dashboard');
    }, 5000);

    return () => clearTimeout(timer);
  }, [searchParams, router]);

  return (
    <div className="max-w-md mx-auto mt-12 p-6 bg-white rounded-lg shadow-md">
      <div className="text-center">
        <div className="rounded-full bg-green-100 h-24 w-24 flex items-center justify-center mx-auto">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        
        <h1 className="text-2xl font-bold text-gray-800 mt-6">
          支払いが完了しました
        </h1>
        
        <p className="text-gray-600 mt-2">
          サブスクリプションの購入ありがとうございます。
          自動的にダッシュボードに移動します。
        </p>
        
        {sessionId && (
          <p className="text-xs text-gray-500 mt-4">
            セッションID: {sessionId}
          </p>
        )}
        
        <div className="mt-8">
          <Link
            href="/dashboard"
            className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            ダッシュボードへ
          </Link>
        </div>
      </div>
    </div>
  );
} 
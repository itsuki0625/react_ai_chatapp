import React from 'react';
import Link from 'next/link';

export default function PaymentRequiredPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md text-center">
        <h1 className="text-2xl font-bold text-orange-600">お支払いのお願い</h1>
        <p className="text-gray-600">
          サービスのご利用を継続するには、お支払いが必要です。
        </p>
        <p className="text-gray-600">
          以下のボタンから決済ページへ進み、手続きを完了してください。
        </p>
        {/* TODO: 実際の決済ページへのリンクに置き換える */}
        <Link href="/subscription" legacyBehavior>
          <a className="inline-block mt-4 px-6 py-3 text-lg font-medium text-white bg-green-600 rounded-md hover:bg-green-700">
            決済ページへ進む
          </a>
        </Link>
         <div className="pt-4">
           <Link href="/login" className="text-sm text-blue-600 hover:underline">
              ログインページに戻る
            </Link>
        </div>
      </div>
    </div>
  );
} 
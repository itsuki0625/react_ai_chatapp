import React from 'react';
import Link from 'next/link';

export default function InactiveAccountPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md text-center">
        <h1 className="text-2xl font-bold text-red-600">アカウントが無効です</h1>
        <p className="text-gray-600">
          現在、お客様のアカウントは無効な状態です。
        </p>
        <p className="text-gray-600">
          アカウントの再開については、サポートまでお問い合わせください。
        </p>
        {/* TODO: サポートページや連絡先へのリンクを追加 */}
        {/* <Link href="/support">サポート</Link> */}
         <div className="pt-4">
           <Link href="/login" className="text-sm text-blue-600 hover:underline">
              ログインページに戻る
            </Link>
        </div>
      </div>
    </div>
  );
} 
import React from 'react';
import Link from 'next/link';

export default function PendingActivationPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md text-center">
        <h1 className="text-2xl font-bold text-gray-900">アカウント有効化のお願い</h1>
        <p className="text-gray-600">
          ご登録ありがとうございます。アカウントを有効化するために、登録されたメールアドレスに送信された確認メールをご確認ください。
        </p>
        <p className="text-gray-600">
          メールが見当たらない場合は、迷惑メールフォルダもご確認ください。
        </p>
        {/* TODO: 必要であればメール再送信ボタンを追加 */}
        {/* <button className="mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
          確認メールを再送信
        </button> */}
        <div className="pt-4">
           <Link href="/login" className="text-sm text-blue-600 hover:underline">
              ログインページに戻る
            </Link>
        </div>
      </div>
    </div>
  );
} 
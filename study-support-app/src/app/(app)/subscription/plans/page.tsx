'use client';

import React, { Suspense } from 'react';
// import { useSession } from 'next-auth/react'; // Remove unused import
import { SubscriptionPlansPage } from '@/components/subscription/SubscriptionPlansPage';
import { StyledH2 } from '@/components/common/CustomHeadings';

export default function SubscriptionPlans() {
  // const { status } = useSession(); // Remove unused variable

  // FAQデータ
  const faqItems = [
    {
      question: 'サブスクリプションの支払いはいつ行われますか？',
      answer: 'サブスクリプションの支払いは毎月の同じ日に自動的に行われます。初回支払い日が毎月の請求日となります。'
    },
    {
      question: 'サブスクリプションはいつでもキャンセルできますか？',
      answer: 'はい、いつでもマイページからサブスクリプションをキャンセルすることができます。キャンセル後も、支払い済みの期間の終了までサービスを利用することができます。'
    },
    {
      question: '支払い方法を変更することはできますか？',
      answer: 'はい、マイページから支払い方法を変更することができます。クレジットカードやデビットカードなど、複数の支払い方法に対応しています。'
    },
    {
      question: 'プランを途中で変更することはできますか？',
      answer: 'はい、いつでもプランを変更することができます。アップグレードの場合は即時反映され、ダウングレードの場合は次回の請求サイクルから適用されます。'
    },
    {
      question: '請求書や領収書は発行されますか？',
      answer: 'はい、すべての支払いに対して電子請求書が発行され、登録されたメールアドレスに送信されます。マイページからも過去の請求書をダウンロードすることができます。'
    }
  ];

  return (
      <div className="flex flex-1">
        <div className="flex-1">
          <div className="min-h-screen bg-gray-50">
            {/* ヘッダーセクション */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-100 border-b border-gray-200 py-12 px-4">
              <div className="max-w-4xl mx-auto text-center">
                <h1 className="text-2xl md:text-3xl font-semibold mb-3 text-gray-800">
                  学習を支えるサブスクリプションプラン
                </h1>
                <p className="text-base md:text-lg text-gray-600 max-w-2xl mx-auto">
                  目標達成をサポートする最適なプランをお選びいただけます。お支払いは安全に処理され、いつでも管理可能です。
                </p>
              </div>
            </div>

            {/* メインコンテンツ */}
            <div className="py-8 px-4">
              <Suspense fallback={<div className="text-center p-8">プランを読み込み中...</div>}>
                <SubscriptionPlansPage />
              </Suspense>
            </div>

            {/* FAQ セクション */}
            <div className="max-w-4xl mx-auto py-12 px-6">
              <StyledH2 className="text-center mb-8">よくある質問</StyledH2>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden divide-y divide-gray-200">
                {faqItems.map((item, index) => (
                  <details key={index} className="group p-4">
                    <summary className="flex justify-between items-center font-medium cursor-pointer list-none">
                      <span>{item.question}</span>
                      <span className="transition group-open:rotate-180">
                        <svg fill="none" height="24" width="24" strokeWidth="1.5" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7"></path>
                        </svg>
                      </span>
                    </summary>
                    <p className="mt-3 text-gray-600">{item.answer}</p>
                  </details>
                ))}
              </div>
            </div>

            {/* サポートセクション */}
            <div className="bg-gray-100 py-10 px-4">
              <div className="max-w-4xl mx-auto text-center">
                <StyledH2 className="mb-4">サポートが必要ですか？</StyledH2>
                <p className="text-gray-600 mb-6">
                  サブスクリプションについてご不明な点がございましたら、カスタマーサポートまでお気軽にお問い合わせください。
                </p>
                <div className="flex flex-col sm:flex-row justify-center gap-4">
                  <a
                    href="/contact"
                    className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    お問い合わせ
                  </a>
                  <a
                    href="/faq"
                    className="inline-flex items-center justify-center px-5 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    よくある質問をすべて見る
                  </a>
                </div>
              </div>
            </div>

            {/* フッター */}
            <footer className="bg-white py-6 px-4 border-t">
              <div className="max-w-4xl mx-auto text-center text-sm text-gray-500">
                <p className="mb-2">
                  支払いはStripeによって安全に処理されます。クレジットカード情報は当社のサーバーには保存されません。
                </p>
                <hr className="my-4 border-gray-200" />
                <p>
                  サブスクリプションに関する詳細は<a href="/terms" className="text-indigo-600 hover:underline">利用規約</a>をご覧ください。
                  <br />
                  &copy; {new Date().getFullYear()} MONONO Inc. All rights reserved.
                </p>
              </div>
            </footer>
          </div>
        </div>
      </div>
  );
}

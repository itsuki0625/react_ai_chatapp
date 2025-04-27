import React, { useEffect, useState } from 'react';
import { PaymentHistory } from '@/types/subscription';
import { subscriptionService } from '@/services/subscriptionService';

export const PaymentHistoryPage: React.FC = () => {
  const [paymentHistory, setPaymentHistory] = useState<PaymentHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const limit = 10;

  useEffect(() => {
    const fetchPaymentHistory = async () => {
      try {
        setIsLoading(true);
        const history = await subscriptionService.getPaymentHistory(page * limit, limit);
        setPaymentHistory(history);
      } catch (err) {
        console.error('Failed to fetch payment history:', err);
        setError('支払い履歴の取得に失敗しました。');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPaymentHistory();
  }, [page]);

  // 金額をフォーマット
  const formatAmount = (amount: number, currency: string): string => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: currency.toUpperCase(),
      minimumFractionDigits: 0
    }).format(amount);
  };

  // 日付をフォーマット
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 支払い状況のステータスラベルを取得
  const getStatusLabel = (status: string): { label: string; className: string } => {
    switch (status) {
      case 'succeeded':
        return { label: '成功', className: 'bg-green-100 text-green-800' };
      case 'pending':
        return { label: '処理中', className: 'bg-yellow-100 text-yellow-800' };
      case 'failed':
        return { label: '失敗', className: 'bg-red-100 text-red-800' };
      default:
        return { label: status, className: 'bg-gray-100 text-gray-800' };
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">支払い履歴</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12">
          <p>支払い履歴を読み込み中...</p>
        </div>
      ) : paymentHistory.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 p-6 rounded-lg text-center">
          <p className="text-gray-600">支払い履歴がありません</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  日付
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  金額
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  支払い方法
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ステータス
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paymentHistory.map((payment) => {
                const status = getStatusLabel(payment.status);
                return (
                  <tr key={payment.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(payment.payment_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatAmount(payment.amount, payment.currency)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {payment.payment_method || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${status.className}`}>
                        {status.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ページネーション */}
      {paymentHistory.length > 0 && (
        <div className="flex justify-between items-center mt-6">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className={`px-4 py-2 border rounded-md ${
              page === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            前へ
          </button>
          <span className="text-sm text-gray-700">
            ページ {page + 1}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={paymentHistory.length < limit}
            className={`px-4 py-2 border rounded-md ${
              paymentHistory.length < limit
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            次へ
          </button>
        </div>
      )}
    </div>
  );
}; 
'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/common/Card';
import { apiClient } from '@/lib/api/client';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { 
  Search, 
  Download, 
  Filter, 
  CreditCard, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  XCircle,
  Shield
} from 'lucide-react';

interface PaymentHistoryItem {
  id: string;
  user_id: string;
  subscription_id?: string;
  stripe_payment_intent_id?: string;
  stripe_invoice_id?: string;
  amount: number;
  currency: string;
  status: string;
  payment_method?: string;
  payment_date: string;
  created_at: string;
  updated_at: string;
}

interface PaymentHistoryResponse {
  items: PaymentHistoryItem[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

const fetchPaymentHistory = async (params: {
  skip?: number;
  limit?: number;
  status?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}): Promise<PaymentHistoryResponse> => {
  const queryParams = new URLSearchParams();
  
  if (params.skip) queryParams.append('skip', params.skip.toString());
  if (params.limit) queryParams.append('limit', params.limit.toString());
  if (params.status && params.status !== 'all') queryParams.append('status', params.status);
  if (params.search) queryParams.append('search', params.search);
  if (params.date_from) queryParams.append('date_from', params.date_from);
  if (params.date_to) queryParams.append('date_to', params.date_to);

  const response = await apiClient.get<PaymentHistoryItem[]>(
    `/subscriptions/payment-history?${queryParams.toString()}`
  );
  
  // APIレスポンスを統一フォーマットに変換
  return {
    items: response.data,
    total: response.data.length,
    page: Math.floor((params.skip || 0) / (params.limit || 10)) + 1,
    size: response.data.length,
    has_next: response.data.length === (params.limit || 10)
  };
};

export function PaymentHistoryTable() {
  const [filters, setFilters] = useState({
    skip: 0,
    limit: 20,
    status: 'all',
    search: '',
    date_from: '',
    date_to: ''
  });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['payment-history', filters],
    queryFn: () => fetchPaymentHistory(filters),
    staleTime: 30000, // 30秒間キャッシュ
  });

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'succeeded':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
            <CheckCircle className="w-3 h-3 mr-1" />
            成功
          </Badge>
        );
      case 'failed':
      case 'canceled':
        return (
          <Badge variant="destructive">
            <XCircle className="w-3 h-3 mr-1" />
            失敗
          </Badge>
        );
      case 'processing':
        return (
          <Badge variant="secondary">
            <Clock className="w-3 h-3 mr-1" />
            処理中
          </Badge>
        );
      case 'requires_action':
        return (
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            <Shield className="w-3 h-3 mr-1" />
            認証要求
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {status}
          </Badge>
        );
    }
  };

  const getPaymentMethodDisplay = (method: string | undefined) => {
    if (!method) return '不明';
    
    if (method.includes('card')) return 'クレジットカード';
    if (method.includes('apple_pay')) return 'Apple Pay';
    if (method.includes('google_pay')) return 'Google Pay';
    return method;
  };

  const handleExportCSV = () => {
    if (!data?.items) return;

    const csvHeaders = [
      '決済ID',
      '金額',
      '通貨',
      'ステータス',
      '決済方法',
      '決済日時',
      'Stripe PaymentIntent ID'
    ];

    const csvData = data.items.map(item => [
      item.id,
      item.amount.toString(),
      item.currency.toUpperCase(),
      item.status,
      getPaymentMethodDisplay(item.payment_method),
      format(new Date(item.payment_date), 'yyyy/MM/dd HH:mm:ss', { locale: ja }),
      item.stripe_payment_intent_id || ''
    ]);

    const csvContent = [csvHeaders, ...csvData]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `payment_history_${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`;
    link.click();
  };

  const handleFilterChange = (key: string, value: string | number) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      skip: key !== 'skip' ? 0 : (typeof value === 'number' ? value : parseInt(value) || 0) // フィルター変更時はページをリセット
    }));
  };

  const handleNextPage = () => {
    setFilters(prev => ({
      ...prev,
      skip: prev.skip + prev.limit
    }));
  };

  const handlePrevPage = () => {
    setFilters(prev => ({
      ...prev,
      skip: Math.max(0, prev.skip - prev.limit)
    }));
  };

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="w-5 h-5" />
            <span>決済履歴の取得に失敗しました</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            決済履歴
          </CardTitle>
          <CardDescription>
            あなたの決済履歴を確認できます。3Dセキュア認証の状況も含まれます。
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {/* フィルタリングセクション */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="space-y-2">
              <label className="text-sm font-medium">検索</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="PaymentIntent ID..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">ステータス</label>
              <Select 
                value={filters.status} 
                onValueChange={(value) => handleFilterChange('status', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">すべて</SelectItem>
                  <SelectItem value="succeeded">成功</SelectItem>
                  <SelectItem value="failed">失敗</SelectItem>
                  <SelectItem value="processing">処理中</SelectItem>
                  <SelectItem value="requires_action">認証要求</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">開始日</label>
              <Input
                type="date"
                value={filters.date_from}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">終了日</label>
              <Input
                type="date"
                value={filters.date_to}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
              />
            </div>
          </div>

          {/* 操作ボタン */}
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isLoading}
              >
                <Filter className="w-4 h-4 mr-2" />
                更新
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportCSV}
                disabled={!data?.items?.length}
              >
                <Download className="w-4 h-4 mr-2" />
                CSVエクスポート
              </Button>
            </div>
            
            <div className="text-sm text-gray-600">
              {data?.total ? `${data.total}件中 ${filters.skip + 1}-${Math.min(filters.skip + filters.limit, data.total)}件` : '0件'}
            </div>
          </div>

          {/* テーブル */}
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>決済日時</TableHead>
                  <TableHead>金額</TableHead>
                  <TableHead>ステータス</TableHead>
                  <TableHead>決済方法</TableHead>
                  <TableHead>PaymentIntent ID</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8">
                      <div className="flex items-center justify-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        読み込み中...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : data?.items?.length ? (
                  data.items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        {format(new Date(item.payment_date), 'yyyy/MM/dd HH:mm', { locale: ja })}
                      </TableCell>
                      <TableCell className="font-mono">
                        {item.currency.toUpperCase() === 'JPY' ? '¥' : item.currency}
                        {item.amount.toLocaleString()}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(item.status)}
                      </TableCell>
                      <TableCell>
                        {getPaymentMethodDisplay(item.payment_method)}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {item.stripe_payment_intent_id ? (
                          <span className="bg-gray-100 px-2 py-1 rounded">
                            {item.stripe_payment_intent_id.substring(0, 20)}...
                          </span>
                        ) : (
                          '−'
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                      決済履歴がありません
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* ページネーション */}
          {data?.items?.length ? (
            <div className="flex justify-between items-center mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrevPage}
                disabled={filters.skip === 0}
              >
                前のページ
              </Button>
              
              <span className="text-sm text-gray-600">
                ページ {data.page}
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleNextPage}
                disabled={!data.has_next}
              >
                次のページ
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
} 
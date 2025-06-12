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
  Shield,
  ChevronDown,
  ChevronUp,
  Calendar,
  DollarSign
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

  const [showFilters, setShowFilters] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

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

  // モバイル用決済履歴カードコンポーネント
  const PaymentCard = ({ item }: { item: PaymentHistoryItem }) => (
    <Card className="mb-4">
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <div className="text-sm text-gray-500 mb-1">
              {format(new Date(item.payment_date), 'yyyy/MM/dd HH:mm', { locale: ja })}
            </div>
            <div className="font-semibold text-lg flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              {item.currency.toUpperCase() === 'JPY' ? '¥' : item.currency}
              {item.amount.toLocaleString()}
            </div>
          </div>
          {getStatusBadge(item.status)}
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <CreditCard className="w-4 h-4 text-gray-500" />
            <span>{getPaymentMethodDisplay(item.payment_method)}</span>
          </div>
          
          {item.stripe_payment_intent_id && (
            <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded font-mono">
              ID: {item.stripe_payment_intent_id.substring(0, 30)}...
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

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
          {/* モバイル対応フィルタリングセクション */}
          <div className="mb-6">
            <Button
              variant="outline"
              className="w-full md:w-auto flex items-center gap-2 mb-4 md:hidden"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="w-4 h-4" />
              フィルター
              {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
            
            <div className={`space-y-4 ${isMobile && !showFilters ? 'hidden' : ''} md:block`}>
              {/* 基本フィルター */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
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
                  <div className="relative">
                    <Calendar className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      type="date"
                      value={filters.date_from}
                      onChange={(e) => handleFilterChange('date_from', e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium">終了日</label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      type="date"
                      value={filters.date_to}
                      onChange={(e) => handleFilterChange('date_to', e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 操作ボタン */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <Filter className="w-4 h-4" />
                更新
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportCSV}
                disabled={!data?.items?.length}
                className="flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                CSVエクスポート
              </Button>
            </div>
            
            <div className="text-sm text-gray-600">
              {data?.total ? `${data.total}件中 ${filters.skip + 1}-${Math.min(filters.skip + filters.limit, data.total)}件` : '0件'}
            </div>
          </div>

          {/* テーブル（デスクトップ用）またはカード（モバイル用） */}
          {isMobile ? (
            // モバイル用カードレイアウト
            <div>
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    読み込み中...
                  </div>
                </div>
              ) : data?.items?.length ? (
                data.items.map((item) => (
                  <PaymentCard key={item.id} item={item} />
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  決済履歴がありません
                </div>
              )}
            </div>
          ) : (
            // デスクトップ用テーブル
            <div className="border rounded-lg overflow-x-auto">
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
          )}

          {/* ページネーション */}
          {data?.items?.length ? (
            <div className="flex flex-col sm:flex-row justify-between items-center mt-4 gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrevPage}
                disabled={filters.skip === 0}
                className="w-full sm:w-auto"
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
                className="w-full sm:w-auto"
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
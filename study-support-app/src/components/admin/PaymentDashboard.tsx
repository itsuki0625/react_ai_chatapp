'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiClient } from '@/lib/api/client';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import {
  TrendingUp,
  TrendingDown,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Shield,
  DollarSign,
  Users,
  Activity,
  Refresh,
} from 'lucide-react';

interface PaymentStats {
  total_payments: number;
  successful_payments: number;
  failed_payments: number;
  pending_payments: number;
  total_amount: number;
  success_rate: number;
  requires_action_count: number;
}

interface RecentPayment {
  id: string;
  user_email: string;
  amount: number;
  currency: string;
  status: string;
  payment_method?: string;
  payment_date: string;
  stripe_payment_intent_id?: string;
  requires_3d_secure: boolean;
}

interface PaymentAlert {
  id: string;
  type: 'high_failure_rate' | 'multiple_3d_secure_failures' | 'unusual_activity';
  message: string;
  severity: 'low' | 'medium' | 'high';
  created_at: string;
}

const fetchPaymentStats = async (): Promise<PaymentStats> => {
  const response = await apiClient.get<PaymentStats>('/admin/payment-stats');
  return response.data;
};

const fetchRecentPayments = async (): Promise<RecentPayment[]> => {
  const response = await apiClient.get<RecentPayment[]>('/admin/recent-payments');
  return response.data;
};

const fetchPaymentAlerts = async (): Promise<PaymentAlert[]> => {
  const response = await apiClient.get<PaymentAlert[]>('/admin/payment-alerts');
  return response.data;
};

export function PaymentDashboard() {
  const [refreshKey, setRefreshKey] = useState(0);

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery({
    queryKey: ['payment-stats', refreshKey],
    queryFn: fetchPaymentStats,
    refetchInterval: 30000, // 30秒間隔で自動更新
  });

  const {
    data: recentPayments,
    isLoading: paymentsLoading,
    error: paymentsError,
  } = useQuery({
    queryKey: ['recent-payments', refreshKey],
    queryFn: fetchRecentPayments,
    refetchInterval: 30000,
  });

  const {
    data: alerts,
    isLoading: alertsLoading,
    error: alertsError,
  } = useQuery({
    queryKey: ['payment-alerts', refreshKey],
    queryFn: fetchPaymentAlerts,
    refetchInterval: 30000,
  });

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const getStatusBadge = (status: string, requires3ds: boolean = false) => {
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
            {requires3ds ? '3DS認証' : '認証要求'}
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

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-blue-500" />;
    }
  };

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(amount / 100); // Stripeは通常セント単位
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">決済監視ダッシュボード</h1>
          <p className="text-gray-600 mt-1">
            リアルタイムでの決済状況と3Dセキュア認証の監視
          </p>
        </div>
        <Button onClick={handleRefresh} variant="outline" size="sm">
          <Refresh className="w-4 h-4 mr-2" />
          更新
        </Button>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">総決済数</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsLoading ? '...' : stats?.total_payments || 0}
            </div>
            <p className="text-xs text-muted-foreground">過去24時間</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">成功率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsLoading ? '...' : `${stats?.success_rate?.toFixed(1) || 0}%`}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.successful_payments || 0} / {stats?.total_payments || 0} 件
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">3DS認証要求</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsLoading ? '...' : stats?.requires_action_count || 0}
            </div>
            <p className="text-xs text-muted-foreground">認証待ち</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">総決済金額</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsLoading ? '...' : formatAmount(stats?.total_amount || 0, 'JPY')}
            </div>
            <p className="text-xs text-muted-foreground">過去24時間</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="recent" className="space-y-4">
        <TabsList>
          <TabsTrigger value="recent">最近の決済</TabsTrigger>
          <TabsTrigger value="alerts">アラート</TabsTrigger>
          <TabsTrigger value="analytics">分析</TabsTrigger>
        </TabsList>

        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>最近の決済履歴</CardTitle>
              <CardDescription>
                過去1時間の決済取引（3Dセキュア認証の状況含む）
              </CardDescription>
            </CardHeader>
            <CardContent>
              {paymentsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : paymentsError ? (
                <div className="text-center py-8 text-red-600">
                  <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
                  <p>データの取得に失敗しました</p>
                </div>
              ) : (
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>時刻</TableHead>
                        <TableHead>ユーザー</TableHead>
                        <TableHead>金額</TableHead>
                        <TableHead>ステータス</TableHead>
                        <TableHead>決済方法</TableHead>
                        <TableHead>PaymentIntent ID</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {recentPayments?.length ? (
                        recentPayments.map((payment) => (
                          <TableRow key={payment.id}>
                            <TableCell>
                              {format(new Date(payment.payment_date), 'HH:mm:ss', { locale: ja })}
                            </TableCell>
                            <TableCell className="font-medium">
                              {payment.user_email}
                            </TableCell>
                            <TableCell>
                              {formatAmount(payment.amount, payment.currency)}
                            </TableCell>
                            <TableCell>
                              {getStatusBadge(payment.status, payment.requires_3d_secure)}
                            </TableCell>
                            <TableCell>
                              {payment.payment_method || '不明'}
                            </TableCell>
                            <TableCell className="font-mono text-xs">
                              {payment.stripe_payment_intent_id ? (
                                <span className="bg-gray-100 px-2 py-1 rounded">
                                  {payment.stripe_payment_intent_id.substring(0, 15)}...
                                </span>
                              ) : (
                                '−'
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                            最近の決済はありません
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>決済アラート</CardTitle>
              <CardDescription>
                異常検知と重要な通知
              </CardDescription>
            </CardHeader>
            <CardContent>
              {alertsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : alerts?.length ? (
                <div className="space-y-4">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className={`p-4 rounded-lg border-l-4 ${
                        alert.severity === 'high'
                          ? 'border-red-500 bg-red-50'
                          : alert.severity === 'medium'
                          ? 'border-yellow-500 bg-yellow-50'
                          : 'border-blue-500 bg-blue-50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {getAlertIcon(alert.severity)}
                        <div className="flex-1">
                          <p className="font-medium">{alert.message}</p>
                          <p className="text-sm text-gray-600 mt-1">
                            {format(new Date(alert.created_at), 'yyyy/MM/dd HH:mm', { locale: ja })}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2" />
                  <p>現在アラートはありません</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>決済ステータス分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      成功
                    </span>
                    <span className="font-mono">
                      {stats?.successful_payments || 0} 件
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-2">
                      <XCircle className="w-4 h-4 text-red-500" />
                      失敗
                    </span>
                    <span className="font-mono">
                      {stats?.failed_payments || 0} 件
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-blue-500" />
                      処理中
                    </span>
                    <span className="font-mono">
                      {stats?.pending_payments || 0} 件
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center gap-2">
                      <Shield className="w-4 h-4 text-orange-500" />
                      認証要求
                    </span>
                    <span className="font-mono">
                      {stats?.requires_action_count || 0} 件
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>3Dセキュア統計</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>3DS認証要求率</span>
                    <span className="font-mono">
                      {stats?.total_payments 
                        ? ((stats.requires_action_count / stats.total_payments) * 100).toFixed(1)
                        : '0.0'
                      }%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>認証待ち決済</span>
                    <span className="font-mono">
                      {stats?.requires_action_count || 0} 件
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
} 
"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminNotificationSettingsApi } from '@/lib/api-client';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { RefreshCw, Search } from 'lucide-react';
import { Badge } from '@/components/ui/badge'; // User情報を表示するためにインポート

// APIレスポンスの型をインポートまたはここで定義
// (api-client.ts で定義した型をエクスポートして使うのが望ましい)
interface User {
  id: string;
  email: string;
  full_name?: string | null;
}

interface NotificationSettingUser {
  id: string;
  user_id: string;
  notification_type: string;
  email_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  created_at: string;
  updated_at: string;
  user?: User;
}

interface NotificationSettingList {
  total: number;
  items: NotificationSettingUser[];
}

interface NotificationSettingUpdateData {
  email_enabled?: boolean;
  push_enabled?: boolean;
  in_app_enabled?: boolean;
  // quiet_hours_start と end も追加する場合はここに
}

const ITEMS_PER_PAGE = 10; // 1ページあたりのアイテム数

export const NotificationSettingsManagement = () => {
  const queryClient = useQueryClient();
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [userIdFilter, setUserIdFilter] = useState<string | undefined>(undefined); // UUID文字列として

  const {
    data: notificationSettingsData,
    isLoading,
    isError,
    error,
    refetch, // 手動で再取得するための関数
  } = useQuery<NotificationSettingList, Error>({
    queryKey: ['adminNotificationSettings', currentPage, userIdFilter],
    queryFn: () =>
      adminNotificationSettingsApi.getAllNotificationSettings({
        skip: (currentPage - 1) * ITEMS_PER_PAGE,
        limit: ITEMS_PER_PAGE,
        userId: userIdFilter, // APIがUUID文字列を期待する場合
      }).then(res => res.data),
    // keepPreviousData: true, // v5では placeholderData: previousData を使用するか、削除
  });

  const updateMutation = useMutation({
    mutationFn: ({ settingId, data }: { settingId: string; data: NotificationSettingUpdateData }) =>
      adminNotificationSettingsApi.updateNotificationSettingById(settingId, data),
    onSuccess: (data) => {
      toast.success(`設定 ID: ${data.data.id} が正常に更新されました。`);
      queryClient.invalidateQueries({ queryKey: ['adminNotificationSettings'] });
    },
    onError: (error: any, variables) => {
      toast.error(`設定 ID: ${variables.settingId} の更新に失敗しました: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleToggle = (setting: NotificationSettingUser, field: keyof NotificationSettingUpdateData) => {
    const currentValue = setting[field as keyof NotificationSettingUser]; // booleanであることを期待
    if (typeof currentValue !== 'boolean') return;

    updateMutation.mutate({
      settingId: setting.id,
      data: { [field]: !currentValue },
    });
  };
  
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleFilterApply = () => {
    // searchTerm をもとにユーザーIDを検索するロジックが別途必要
    // ここでは簡易的に searchTerm が UUID形式であればそれを userIdFilter に設定
    // 本来はメールアドレス等で検索し、対応するユーザーIDを取得するAPI呼び出しなどが必要
    if (searchTerm.match(/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/)) {
      setUserIdFilter(searchTerm);
    } else if (searchTerm === '') {
      setUserIdFilter(undefined);
    } else {
      toast.info("有効なユーザーID (UUID形式) を入力するか、空にしてください。");
      // ここでメールアドレスからユーザーIDを検索するAPIを呼び出す場合はその処理
    }
    setCurrentPage(1); // フィルター変更時は1ページ目に戻る
  };
  
  const totalPages = notificationSettingsData ? Math.ceil(notificationSettingsData.total / ITEMS_PER_PAGE) : 0;

  if (isLoading) return <div className="flex justify-center items-center p-8"><RefreshCw className="animate-spin mr-2" /> データを読み込んでいます...</div>;
  if (isError) return <div className="text-red-500 p-4">エラーが発生しました: {error?.message || '不明なエラー'}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-grow">
          <Input
            type="text"
            placeholder="ユーザーID (UUID) で検索..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="max-w-xs"
          />
          <Button onClick={handleFilterApply} variant="outline" size="sm">
            <Search className="mr-2 h-4 w-4" />
            検索
          </Button>
        </div>
        <Button onClick={() => refetch()} variant="outline" size="sm">
          <RefreshCw className="mr-2 h-4 w-4" />
          最新の情報に更新
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ユーザー</TableHead>
            <TableHead>通知タイプ</TableHead>
            <TableHead className="text-center">メール</TableHead>
            <TableHead className="text-center">プッシュ</TableHead>
            <TableHead className="text-center">アプリ内</TableHead>
            <TableHead>最終更新</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {notificationSettingsData && notificationSettingsData.items && notificationSettingsData.items.length > 0 ? (
            notificationSettingsData.items.map((setting: NotificationSettingUser) => (
              <TableRow key={setting.id}>
                <TableCell>
                  <div>{setting.user?.full_name || 'N/A'}</div>
                  <div className="text-xs text-muted-foreground">{setting.user?.email || setting.user_id}</div>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{setting.notification_type}</Badge>
                </TableCell>
                <TableCell className="text-center">
                  <Switch
                    checked={setting.email_enabled}
                    onCheckedChange={() => handleToggle(setting, 'email_enabled')}
                    disabled={updateMutation.isPending && updateMutation.variables?.settingId === setting.id}
                  />
                </TableCell>
                <TableCell className="text-center">
                  <Switch
                    checked={setting.push_enabled}
                    onCheckedChange={() => handleToggle(setting, 'push_enabled')}
                    disabled={updateMutation.isPending && updateMutation.variables?.settingId === setting.id}
                  />
                </TableCell>
                <TableCell className="text-center">
                  <Switch
                    checked={setting.in_app_enabled}
                    onCheckedChange={() => handleToggle(setting, 'in_app_enabled')}
                    disabled={updateMutation.isPending && updateMutation.variables?.settingId === setting.id}
                  />
                </TableCell>
                <TableCell>{new Date(setting.updated_at).toLocaleString('ja-JP')}</TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                表示する通知設定がありません。
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {totalPages > 1 && (
        <div className="flex items-center justify-end space-x-2 py-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            前へ
          </Button>
          <span className="text-sm">
            {currentPage} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
          >
            次へ
          </Button>
        </div>
      )}
    </div>
  );
}; 
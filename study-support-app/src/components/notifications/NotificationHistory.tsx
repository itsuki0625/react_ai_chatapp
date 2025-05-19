import React, { useEffect, useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format, isWithinInterval, subDays } from 'date-fns';
import { ja } from 'date-fns/locale';
import { Bell, Check, Trash2, Filter, CheckCircle, Trash, Search, ChevronDown, X, Archive, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
  metadata?: Record<string, any>;
}

type FilterType = 'all' | 'unread' | 'read';
type SortType = 'newest' | 'oldest' | 'type';
type DateRange = 'all' | 'today' | 'week' | 'month' | 'custom';

interface DateFilter {
  type: DateRange;
  startDate?: Date;
  endDate?: Date;
}

export const NotificationHistory = () => {
  const queryClient = useQueryClient();
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortType, setSortType] = useState<SortType>('newest');
  const [dateFilter, setDateFilter] = useState<DateFilter>({ type: 'all' });
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isBulkActionLoading, setIsBulkActionLoading] = useState(false);

  // 通知履歴の取得
  const { data: notifications, isLoading } = useQuery<Notification[]>({
    queryKey: ['notifications'],
    queryFn: async () => {
      const response = await apiClient.get('/notifications');
      return response.data;
    },
  });

  // 通知タイプの一覧を取得
  const notificationTypes = useMemo(() => {
    if (!notifications) return [];
    return Array.from(new Set(notifications.map(n => n.type)));
  }, [notifications]);

  // 通知を既読にする
  const markAsRead = useMutation({
    mutationFn: async (notificationIds: string[]) => {
      await apiClient.patch('/notifications/read', { ids: notificationIds });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setSelectedNotifications([]);
      toast.success('選択した通知を既読にしました');
    },
    onError: () => {
      toast.error('通知の既読化に失敗しました');
    },
  });

  // 通知を削除する
  const deleteNotification = useMutation({
    mutationFn: async (notificationIds: string[]) => {
      await apiClient.delete('/notifications', { data: { ids: notificationIds } });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setSelectedNotifications([]);
      setShowDeleteDialog(false);
      toast.success('選択した通知を削除しました');
    },
    onError: () => {
      toast.error('通知の削除に失敗しました');
    },
  });

  // 通知をアーカイブする
  const archiveNotification = useMutation({
    mutationFn: async (notificationIds: string[]) => {
      await apiClient.patch('/notifications/archive', { ids: notificationIds });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setSelectedNotifications([]);
      toast.success('選択した通知をアーカイブしました');
    },
    onError: () => {
      toast.error('通知のアーカイブに失敗しました');
    },
  });

  // 通知を更新する
  const refreshNotification = useMutation({
    mutationFn: async (notificationIds: string[]) => {
      await apiClient.post('/notifications/refresh', { ids: notificationIds });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setSelectedNotifications([]);
      toast.success('選択した通知を更新しました');
    },
    onError: () => {
      toast.error('通知の更新に失敗しました');
    },
  });

  // 一括操作の実行
  const handleBulkAction = async (action: 'read' | 'delete' | 'archive' | 'refresh') => {
    if (selectedNotifications.length === 0) return;

    setIsBulkActionLoading(true);
    try {
      switch (action) {
        case 'read':
          await markAsRead.mutateAsync(selectedNotifications);
          break;
        case 'delete':
          setShowDeleteDialog(true);
          break;
        case 'archive':
          await archiveNotification.mutateAsync(selectedNotifications);
          break;
        case 'refresh':
          await refreshNotification.mutateAsync(selectedNotifications);
          break;
      }
    } finally {
      setIsBulkActionLoading(false);
    }
  };

  // 日付フィルターの適用
  const applyDateFilter = (notification: Notification) => {
    const date = new Date(notification.created_at);
    const now = new Date();

    switch (dateFilter.type) {
      case 'today':
        return isWithinInterval(date, {
          start: new Date(now.setHours(0, 0, 0, 0)),
          end: new Date(now.setHours(23, 59, 59, 999)),
        });
      case 'week':
        return isWithinInterval(date, {
          start: subDays(now, 7),
          end: now,
        });
      case 'month':
        return isWithinInterval(date, {
          start: subDays(now, 30),
          end: now,
        });
      case 'custom':
        if (dateFilter.startDate && dateFilter.endDate) {
          return isWithinInterval(date, {
            start: dateFilter.startDate,
            end: dateFilter.endDate,
          });
        }
        return true;
      default:
        return true;
    }
  };

  // フィルタリングと検索を適用した通知を取得
  const filteredNotifications = useMemo(() => {
    if (!notifications) return [];

    return notifications
      .filter((notification) => {
        // フィルターの適用
        const matchesFilter =
          filterType === 'all' ||
          (filterType === 'unread' && !notification.is_read) ||
          (filterType === 'read' && notification.is_read);

        // 検索クエリの適用
        const searchLower = searchQuery.toLowerCase();
        const matchesSearch =
          !searchQuery ||
          notification.title.toLowerCase().includes(searchLower) ||
          notification.message.toLowerCase().includes(searchLower) ||
          notification.type.toLowerCase().includes(searchLower);

        // タイプフィルターの適用
        const matchesType =
          selectedTypes.length === 0 || selectedTypes.includes(notification.type);

        // 日付フィルターの適用
        const matchesDate = applyDateFilter(notification);

        return matchesFilter && matchesSearch && matchesType && matchesDate;
      })
      .sort((a, b) => {
        switch (sortType) {
          case 'newest':
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
          case 'oldest':
            return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          case 'type':
            return a.type.localeCompare(b.type);
          default:
            return 0;
        }
      });
  }, [notifications, filterType, searchQuery, sortType, dateFilter, selectedTypes]);

  // 通知の選択状態を切り替え
  const toggleNotification = (id: string) => {
    setSelectedNotifications((prev) =>
      prev.includes(id)
        ? prev.filter((notificationId) => notificationId !== id)
        : [...prev, id]
    );
  };

  // すべての通知を選択/解除
  const toggleAllNotifications = () => {
    setSelectedNotifications((prev) =>
      prev.length === filteredNotifications.length
        ? []
        : filteredNotifications.map((n) => n.id)
    );
  };

  // タイプフィルターの切り替え
  const toggleTypeFilter = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    );
  };

  // 日付フィルターのリセット
  const resetDateFilter = () => {
    setDateFilter({ type: 'all' });
  };

  if (isLoading) {
    return <div>読み込み中...</div>;
  }

  if (!notifications?.length) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground">
          通知はありません
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Select value={filterType} onValueChange={(value: FilterType) => setFilterType(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="フィルター" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">すべて</SelectItem>
                <SelectItem value="unread">未読</SelectItem>
                <SelectItem value="read">既読</SelectItem>
              </SelectContent>
            </Select>

            <Select value={sortType} onValueChange={(value: SortType) => setSortType(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="並び替え" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">新しい順</SelectItem>
                <SelectItem value="oldest">古い順</SelectItem>
                <SelectItem value="type">タイプ順</SelectItem>
              </SelectContent>
            </Select>

            <div className="relative w-[300px]">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="通知を検索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  日付フィルター
                  {dateFilter.type !== 'all' && (
                    <Badge variant="secondary" className="ml-2">
                      {dateFilter.type === 'custom'
                        ? 'カスタム'
                        : dateFilter.type === 'today'
                        ? '今日'
                        : dateFilter.type === 'week'
                        ? '1週間'
                        : '1ヶ月'}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="end">
                <div className="p-4 space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Button
                        variant={dateFilter.type === 'today' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setDateFilter({ type: 'today' })}
                      >
                        今日
                      </Button>
                      <Button
                        variant={dateFilter.type === 'week' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setDateFilter({ type: 'week' })}
                      >
                        1週間
                      </Button>
                      <Button
                        variant={dateFilter.type === 'month' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setDateFilter({ type: 'month' })}
                      >
                        1ヶ月
                      </Button>
                    </div>
                    <div className="pt-2">
                      <div className="text-sm font-medium mb-2">カスタム期間</div>
                      <div className="grid gap-2">
                        <Calendar
                          mode="range"
                          selected={{
                            from: dateFilter.startDate,
                            to: dateFilter.endDate,
                          }}
                          onSelect={(range) => {
                            if (range?.from) {
                              setDateFilter({
                                type: 'custom',
                                startDate: range.from,
                                endDate: range.to || range.from,
                              });
                            }
                          }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={resetDateFilter}
                    >
                      リセット
                    </Button>
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleAllNotifications}
                disabled={!filteredNotifications.length}
              >
                <Checkbox
                  checked={
                    filteredNotifications.length > 0 &&
                    selectedNotifications.length === filteredNotifications.length
                  }
                  className="mr-2"
                />
                すべて選択
              </Button>

              {selectedNotifications.length > 0 && (
                <div className="flex items-center space-x-2">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" size="sm" disabled={isBulkActionLoading}>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        一括操作
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={() => handleBulkAction('read')}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        既読にする
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleBulkAction('archive')}>
                        <Archive className="w-4 h-4 mr-2" />
                        アーカイブする
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleBulkAction('refresh')}>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        更新する
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => handleBulkAction('delete')}
                      >
                        <Trash className="w-4 h-4 mr-2" />
                        削除する
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>

                  <span className="text-sm text-muted-foreground">
                    {selectedNotifications.length}件選択中
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {notificationTypes.map((type) => (
            <Badge
              key={type}
              variant={selectedTypes.includes(type) ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => toggleTypeFilter(type)}
            >
              {type}
              {selectedTypes.includes(type) && (
                <X className="w-3 h-3 ml-1" />
              )}
            </Badge>
          ))}
        </div>
      </div>

      {filteredNotifications.length === 0 ? (
        <Card className="p-6">
          <div className="text-center text-muted-foreground">
            検索条件に一致する通知はありません
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredNotifications.map((notification) => (
            <Card key={notification.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <Checkbox
                    checked={selectedNotifications.includes(notification.id)}
                    onCheckedChange={() => toggleNotification(notification.id)}
                  />
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <Bell className="w-4 h-4 text-muted-foreground" />
                      <h3 className="font-medium">{notification.title}</h3>
                      {!notification.is_read && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-primary text-primary-foreground rounded-full">
                          未読
                        </span>
                      )}
                      <Badge variant="outline">{notification.type}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {notification.message}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {format(new Date(notification.created_at), 'yyyy年MM月dd日 HH:mm', {
                        locale: ja,
                      })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {!notification.is_read && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => markAsRead.mutate([notification.id])}
                    >
                      <Check className="w-4 h-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteNotification.mutate([notification.id])}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>通知の削除</AlertDialogTitle>
            <AlertDialogDescription>
              選択した{selectedNotifications.length}件の通知を削除します。
              この操作は取り消せません。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>キャンセル</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteNotification.mutate(selectedNotifications)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              削除する
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}; 
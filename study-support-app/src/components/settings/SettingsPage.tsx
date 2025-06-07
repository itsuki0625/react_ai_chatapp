"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Bell, User, Shield, CreditCard, ExternalLink, Settings } from 'lucide-react';
import LogoutButton from '@/components/common/LogoutButton';
import { toast } from 'react-hot-toast';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Badge } from "@/components/ui/badge";
import { UserSettings, User as UserType } from '@/types/user';
import { SubscriptionInfo } from '@/types/user';
import { Subscription } from '@/types/subscription';
import { useAuthHelpers } from "@/lib/authUtils";
import { Label } from "@/components/ui/label";
import { fetchUserSettings, updateUserSettings } from '@/services/userService';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { uploadUserIcon, deleteUserIcon } from '@/services/userService';
import { useUserStore } from '@/store/userStore';
import { useQuery } from '@tanstack/react-query';
import { subscriptionService } from '@/services/subscriptionService';
import { useRouter } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';
const ASSET_BASE_URL = process.env.NEXT_PUBLIC_ASSET_BASE_URL || '';

const SettingsPage = () => {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { user, setUser } = useUserStore();
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isIconLoading, setIsIconLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isPortalLoading, setIsPortalLoading] = useState(false);

  const { userRole, isLoading: isAuthLoading } = useAuthHelpers();

  const { data: currentSubscription, isLoading: isSubLoading, error: subError } = useQuery<Subscription | null>({
    queryKey: ['userSubscription'],
    queryFn: subscriptionService.getUserSubscription,
    enabled: status === 'authenticated',
    staleTime: 5 * 60 * 1000,
  });

  // Extract necessary values from session to stabilize dependencies
  const userId = session?.user?.id;
  const userName = session?.user?.name;
  const userEmail = session?.user?.email;

  const loadUserSettingsInternal = useCallback(async () => {
    // Loading states should be checked centrally
    const shouldShowLoading = status === 'loading' || (status === 'authenticated' && (isAuthLoading || isSubLoading));
    
    if (shouldShowLoading) {
      setIsLoading(true);
      return; // Exit early if we're still loading auth state
    }

    if (status === 'authenticated' && userId) {
      setIsLoading(true); 
      try {
        const settingsData = await fetchUserSettings();
        const mappedSettings: UserSettings = {
          full_name: String(settingsData.full_name || userName || ''),
          name: String(settingsData.name || settingsData.full_name || userName || ''),
          email: String(settingsData.email || userEmail || ''),
          profile_image_url: settingsData.profile_image_url ?? null,
          emailNotifications: settingsData.emailNotifications ?? true,
          browserNotifications: settingsData.browserNotifications ?? false,
          systemNotifications: settingsData.systemNotifications ?? true,
          chatNotifications: settingsData.chatNotifications ?? true,
          documentNotifications: settingsData.documentNotifications ?? true,
          theme: String(settingsData.theme || 'light'),
        };
        setUserSettings(mappedSettings);

        const userProfileImageKey = settingsData.profile_image_url ?? null;

        const currentUserInStore = useUserStore.getState().user;

        if (!currentUserInStore || currentUserInStore.id !== userId || currentUserInStore.profile_image_url !== userProfileImageKey) {
          console.log("Initializing/Updating Zustand user state based on fetched data or userID change...");
          const currentSessionUser = session?.user ?? {};
          const userDataForStore = {
            ...currentSessionUser,
            id: userId,
            name: settingsData.name || settingsData.full_name || userName,
            email: settingsData.email || userEmail,
            profile_image_url: userProfileImageKey,
            role: (currentSessionUser as any)?.role,
          };
          setUser(userDataForStore as any);
        }
        setPreviewUrl(userProfileImageKey);

      } catch (error) {
        console.error('ユーザー設定の取得エラー:', error);
        toast.error('ユーザー設定の取得に失敗しました。');
        setUserSettings({
          full_name: String(userName || 'ユーザー'),
          name: String(userName || 'ユーザー'),
          email: String(userEmail || ''),
          profile_image_url: null,
          emailNotifications: true,
          browserNotifications: false,
          systemNotifications: true,
          chatNotifications: true,
          documentNotifications: true,
          theme: 'light',
        });
        setPreviewUrl(null);
      } finally {
        setIsLoading(false);
      }
    } else if (status === 'unauthenticated') {
      setUserSettings(null);
      setPreviewUrl(null);
      setUser(null);
      setIsLoading(false);
    }
  }, [status, userId, userName, userEmail, isAuthLoading, isSubLoading, session?.user]);

  useEffect(() => {
    loadUserSettingsInternal();
  }, [loadUserSettingsInternal]);

  useEffect(() => {
    if (selectedFile) {
        const reader = new FileReader();
        reader.onloadend = () => {
            setPreviewUrl(reader.result as string);
        };
        reader.readAsDataURL(selectedFile);
    } else {
        setPreviewUrl(user?.profile_image_url ?? null);
    }
  }, [selectedFile, user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;

    setUserSettings(prev => {
      if (prev === null) return null;
      return { ...prev, [name]: type === 'checkbox' ? checked : value };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userSettings) {
      toast.error('ユーザー設定が読み込まれていません。');
      return;
    }
    if (status !== 'authenticated') {
      toast.error('認証されていません。設定は更新されません。');
      return;
    }
    try {
      setSaving(true);
      const requestData = {
        name: userSettings.name,
        emailNotifications: userSettings.emailNotifications,
        browserNotifications: userSettings.browserNotifications,
        systemNotifications: userSettings.systemNotifications,
        chatNotifications: userSettings.chatNotifications,
        documentNotifications: userSettings.documentNotifications,
        theme: userSettings.theme,
      };
      console.log('設定更新データ:', requestData);
      const updatedSettings = await updateUserSettings(requestData as Partial<UserSettings>);

      const currentUserFromStore = useUserStore.getState().user;
      if (currentUserFromStore) {
        const userToUpdate: UserType = { 
          ...currentUserFromStore, 
          name: updatedSettings.name || updatedSettings.full_name || currentUserFromStore.name,
          profile_image_url: updatedSettings.profile_image_url !== undefined
            ? updatedSettings.profile_image_url
            : currentUserFromStore.profile_image_url,
        };
        setUser(userToUpdate);
      }

      setUserSettings({
          full_name: updatedSettings.full_name || userSettings?.full_name || '',
          name: updatedSettings.name || userSettings?.name || '',
          email: userSettings?.email || '', 
          profile_image_url: updatedSettings.profile_image_url !== undefined ? updatedSettings.profile_image_url : userSettings?.profile_image_url,
          emailNotifications: updatedSettings.emailNotifications,
          browserNotifications: updatedSettings.browserNotifications,
          systemNotifications: updatedSettings.systemNotifications,
          chatNotifications: updatedSettings.chatNotifications,
          documentNotifications: updatedSettings.documentNotifications,
          theme: updatedSettings.theme,
      });

      toast.success('設定を更新しました。');
    } catch (error) {
      console.error('設定更新エラー:', error);
      toast.error(`設定の更新に失敗しました: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
        const allowedTypes = ['image/png', 'image/jpeg', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            toast.error('許可されていないファイル形式です。(PNG, JPG, GIFのみ)');
            if (fileInputRef.current) fileInputRef.current.value = "";
            setSelectedFile(null);
            return;
        }
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            toast.error('ファイルサイズが大きすぎます。(5MBまで)');
            if (fileInputRef.current) fileInputRef.current.value = "";
            setSelectedFile(null);
            return;
        }
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  };

  const handleUploadIcon = async () => {
    if (!selectedFile) return;
    setIsIconLoading(true);
    try {
      const updatedUser = await uploadUserIcon(selectedFile);
      setUser(updatedUser);
      toast.success('アイコンを更新しました。');
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (error) {
      console.error('Icon upload failed:', error);
      toast.error(error instanceof Error ? error.message : 'アイコンのアップロードに失敗しました。');
    } finally {
      setIsIconLoading(false);
    }
  };

  const handleDeleteIcon = async () => {
    if (!user?.profile_image_url && !session?.user?.profile_image_url) return;
    setIsIconLoading(true);
    try {
      const updatedUser = await deleteUserIcon();
      setUser(updatedUser);
      toast.success('アイコンを削除しました。');
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setPreviewUrl(null);
    } catch (error) {
      console.error('Icon delete failed:', error);
      toast.error(error instanceof Error ? error.message : 'アイコンの削除に失敗しました。');
    } finally {
      setIsIconLoading(false);
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleManageSubscription = async () => {
    setIsPortalLoading(true);
    try {
      const returnUrl = window.location.href;
      const { url } = await subscriptionService.createPortalSession(returnUrl);
      window.location.href = url;
    } catch (error) {
      console.error('ポータルセッション作成エラー:', error);
      toast.error(error instanceof Error ? error.message : 'サブスクリプション管理画面への遷移に失敗しました。');
    } finally {
      setIsPortalLoading(false);
    }
  };

  const handleChangePlanClick = () => {
    toast.success('プラン変更機能は現在実装中です。');
  };

  const navigateToPasswordChange = () => {
    router.push('/settings/password');
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto text-center">
        <p>読み込み中...</p>
      </div>
    );
  }

  const displayName = userSettings?.name ?? user?.name ?? session?.user?.name ?? 'ユーザー';
  const fallbackChar = displayName?.charAt(0)?.toUpperCase() ?? 'U';

  const profileImageUrlKey = previewUrl;
  const currentIconUrl = profileImageUrlKey && !profileImageUrlKey.startsWith('data:')
    ? `${ASSET_BASE_URL}/${profileImageUrlKey}`
    : profileImageUrlKey;

  const hasExistingIcon = !!(user?.profile_image_url ?? session?.user?.profile_image_url);

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleDateString('ja-JP');
    } catch {
      return '無効な日付';
    }
  };

  const getPlanStatusBadge = (status: string | undefined) => {
    if (!status) return <Badge variant="secondary">不明</Badge>;
    switch (status) {
      case 'active':
      case 'trialing':
        return <Badge variant="secondary">有効</Badge>;
      case 'past_due':
      case 'unpaid':
        return <Badge variant="destructive">支払い要</Badge>;
      case 'canceled':
        return <Badge variant="outline">キャンセル済み</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">アカウント設定</h1>
        <div className="flex items-center gap-2">
          <LogoutButton />
        </div>
      </div>

      {status === 'authenticated' ? (
        <Tabs defaultValue="profile" className="w-full">
          <TabsList className="grid grid-cols-4 mb-6">
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              プロフィール
            </TabsTrigger>
            <TabsTrigger value="subscription" className="flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              契約プラン
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              通知設定
            </TabsTrigger>
            <TabsTrigger value="security" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              セキュリティ
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>プロフィール設定</CardTitle>
                <CardDescription>
                  あなたの個人情報と表示設定を管理します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <form onSubmit={handleSubmit}>
                  <div className="space-y-6">
                    <div>
                      <Label className="block text-sm font-medium text-gray-700 mb-2">プロフィール画像</Label>
                      <div className="flex items-center space-x-4">
                        <Avatar className="h-20 w-20 cursor-pointer" onClick={handleAvatarClick}>
                          <AvatarImage src={currentIconUrl ?? undefined} alt={displayName} />
                          <AvatarFallback>{fallbackChar}</AvatarFallback>
                        </Avatar>
                        <Input
                          type="file"
                          accept="image/png, image/jpeg, image/gif"
                          ref={fileInputRef}
                          onChange={handleFileChange}
                          className="hidden"
                        />
                        <div className="flex flex-col space-y-2">
                          <Button type="button" onClick={handleAvatarClick} variant="outline" size="sm" disabled={isIconLoading}>
                            画像を選択
                          </Button>
                          {selectedFile && (
                            <Button type="button" onClick={handleUploadIcon} size="sm" disabled={isIconLoading}>
                              {isIconLoading ? 'アップロード中...' : 'アイコンを更新'}
                            </Button>
                          )}
                          {hasExistingIcon && !selectedFile && (
                            <Button type="button" onClick={handleDeleteIcon} variant="destructive" size="sm" disabled={isIconLoading}>
                              {isIconLoading ? '削除中...' : 'アイコンを削除'}
                            </Button>
                          )}
                        </div>
                      </div>
                      {selectedFile && (
                        <p className="text-sm text-muted-foreground mt-2">
                          選択中のファイル: {selectedFile.name}
                        </p>
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="name">名前</Label>
                        <Input
                          type="text"
                          name="name"
                          id="name"
                          value={userSettings?.name || ''}
                          onChange={handleChange}
                          className="mt-1"
                          disabled={saving}
                        />
                      </div>
                      <div>
                        <Label htmlFor="email">メールアドレス</Label>
                        <Input
                          type="email"
                          name="email"
                          id="email"
                          value={userSettings?.email || ''}
                          disabled
                          className="mt-1 bg-gray-100"
                        />
                        <p className="mt-1 text-xs text-gray-500">メールアドレスの変更はサポートにお問い合わせください</p>
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="theme">テーマ</Label>
                      <select
                        id="theme"
                        name="theme"
                        value={userSettings?.theme || 'light'}
                        onChange={handleChange}
                        className="w-full p-2 border rounded-md mt-1"
                      >
                        <option value="light">ライト</option>
                        <option value="dark">ダーク</option>
                      </select>
                    </div>
                  </div>
                  <div className="mt-6">
                    <Button type="submit" disabled={saving || isLoading}>
                      {saving ? '保存中...' : '設定を保存'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="subscription">
            <Card>
              <CardHeader>
                <CardTitle>契約プラン</CardTitle>
                <CardDescription>
                  現在のサブスクリプション情報と支払い状況を確認できます
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isSubLoading ? (
                  <p>契約情報を読み込み中...</p>
                ) : subError ? (
                  <p className="text-red-500">契約情報の取得に失敗しました。</p>
                ) : currentSubscription ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">現在のプラン</h3>
                        <p className="mt-1 font-semibold">{currentSubscription.plan_name || '不明なプラン'}</p>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">ステータス</h3>
                        <div className="mt-1">{getPlanStatusBadge(currentSubscription.status)}</div>
                      </div>
                    </div>
                    
                    {currentSubscription.current_period_end && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">次回更新日</h3>
                        <p className="mt-1">{formatDate(currentSubscription.current_period_end)}</p>
                      </div>
                    )}
                    
                    {currentSubscription.cancel_at && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">キャンセル予定日</h3>
                        <p className="mt-1 text-yellow-600">{formatDate(currentSubscription.cancel_at)}</p>
                      </div>
                    )}
                    
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleManageSubscription}
                      disabled={isPortalLoading}
                      className="mt-4 w-full sm:w-auto"
                    >
                      {isPortalLoading ? '読み込み中...' : 'サブスクリプション管理'}
                      <ExternalLink className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <p>現在アクティブなプランはありません。</p>
                    <Button
                      type="button"
                      variant="default"
                      onClick={() => window.location.href = '/subscription/plans'}
                      className="w-full sm:w-auto"
                    >
                      プランを選択する
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle>通知設定</CardTitle>
                <CardDescription>
                  あなたの通知設定を管理します
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium mb-3">通知の種類</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="systemNotifications" className="font-medium">システム通知</Label>
                          <p className="text-sm text-gray-500">システムからの重要なお知らせを受け取ります</p>
                        </div>
                        <div className="h-6 w-12">
                          <input
                            type="checkbox"
                            id="systemNotifications"
                            name="systemNotifications"
                            checked={userSettings?.systemNotifications ?? true}
                            onChange={handleChange}
                            className="sr-only peer"
                            disabled={saving}
                          />
                          <label
                            htmlFor="systemNotifications"
                            className="relative flex items-center h-6 w-12 cursor-pointer rounded-full bg-gray-200 peer-checked:bg-blue-600 peer-disabled:opacity-50 transition-colors"
                          >
                            <span className="absolute left-1 top-1 h-4 w-4 rounded-full bg-white peer-checked:left-7 transition-all"></span>
                          </label>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="chatNotifications" className="font-medium">チャットメッセージ</Label>
                          <p className="text-sm text-gray-500">新しいメッセージが届いたときに通知を受け取ります</p>
                        </div>
                        <div className="h-6 w-12">
                          <input
                            type="checkbox"
                            id="chatNotifications"
                            name="chatNotifications"
                            checked={userSettings?.chatNotifications ?? true}
                            onChange={handleChange}
                            className="sr-only peer"
                            disabled={saving}
                          />
                          <label
                            htmlFor="chatNotifications"
                            className="relative flex items-center h-6 w-12 cursor-pointer rounded-full bg-gray-200 peer-checked:bg-blue-600 peer-disabled:opacity-50 transition-colors"
                          >
                            <span className="absolute left-1 top-1 h-4 w-4 rounded-full bg-white peer-checked:left-7 transition-all"></span>
                          </label>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="documentNotifications" className="font-medium">ドキュメント期限</Label>
                          <p className="text-sm text-gray-500">ドキュメントの期限が近づいたときに通知を受け取ります</p>
                        </div>
                        <div className="h-6 w-12">
                          <input
                            type="checkbox"
                            id="documentNotifications"
                            name="documentNotifications"
                            checked={userSettings?.documentNotifications ?? true}
                            onChange={handleChange}
                            className="sr-only peer"
                            disabled={saving}
                          />
                          <label
                            htmlFor="documentNotifications"
                            className="relative flex items-center h-6 w-12 cursor-pointer rounded-full bg-gray-200 peer-checked:bg-blue-600 peer-disabled:opacity-50 transition-colors"
                          >
                            <span className="absolute left-1 top-1 h-4 w-4 rounded-full bg-white peer-checked:left-7 transition-all"></span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <h3 className="text-sm font-medium mb-3">通知方法</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="emailNotifications" className="font-medium">メール通知</Label>
                          <p className="text-sm text-gray-500">通知をメールで受け取ります</p>
                        </div>
                        <div className="h-6 w-12">
                          <input
                            type="checkbox"
                            id="emailNotifications"
                            name="emailNotifications"
                            checked={userSettings?.emailNotifications ?? true}
                            onChange={handleChange}
                            className="sr-only peer"
                            disabled={saving}
                          />
                          <label
                            htmlFor="emailNotifications"
                            className="relative flex items-center h-6 w-12 cursor-pointer rounded-full bg-gray-200 peer-checked:bg-blue-600 peer-disabled:opacity-50 transition-colors"
                          >
                            <span className="absolute left-1 top-1 h-4 w-4 rounded-full bg-white peer-checked:left-7 transition-all"></span>
                          </label>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="browserNotifications" className="font-medium">ブラウザ通知</Label>
                          <p className="text-sm text-gray-500">ブラウザのプッシュ通知を受け取ります</p>
                        </div>
                        <div className="h-6 w-12">
                          <input
                            type="checkbox"
                            id="browserNotifications"
                            name="browserNotifications"
                            checked={userSettings?.browserNotifications ?? false}
                            onChange={handleChange}
                            className="sr-only peer"
                            disabled={saving}
                          />
                          <label
                            htmlFor="browserNotifications"
                            className="relative flex items-center h-6 w-12 cursor-pointer rounded-full bg-gray-200 peer-checked:bg-blue-600 peer-disabled:opacity-50 transition-colors"
                          >
                            <span className="absolute left-1 top-1 h-4 w-4 rounded-full bg-white peer-checked:left-7 transition-all"></span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4">
                    <Button type="submit" disabled={saving}>
                      {saving ? '保存中...' : '設定を保存'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card>
              <CardHeader>
                <CardTitle>セキュリティ設定</CardTitle>
                <CardDescription>
                  アカウントのセキュリティ設定を管理します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">パスワード管理</h3>
                  <p className="text-sm text-muted-foreground">
                    定期的なパスワード変更はアカウントの安全性を高めます
                  </p>
                </div>
                <Button onClick={navigateToPasswordChange}>パスワードを変更する</Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      ) : (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p>設定を表示・編集するにはログインしてください。</p>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
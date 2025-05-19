"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Bell, User, Shield, CreditCard, ExternalLink } from 'lucide-react';
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
import { uploadUserIcon, deleteUserIcon } from '@/services/userService';
import { useUserStore } from '@/store/userStore';
import { useQuery } from '@tanstack/react-query';
import { subscriptionService } from '@/services/subscriptionService';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';
const ASSET_BASE_URL = process.env.NEXT_PUBLIC_ASSET_BASE_URL || '';

const SettingsPage = () => {
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { user, setUser } = useUserStore();
  const [userSettings, setUserSettings] = useState<Omit<UserSettings, 'subscription'> | null>(null);

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
  // Add any other session properties used in the effect if necessary

  useEffect(() => {
    const loadUserSettingsInternal = async () => {
      if (status === 'loading' || (status === 'authenticated' && (isAuthLoading || isSubLoading))) {
        setIsLoading(true);
      }

      if (status === 'authenticated' && userId) {
        setIsLoading(true); // Ensure loading is true for this fetch operation
        try {
          const settingsData = await fetchUserSettings();
          const mappedSettings: Omit<UserSettings, 'subscription'> = {
            full_name: String(settingsData.full_name || userName || ''),
            name: String(settingsData.name || settingsData.full_name || userName || ''),
            email: String(settingsData.email || userEmail || ''),
            profile_image_url: settingsData.profile_image_url ?? null,
            emailNotifications: settingsData.emailNotifications ?? true,
            browserNotifications: settingsData.browserNotifications ?? false,
            theme: String(settingsData.theme || 'light'),
          };
          setUserSettings(mappedSettings);

          const userProfileImageKey = settingsData.profile_image_url ?? null;

          const currentUserInStore = useUserStore.getState().user;

          if (!currentUserInStore || currentUserInStore.id !== userId || currentUserInStore.profile_image_url !== userProfileImageKey /* Add more critical field comparisons if needed */) {
            console.log("Initializing/Updating Zustand user state based on fetched data or userID change...");
            const currentSessionUser = session?.user ?? {};
            const userDataForStore = {
              ...currentSessionUser, // Base with session user data
              id: userId, // Ensure correct ID from session
              name: settingsData.name || settingsData.full_name || userName, // Prioritize fetched/settings data
              email: settingsData.email || userEmail, // Prioritize fetched/settings data
              profile_image_url: userProfileImageKey, // Fetched data
              // Preserve other fields from session.user like role, if not in settingsData
              role: (currentSessionUser as any)?.role,
            };
            setUser(userDataForStore as any); // Update Zustand store
          }
          setPreviewUrl(userProfileImageKey);

        } catch (error) {
          console.error('ユーザー設定の取得エラー:', error);
          toast.error('ユーザー設定の取得に失敗しました。');
          // Fallback settings on error
          setUserSettings({
            full_name: String(userName || 'ユーザー'),
            name: String(userName || 'ユーザー'),
            email: String(userEmail || ''),
            profile_image_url: null,
            emailNotifications: true,
            browserNotifications: false,
            theme: 'light',
          });
          setPreviewUrl(null);
        } finally {
          // After this fetch, re-evaluate loading based on other ongoing loading states
          if (status === 'authenticated') {
            setIsLoading(isAuthLoading || isSubLoading);
          } else {
            setIsLoading(false); // If no longer authenticated, not loading
          }
        }
      } else if (status === 'unauthenticated') {
        setUserSettings(null);
        setPreviewUrl(null);
        setUser(null);
        setIsLoading(false);
      } else if (status === 'loading') {
        // If only session status is loading and other blocks didn't handle
        setIsLoading(true);
      }
    };

    loadUserSettingsInternal();
  // Removed 'user' from dependencies.
  // setUserSettings is included because loadUserSettingsInternal calls it.
  // session is kept as per original; if issues persist, its direct usage or frequent reference changes could be reviewed.
  }, [status, userId, userName, userEmail, setUser, setUserSettings, isAuthLoading, isSubLoading]);

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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
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

  console.log("--- Icon URL Debug ---");
  console.log("ASSET_BASE_URL:", ASSET_BASE_URL);
  console.log("profileImageUrlKey (from previewUrl):", profileImageUrlKey);
  console.log("Final currentIconUrl passed to AvatarImage:", currentIconUrl);

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
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">設定</h1>
      {status === 'authenticated' ? (
        <form onSubmit={handleSubmit}>
          <section className="bg-white rounded-lg shadow mb-6">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center">
              <User className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">プロフィール設定</h2>
            </div>
            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">プロフィール画像</label>
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
          </section>

          <section className="bg-white rounded-lg shadow mb-6">
             <div className="px-6 py-4 border-b border-gray-200 flex items-center">
              <CreditCard className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">契約プラン</h2>
            </div>
            <div className="p-6 space-y-4">
              {isSubLoading ? (
                <p>契約情報を読み込み中...</p>
              ) : subError ? (
                <p className="text-red-500">契約情報の取得に失敗しました。</p>
              ) : currentSubscription ? (
                <div>
                  <p className="mb-2">
                    <span className="font-semibold">現在のプラン:</span> {currentSubscription.plan_name || '不明なプラン'}
                  </p>
                  <p className="mb-2">
                    <span className="font-semibold">ステータス:</span> {getPlanStatusBadge(currentSubscription.status)}
                  </p>
                  {currentSubscription.current_period_end && (
                    <p className="mb-2">
                      <span className="font-semibold">次回更新日:</span> {formatDate(currentSubscription.current_period_end)}
                    </p>
                  )}
                  {currentSubscription.cancel_at && (
                     <p className="mb-4 text-yellow-600">
                       <span className="font-semibold">キャンセル予定日:</span> {formatDate(currentSubscription.cancel_at)}
                     </p>
                   )}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleManageSubscription}
                    disabled={isPortalLoading}
                    className="mt-4"
                  >
                    {isPortalLoading ? '読み込み中...' : 'サブスクリプション管理'}
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div>
                  <p>現在アクティブなプランはありません。</p>
                  <Button
                    type="button"
                    variant="default"
                    onClick={() => window.location.href = '/subscription/plans'}
                    className="mt-4"
                  >
                    プランを選択する
                  </Button>
                </div>
              )}
            </div>
          </section>

          <section className="bg-white rounded-lg shadow mb-6">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center">
                <Bell className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">通知設定</h2>
            </div>
            <div className="p-6 space-y-6">
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-900">通知の種類</h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <Label htmlFor="systemNotifications">システム通知</Label>
                            <Input
                                type="checkbox"
                                name="systemNotifications"
                                id="systemNotifications"
                                checked={userSettings?.systemNotifications ?? true}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                disabled={saving}
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <Label htmlFor="chatNotifications">チャットメッセージ</Label>
                            <Input
                                type="checkbox"
                                name="chatNotifications"
                                id="chatNotifications"
                                checked={userSettings?.chatNotifications ?? true}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                disabled={saving}
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <Label htmlFor="documentNotifications">ドキュメント期限</Label>
                            <Input
                                type="checkbox"
                                name="documentNotifications"
                                id="documentNotifications"
                                checked={userSettings?.documentNotifications ?? true}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                disabled={saving}
                            />
                        </div>
                    </div>
                </div>

                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-900">通知方法</h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <Label htmlFor="emailNotifications">メール通知</Label>
                            <Input
                                type="checkbox"
                                name="emailNotifications"
                                id="emailNotifications"
                                checked={userSettings?.emailNotifications ?? true}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                disabled={saving}
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <Label htmlFor="browserNotifications">ブラウザ通知</Label>
                            <Input
                                type="checkbox"
                                name="browserNotifications"
                                id="browserNotifications"
                                checked={userSettings?.browserNotifications ?? false}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                disabled={saving}
                            />
                        </div>
                    </div>
                </div>

                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-900">静かな時間帯</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label htmlFor="quietHoursStart">開始時間</Label>
                            <Input
                                type="time"
                                name="quietHoursStart"
                                id="quietHoursStart"
                                value={userSettings?.quietHoursStart || ''}
                                onChange={handleChange}
                                className="mt-1"
                                disabled={saving}
                            />
                        </div>
                        <div>
                            <Label htmlFor="quietHoursEnd">終了時間</Label>
                            <Input
                                type="time"
                                name="quietHoursEnd"
                                id="quietHoursEnd"
                                value={userSettings?.quietHoursEnd || ''}
                                onChange={handleChange}
                                className="mt-1"
                                disabled={saving}
                            />
                        </div>
                    </div>
                </div>
            </div>
          </section>

           <section className="bg-white rounded-lg shadow mb-6">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center">
                    <Shield className="h-5 w-5 text-gray-400 mr-2" />
                    <h2 className="text-lg font-medium text-gray-900">セキュリティ設定</h2>
                </div>
                <div className="p-6">
                    <Button type="button" variant="outline">パスワードを変更する</Button>
                </div>
           </section>

          <div className="mt-6 flex justify-end">
            <Button type="submit" disabled={saving}>
              {saving ? '保存中...' : '設定を保存'}
            </Button>
          </div>
        </form>
      ) : (
        <p>設定を表示・編集するにはログインしてください。</p>
      )}
      <div className="mt-8 border-t pt-6">
        <LogoutButton />
      </div>
    </div>
  );
};

export default SettingsPage;
"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Bell, User, Shield, CreditCard } from 'lucide-react';
import LogoutButton from '@/components/common/LogoutButton';
import { toast } from 'react-hot-toast';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Badge } from "@/components/ui/badge";
import { UserSettings } from '@/types/user';
import { useAuthHelpers } from "@/lib/authUtils";
import { Label } from "@/components/ui/label";
import { fetchUserSettings } from '@/services/userService';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { uploadUserIcon, deleteUserIcon } from '@/services/userService';
import { useUserStore } from '@/store/userStore';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';
const ASSET_BASE_URL = process.env.NEXT_PUBLIC_ASSET_BASE_URL || '';

const SettingsPage = () => {
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { user, setUser } = useUserStore();
  const [userSettings, setUserSettings] = useState<Omit<UserSettings, 'subscription'> & { subscription?: UserSettings['subscription'] } | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isIconLoading, setIsIconLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { userRole, isLoading: isAuthLoading } = useAuthHelpers();

  useEffect(() => {
    const loadInitialData = async () => {
      if (status === 'authenticated' && session?.user?.id) {
        setIsLoading(true);
        try {
          const settingsData = await fetchUserSettings();
          const mappedSettings: UserSettings = {
            full_name: String(settingsData.full_name || session.user.name || ''),
            name: String(settingsData.name || settingsData.full_name || session.user.name || ''),
            email: String(settingsData.email || session.user.email || ''),
            emailNotifications: settingsData.emailNotifications ?? true,
            browserNotifications: settingsData.browserNotifications ?? false,
            theme: String(settingsData.theme || 'light'),
            subscription: settingsData.subscription || null,
          };
          setUserSettings(mappedSettings);

          const profileImageUrlFromSession = (session.user as any).profile_image_url ?? null;
          
          if (!user) {
            console.log("Initializing Zustand user state from session...");
            setUser(session.user as any);
            setPreviewUrl(profileImageUrlFromSession);
          } else {
            setPreviewUrl(user.profile_image_url ?? profileImageUrlFromSession);
          }

        } catch (error) {
          console.error('ユーザー設定の取得エラー:', error);
          toast.error('ユーザー設定の取得に失敗しました。');
          setUserSettings({
            full_name: 'デモユーザー',
            name: 'デモユーザー',
            email: 'demo@example.com',
            emailNotifications: true,
            browserNotifications: false,
            theme: 'light',
            subscription: null,
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
    };
    loadInitialData();
  }, [status, session?.user?.id, setUser]);

  useEffect(() => {
    const profileImageUrlFromSession = (session?.user as any)?.profile_image_url ?? null;
    if (selectedFile) {
        const reader = new FileReader();
        reader.onloadend = () => {
            setPreviewUrl(reader.result as string);
        };
        reader.readAsDataURL(selectedFile);
    } else {
        setPreviewUrl(user?.profile_image_url ?? profileImageUrlFromSession);
    }
  }, [selectedFile, user?.profile_image_url]);

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
        full_name: userSettings.name,
        email_notifications: userSettings.emailNotifications,
        browser_notifications: userSettings.browserNotifications,
        theme: userSettings.theme
      };
      console.log('設定更新データ:', requestData);
      toast.success('設定を更新しました（API仮）');
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

  const handleChangePlanClick = () => {
    alert('プラン変更機能は現在実装中です。');
  };

  if (isLoading || isAuthLoading) {
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

  // ★★★ デバッグログを追加 ★★★
  console.log("--- Icon URL Debug ---");
  console.log("ASSET_BASE_URL:", ASSET_BASE_URL);
  console.log("profileImageUrlKey (from previewUrl):", profileImageUrlKey);
  console.log("Final currentIconUrl passed to AvatarImage:", currentIconUrl);
  // ★★★ デバッグログここまで ★★★

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
                {session?.user?.role ? (
                    <div>
                        <p>現在のプラン: <Badge variant="secondary">{session.user.role}</Badge></p>
                    </div>
                ) : (
                    <p>現在アクティブなプランはありません。</p>
                )}
            </div>
          </section>

          <section className="bg-white rounded-lg shadow mb-6">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center">
                <Bell className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">通知設定</h2>
            </div>
            <div className="p-6 space-y-4">
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
"use client";

import React, { useState, useEffect } from 'react';
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';

const SettingsPage = () => {
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);

  // Get user role using the hook
  const { userRole, isLoading: isAuthLoading } = useAuthHelpers();

  const loadUserSettingsData = async () => {
    setIsLoading(true);
    try {
      const settingsData: UserSettings = await fetchUserSettings();
      console.log('取得した設定データ:', settingsData);

      if (!settingsData) {
          console.error('fetchUserSettingsService returned null or undefined');
          throw new Error("User settings data could not be fetched.");
      }

      const mappedSettings: UserSettings = {
        full_name: String(settingsData.full_name || session?.user?.name || ''),
        name: String(settingsData.name || settingsData.full_name || session?.user?.name || ''),
        email: String(settingsData.email || session?.user?.email || ''),
        emailNotifications: settingsData.emailNotifications ?? true,
        browserNotifications: settingsData.browserNotifications ?? false,
        theme: String(settingsData.theme || 'light'),
        subscription: settingsData.subscription || null,
      };

      setUserSettings(mappedSettings);

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
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (status === 'authenticated') {
      loadUserSettingsData();
    } else if (status === 'unauthenticated') {
      setUserSettings({
        full_name: 'デモユーザー',
        name: 'デモユーザー',
        email: 'demo@example.com',
        emailNotifications: true,
        browserNotifications: false,
        theme: 'light',
        subscription: null,
      });
      setIsLoading(false);
    } else {
      setIsLoading(true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setUserSettings(prev => {
      if (prev === null) return null;

      return {
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      };
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
      toast.success('設定を更新しました（API未実装）');
    } catch (error) {
      console.error('設定更新エラー:', error);
      toast.error(`設定の更新に失敗しました: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  // Placeholder function for the change plan button
  const handleChangePlanClick = () => {
    // TODO: Implement navigation or modal logic for changing the plan
    alert('プラン変更機能は現在実装中です。');
  };

  if (isLoading || isAuthLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-center">
          <p>読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">設定</h1>
      <form onSubmit={handleSubmit}>
        <section className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <User className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">プロフィール設定</h2>
            </div>
          </div>
          <div className="p-6 space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">プロフィール画像</label>
              <div className="mt-2 flex items-center space-x-4">
                <div className="h-20 w-20 rounded-full bg-gray-200 flex items-center justify-center">
                  <User className="h-10 w-10 text-gray-400" />
                </div>
                <button 
                  type="button"
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  画像を変更
                </button>
              </div>
            </div>
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">名前</label>
              <input
                type="text"
                name="name"
                id="name"
                value={userSettings?.name || ''}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">メールアドレス</label>
              <input
                type="email"
                name="email"
                id="email"
                value={userSettings?.email || ''}
                disabled
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-gray-100 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">メールアドレスの変更はサポートにお問い合わせください</p>
            </div>
          </div>
        </section>

        <section className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <CreditCard className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">契約プラン</h2>
            </div>
          </div>
          <div className="p-6">
             <div className="space-y-2">
               <Label htmlFor="currentPlan">現在のプラン</Label>
               <div className="flex items-center space-x-4">
                 {userRole ? (
                   <Badge variant="secondary" id="currentPlan" className="text-base px-3 py-1">{userRole}</Badge>
                 ) : (
                   <p className="text-sm text-muted-foreground">プラン情報なし</p>
                 )}
                 <Button variant="outline" size="sm" type="button" onClick={handleChangePlanClick}>
                   プランを変更
                 </Button>
               </div>
             </div>
          </div>
        </section>

        <section className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <Bell className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">通知設定</h2>
            </div>
          </div>
          <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-900">メール通知</h3>
                <p className="text-sm text-gray-500">添削完了時やお知らせをメールで受け取る</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  name="emailNotifications"
                  checked={userSettings?.emailNotifications || false}
                  onChange={handleChange}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-900">ブラウザ通知</h3>
                <p className="text-sm text-gray-500">ブラウザでリアルタイム通知を受け取る</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  name="browserNotifications"
                  checked={userSettings?.browserNotifications || false}
                  onChange={handleChange}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </section>

        <section className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">セキュリティ</h2>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <button 
              type="button"
              className="w-full text-left px-4 py-3 border border-gray-300 rounded-md hover:bg-gray-50"
              onClick={() => window.location.href = '/settings/password'}
            >
              パスワードを変更
            </button>
            <button 
              type="button"
              className="w-full text-left px-4 py-3 border border-gray-300 rounded-md hover:bg-gray-50"
              onClick={() => window.location.href = '/settings/2fa'}
            >
              二段階認証を設定
            </button>
          </div>
        </section>

        <section className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <User className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">アカウント管理</h2>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <LogoutButton />
            <button 
              type="button"
              className="w-full text-left px-4 py-3 text-red-600 hover:bg-red-50 rounded-md"
              onClick={() => {
                if (window.confirm('本当にアカウントを削除しますか？この操作は取り消せません。')) {
                  if (process.env.NODE_ENV !== 'production' || !session) {
                    toast.success('アカウントを削除しました (開発モード)');
                    window.location.href = '/';
                    return;
                  }
                  
                  fetch(`${API_BASE_URL}/api/v1/auth/delete-account`, {
                    method: 'DELETE',
                    credentials: 'include',
                    headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${session.accessToken}`
                    },
                  })
                  .then(response => {
                    if (response.ok) {
                      toast.success('アカウントを削除しました');
                      window.location.href = '/';
                    } else {
                      throw new Error('アカウントの削除に失敗しました');
                    }
                  })
                  .catch(error => {
                    console.error('アカウント削除エラー:', error);
                    toast.error('アカウントの削除に失敗しました');
                  });
                }
              }}
            >
              アカウントを削除
            </button>
          </div>
        </section>

        <div className="mt-8 flex justify-end">
          <Button type="submit" disabled={saving || status !== 'authenticated'}>
            {saving ? '保存中...' : '変更を保存'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default SettingsPage;
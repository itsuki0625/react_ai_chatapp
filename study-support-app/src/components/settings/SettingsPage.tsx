"use client";

import React, { useState, useEffect } from 'react';
import { Bell, User, Shield, LogOut } from 'lucide-react';
import LogoutButton from '@/components/common/LogoutButton';
import { API_BASE_URL } from '@/lib/config';
import { toast } from 'react-hot-toast';
import { useSession } from 'next-auth/react';

const SettingsPage = () => {
  const { data: session, status } = useSession();
  const [userSettings, setUserSettings] = useState({
    email: '',
    name: '',
    emailNotifications: true,
    browserNotifications: false,
    theme: 'light'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Function to fetch user settings (now assumes session and accessToken are ready)
  const fetchUserSettings = async () => {
    // This function is now called only when status is 'authenticated' and session.accessToken exists
    if (!session || !session.accessToken) {
        console.error('fetchUserSettings called without valid session/accessToken');
        setLoading(false); // Stop loading if something went wrong
        return;
    }
    try {
      // setLoading(true); // setLoading is handled in the useEffect now
      console.log('API接続先:', API_BASE_URL);
      console.log('セッション情報 (fetchUserSettings):', session);

      try {
        // APIからのデータ取得を試みる
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.accessToken}`
          },
        });

        console.log('ユーザー情報レスポンスステータス:', response.status);
        
        if (response.ok) {
          const userData = await response.json();
          console.log('取得したユーザーデータ:', userData);
          
          // ユーザーの詳細情報を取得
          const userDetailResponse = await fetch(`${API_BASE_URL}/api/v1/auth/user-settings`, {
            method: 'GET',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.accessToken}`
            },
          });

          console.log('設定情報レスポンスステータス:', userDetailResponse.status);

          if (userDetailResponse.ok) {
            const userDetailData = await userDetailResponse.json();
            console.log('取得した設定データ:', userDetailData);
            
            setUserSettings({
              email: userData.email || '',
              name: userDetailData.full_name || '',
              emailNotifications: userDetailData.email_notifications || false,
              browserNotifications: userDetailData.browser_notifications || false,
              theme: userDetailData.theme || 'light'
            });
          } else {
            // 詳細情報の取得に失敗した場合のフォールバック
            console.warn('Failed to fetch user details, using basic info.');
            setUserSettings({
              email: userData.email || '',
              name: userData.full_name || '' , // Fallback name from /me if available?
              emailNotifications: true, // Default fallback
              browserNotifications: false,
              theme: 'light'
            });
          }
        } else {
          // /api/v1/auth/me の取得に失敗した場合
          console.error(`Failed to fetch /me endpoint: ${response.status}`);
          // ここでエラー処理（例：ログインページへリダイレクト、エラー表示）
          // setUserSettings({...demoData}); // Or handle error state
          toast.error('ユーザー情報の取得に失敗しました。');
        }
      } catch (apiError) {
        console.error('API接続エラー:', apiError);
        // setUserSettings({...demoData}); // Or handle error state
        toast.error('APIへの接続中にエラーが発生しました。');
      }
    } catch (error) {
      console.error('ユーザー設定の取得エラー (outer):', error);
    } finally {
       setLoading(false); // Set loading to false after fetch attempt (success or fail)
    }
  };

  // useEffect hook to manage loading state and trigger fetch based on session status
  useEffect(() => {
    console.log('Session status:', status);
    if (status === 'loading') {
      setLoading(true);
      return; // Wait until status is determined
    }

    if (status === 'authenticated') {
      if (session?.accessToken) {
        fetchUserSettings();
      } else {
        // This case should ideally not happen if status is authenticated
        console.error('Authenticated status but no access token found.');
        setLoading(false);
        // Handle error appropriately, maybe redirect to login?
        toast.error('認証エラーが発生しました。再ログインしてください。');
      }
    } else { // status === 'unauthenticated'
      console.log('User is unauthenticated. Showing demo data or redirecting...');
      // Optionally redirect to login or show demo data
      setUserSettings({ // Set demo data
        email: 'demo@example.com',
        name: 'デモユーザー',
        emailNotifications: true,
        browserNotifications: false,
        theme: 'light'
      });
      setLoading(false);
      // Or redirect: router.push('/login?error=session_expired');
    }
  }, [session, status]); // Depend on session object and status

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setUserSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      
      const requestData = {
        full_name: userSettings.name,
        email_notifications: userSettings.emailNotifications,
        browser_notifications: userSettings.browserNotifications,
        theme: userSettings.theme
      };
      
      console.log('設定更新データ:', requestData);
      
      // 未認証の場合はデモ動作
      if (!session) {
        toast.success('設定を更新しました (デモモード)');
        setSaving(false);
        return;
      }
      
      // セッションがある場合は実際のAPI呼び出し
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/user-settings`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.accessToken}`
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('設定更新エラー:', errorText);
        throw new Error('設定の更新に失敗しました');
      }

      toast.success('設定を更新しました');
    } catch (error) {
      console.error('設定更新エラー:', error);
      toast.error(`設定の更新に失敗しました: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
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
        {/* プロフィール設定 */}
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
                value={userSettings.name}
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
                value={userSettings.email}
                disabled
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-gray-100 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">メールアドレスの変更はサポートにお問い合わせください</p>
            </div>
          </div>
        </section>

        {/* 通知設定 */}
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
                  checked={userSettings.emailNotifications}
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
                  checked={userSettings.browserNotifications}
                  onChange={handleChange}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </section>

        {/* セキュリティ設定 */}
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

        {/* アカウント管理 */}
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
                  // 開発環境では実際にAPIを呼び出さない
                  if (process.env.NODE_ENV !== 'production' || !session) {
                    toast.success('アカウントを削除しました (開発モード)');
                    window.location.href = '/';
                    return;
                  }
                  
                  // 本番環境ではアカウント削除APIを呼び出す
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

        <div className="mt-6">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {saving ? '保存中...' : '設定を保存'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SettingsPage;
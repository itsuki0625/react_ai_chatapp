"use client";

import React, { useState } from 'react';
import { Bell, User, Shield, LogOut } from 'lucide-react';
import LogoutButton from '@/components/common/LogoutButton';
import { API_BASE_URL } from '@/lib/config';

const SettingsPage = () => {
  const [userSettings, setUserSettings] = useState({
    email: 'user@example.com',
    name: '山田 太郎',
    emailNotifications: true,
    browserNotifications: false,
    theme: 'light'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setUserSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">設定</h1>

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
              <button className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
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
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
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
          <button className="w-full text-left px-4 py-3 border border-gray-300 rounded-md hover:bg-gray-50">
            パスワードを変更
          </button>
          <button className="w-full text-left px-4 py-3 border border-gray-300 rounded-md hover:bg-gray-50">
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
          <button className="w-full text-left px-4 py-3 text-red-600 hover:bg-red-50 rounded-md">
            アカウントを削除
          </button>
        </div>
      </section>
    </div>
  );
};

export default SettingsPage;
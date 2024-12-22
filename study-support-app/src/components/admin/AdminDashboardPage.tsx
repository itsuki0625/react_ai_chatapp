"use client";

import React, { useState } from 'react';
import { 
  Users,
  UserCheck,
  School,
  FileText,
  Activity,
  Settings,
  AlertTriangle,
  TrendingUp,
  Search,
  MoreVertical
} from 'lucide-react';

interface UserStats {
  totalStudents: number;
  activeStudents: number;
  totalTeachers: number;
  activeTeachers: number;
}

interface SystemStats {
  documentsReviewed: number;
  averageResponseTime: string;
  systemUptime: string;
  activeChats: number;
}

const AdminDashboard = () => {
  const [userStats] = useState<UserStats>({
    totalStudents: 1250,
    activeStudents: 980,
    totalTeachers: 45,
    activeTeachers: 38
  });

  const [systemStats] = useState<SystemStats>({
    documentsReviewed: 3420,
    averageResponseTime: '2.5時間',
    systemUptime: '99.9%',
    activeChats: 24
  });

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">管理ダッシュボード</h1>
        <p className="mt-1 text-sm text-gray-500">
          システム全体の統計と管理機能
        </p>
      </div>

      {/* メイン統計 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-600">総生徒数</p>
              <p className="text-2xl font-semibold text-gray-900">{userStats.totalStudents}</p>
              <p className="text-sm text-green-600">
                アクティブ: {userStats.activeStudents}
              </p>
            </div>
            <Users className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-600">総教師数</p>
              <p className="text-2xl font-semibold text-gray-900">{userStats.totalTeachers}</p>
              <p className="text-sm text-green-600">
                アクティブ: {userStats.activeTeachers}
              </p>
            </div>
            <UserCheck className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-600">添削完了数</p>
              <p className="text-2xl font-semibold text-gray-900">{systemStats.documentsReviewed}</p>
              <p className="text-sm text-blue-600">
                平均応答時間: {systemStats.averageResponseTime}
              </p>
            </div>
            <FileText className="h-8 w-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-600">システム稼働率</p>
              <p className="text-2xl font-semibold text-gray-900">{systemStats.systemUptime}</p>
              <p className="text-sm text-green-600">正常稼働中</p>
            </div>
            <Activity className="h-8 w-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* システムアラート */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">システムアラート</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-start p-4 bg-yellow-50 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5 mr-3" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">高負荷検知</p>
                  <p className="text-sm text-yellow-700">
                    チャットサーバーの負荷が上昇しています
                  </p>
                </div>
              </div>
              <div className="flex items-start p-4 bg-blue-50 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-blue-500 mt-0.5 mr-3" />
                <div>
                  <p className="text-sm font-medium text-blue-800">バックアップ完了</p>
                  <p className="text-sm text-blue-700">
                    システムバックアップが正常に完了しました
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* アクティビティグラフ */}
        <div className="bg-white rounded-lg shadow lg:col-span-2">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">利用統計</h2>
          </div>
          <div className="p-6">
            <div className="h-64 flex items-center justify-center text-gray-500">
              ここにグラフを表示
            </div>
          </div>
        </div>

        {/* クイックアクション */}
        <div className="bg-white rounded-lg shadow lg:col-span-3">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">システム管理</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="flex items-center justify-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100">
                <Users className="h-6 w-6 text-gray-600 mr-2" />
                <span className="text-sm font-medium text-gray-900">ユーザー管理</span>
              </button>
              <button className="flex items-center justify-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100">
                <School className="h-6 w-6 text-gray-600 mr-2" />
                <span className="text-sm font-medium text-gray-900">学校管理</span>
              </button>
              <button className="flex items-center justify-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100">
                <Settings className="h-6 w-6 text-gray-600 mr-2" />
                <span className="text-sm font-medium text-gray-900">システム設定</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
'use client';

import React from 'react';
import { ContentManagement } from '@/components/feature/admin/ContentManagement';
import { AdminNavBar } from '@/components/feature/admin/AdminNavBar';

const AdminContentPage = () => {
  return (
    <div>
      <AdminNavBar />
      <div className="min-h-screen bg-gray-50 p-6">
        {/* <h1 className="text-2xl font-semibold text-gray-900 mb-6">コンテンツ管理</h1> */}
        {/* ContentManagement コンポーネント内でタイトル表示がされている想定 */}
        <ContentManagement />
      </div>
    </div>
  );
};

export default AdminContentPage; 
'use client';

import React from 'react';
// import { useAuthHelpers } from '@/lib/authUtils'; // 削除: 存在しないフック

interface ChatLayoutProps {
  children: React.ReactNode;
}

export default function ChatLayout({ children }: ChatLayoutProps) {
  // 削除: 認証・権限チェックロジック (ミドルウェアに委任)
  // const { hasPermission, isLoading, isAuthenticated } = useAuthHelpers();
  // if (isLoading) { ... }
  // if (!isAuthenticated) { ... }
  // if (!hasPermission('chat_session_read')) { ... }

  // 単純に子要素を返す
  return <>{children}</>;
} 
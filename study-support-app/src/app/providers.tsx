'use client';

import React from 'react';
import { SessionProvider } from 'next-auth/react';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatProvider } from '@/store/chat/ChatContext';
import ErrorBoundary from '@/components/common/ErrorBoundary';

// React DevTools関連のエラーを抑制
if (typeof window !== 'undefined') {
  const originalError = console.error;
  console.error = (...args) => {
    const message = args[0]?.toString() || '';
    if (message.includes('recentlyCreatedOwnerStacks') || 
        message.includes('_owner') ||
        message.includes('DevTools')) {
      return; // React DevTools関連のエラーを無視
    }
    originalError.apply(console, args);
  };
}

// QueryClientを外部で作成して安定化
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      refetchOnWindowFocus: false,
      retry: 1,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <SessionProvider refetchOnWindowFocus={false}>
        <QueryClientProvider client={queryClient}>
          <ErrorBoundary>
            <ChatProvider>
              {children}
              <Toaster position="top-center" />
            </ChatProvider>
          </ErrorBoundary>
        </QueryClientProvider>
      </SessionProvider>
    </ErrorBoundary>
  );
} 
'use client';

import React from 'react';
import { SessionProvider } from 'next-auth/react';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SimpleChatProvider } from '@/store/chat/SimpleChatContext';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(() => new QueryClient());

  return (
    <SessionProvider refetchOnWindowFocus={true}>
      <QueryClientProvider client={queryClient}>
        <SimpleChatProvider>
          <Toaster position="top-center" />
          {children}
        </SimpleChatProvider>
      </QueryClientProvider>
    </SessionProvider>
  );
} 
'use client';

import React from 'react';
import { SessionProvider, useSession } from 'next-auth/react';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatProvider } from '@/store/chat/ChatContext';

function AppChatProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  
  const authToken = session?.user?.accessToken || null;

  const tokenForChatProvider = status === 'loading' ? null : authToken;

  if (status === "loading") {
    console.log("Auth session loading, ChatProvider will init with null token.");
  }

  return (
    <ChatProvider initialAuthToken={tokenForChatProvider}>
      {children}
    </ChatProvider>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(() => new QueryClient());

  return (
    <SessionProvider refetchOnWindowFocus={true}>
      <QueryClientProvider client={queryClient}>
        <AppChatProvider>
          <Toaster position="top-center" />
          {children}
        </AppChatProvider>
      </QueryClientProvider>
    </SessionProvider>
  );
} 
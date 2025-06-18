"use client";

import { useState } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import Image from 'next/image';
import { Menu, X } from 'lucide-react';
import { Navigation } from './Navigation';
import { useAuthError } from '@/hooks/useAuthError';

export const AppLayout = ({ children }: { children: React.ReactNode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { status } = useSession();
  
  // 認証エラーの自動処理を有効化
  useAuthError();

  if (status === 'loading') {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="lg:hidden fixed top-4 right-4 z-40">
        <button
          className="p-2 rounded-md bg-white shadow-sm"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>

      <div className={`
        fixed top-0 left-0 z-30 h-full w-64 transform bg-white shadow-lg transition-transform duration-200 ease-in-out overflow-y-auto
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <Link href="/dashboard">
              <Image
                src="/logo.svg"
                alt="SmartAO Logo"
                width={120}
                height={32}
                priority
              />
            </Link>
            <button
              className="lg:hidden p-2"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        <Navigation />
      </div>

      <main className="lg:pl-64 h-screen flex flex-col">
        <div className="py-6 px-4 sm:px-6 lg:px-8 flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

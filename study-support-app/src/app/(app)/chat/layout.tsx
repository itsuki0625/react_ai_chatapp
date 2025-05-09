"use client";

import { useSession } from "next-auth/react";
import { ReactNode } from "react";
import Link from "next/link";

interface ChatLayoutProps {
  children: ReactNode;
}

export default function ChatLayout({ children }: ChatLayoutProps) {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <p>Loading...</p>;
  }

  if (status === "unauthenticated" || !session?.user?.permissions) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)] text-center">
        <h2 className="text-2xl font-semibold mb-4">アクセス権限がありません</h2>
        <p className="mb-2">
          この機能をご利用いただくには、スタンダードプラン以上のご契約が必要です。
        </p>
        <Link href="/subscription/plans" className="text-blue-600 hover:underline">
          プランを確認する
        </Link>
      </div>
    );
  }

  const hasChatPermission = session.user.permissions.includes("chat_session_read");

  if (!hasChatPermission) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)] text-center">
        <h2 className="text-2xl font-semibold mb-4">アクセス権限がありません</h2>
        <p className="mb-2">
          この機能をご利用いただくには、スタンダードプラン以上のご契約が必要です。
        </p>
        <Link href="/subscription/plans" className="text-blue-600 hover:underline">
          プランを確認する
        </Link>
      </div>
    );
  }

  return <>{children}</>;
} 
"use client";

import { ApplicationList } from "@/components/application/ApplicationList";

export default function ApplicationPage() {
  if (process.env.NODE_ENV === 'production') {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <p className="text-xl">開発中です。公開までお待ちください。</p>
      </div>
    );
  }
  return <ApplicationList />;
}
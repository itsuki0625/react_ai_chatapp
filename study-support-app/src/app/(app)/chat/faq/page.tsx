"use client";
import { Metadata } from 'next';
import ChatPage from '@/components/chat/ChatPage';
import { ChatTypeEnum } from '@/types/chat';

export const metadata: Metadata = {
  title: 'FAQチャット',
  description: 'よくある質問にAIが答えます。',
};

export default function FaqPage() {
  if (process.env.NODE_ENV === 'production') {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <p className="text-xl">開発中です。公開までお待ちください。</p>
      </div>
    );
  }
  return <ChatPage key="fixedChatPageKey" initialChatType={ChatTypeEnum.FAQ} />;
}
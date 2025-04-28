import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChatType } from '@/types/chat';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '学習支援チャット',
  description: 'AIがあなたの学習をサポートします。',
};

export default function ChatTypePage() {
  const chatType = ChatType.STUDY_SUPPORT;

  return (
    <div className="flex h-full w-full">
      <ChatSidebar chatType={chatType} />
      <div className="flex-1 flex flex-col">
        <ChatWindow chatType={chatType} />
      </div>
    </div>
  );
} 
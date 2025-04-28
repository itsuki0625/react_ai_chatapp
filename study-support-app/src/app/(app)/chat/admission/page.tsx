import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChatType } from '@/types/chat';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '総合型選抜チャット',
  description: 'AIが総合型選抜に関する相談に乗ります。',
};

export default function ChatTypePage() {
  const chatType = ChatType.ADMISSION;

  return (
    <div className="flex h-full w-full">
      <ChatSidebar chatType={chatType} />
      <div className="flex-1 flex flex-col">
        <ChatWindow chatType={chatType} />
      </div>
    </div>
  );
} 
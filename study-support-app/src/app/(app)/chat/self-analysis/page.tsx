import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChatType } from '@/types/chat';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '自己分析チャット',
  description: 'AIとの対話を通じて自己理解を深めましょう。',
};

export default function ChatTypePage() {
  const chatType = ChatType.SELF_ANALYSIS;

  return (
    <div className="flex h-full w-full">
      <ChatSidebar chatType={chatType} />
      <div className="flex-1 flex flex-col">
        {/* sessionId を渡さないことで新規チャットモードになる */}
        <ChatWindow chatType={chatType} />
      </div>
    </div>
  );
} 
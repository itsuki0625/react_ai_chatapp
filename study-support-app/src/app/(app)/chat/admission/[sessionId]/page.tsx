import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChatType } from '@/types/chat';
import { Metadata } from 'next';

// Next.js App Routerの標準的な型を使用
type PageProps = {
  params: { sessionId: string };
  searchParams: { [key: string]: string | string[] | undefined };
};

export async function generateMetadata({ params }: { params: { sessionId: string } }): Promise<Metadata> {
    return {
        title: `総合型選抜チャット - ${params.sessionId.substring(0, 8)}...`,
    };
}

export default function ChatSessionPage({ params }: PageProps) {
  const chatType = ChatType.ADMISSION;
  const { sessionId } = params;

  return (
    <div className="flex h-full w-full">
      <ChatSidebar chatType={chatType} currentSessionId={sessionId} />
      <div className="flex-1 flex flex-col">
        <ChatWindow chatType={chatType} sessionId={sessionId} />
      </div>
    </div>
  );
} 
import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChatType } from '@/types/chat';
import { Metadata } from 'next';

interface ChatSessionPageProps {
  params: {
    sessionId: string;
  };
}

export async function generateMetadata({ params }: ChatSessionPageProps): Promise<Metadata> {
    return {
        title: `学習支援チャット - ${params.sessionId.substring(0, 8)}...`,
    };
}

export default function ChatSessionPage({ params }: ChatSessionPageProps) {
  const chatType = ChatType.STUDY_SUPPORT;
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
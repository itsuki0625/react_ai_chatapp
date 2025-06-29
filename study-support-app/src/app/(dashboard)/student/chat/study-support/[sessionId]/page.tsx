import { Metadata } from 'next';
import ChatPage from '@/components/feature/student/chat/ChatPage';
import { ChatTypeEnum } from '@/types/chat';

interface ChatSessionPageProps {
  params: {
    sessionId: string;
  };
}

export async function generateMetadata(
  { params }: ChatSessionPageProps
): Promise<Metadata> {
  return {
    title: `学習支援チャットセッション - ${params.sessionId.substring(0, 8)}...`,
  };
}

export default function StudySupportChatSessionPage({ params }: ChatSessionPageProps) {
  return (
    <ChatPage
      initialChatType={ChatTypeEnum.STUDY_SUPPORT}
      initialSessionId={params.sessionId}
    />
  );
} 
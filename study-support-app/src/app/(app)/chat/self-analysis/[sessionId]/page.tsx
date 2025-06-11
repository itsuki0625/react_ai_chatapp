import { Metadata } from 'next';
import ChatPage from '@/components/chat/ChatPage';
import { ChatTypeEnum } from '@/types/chat';

interface ChatSessionPageProps {
  params: {
    sessionId: string;
  };
}

export async function generateMetadata(
  { params }: ChatSessionPageProps
): Promise<Metadata> {
  // TODO: 必要であればAPIを叩いてセッションタイトルなどを取得
  return {
    title: `自己分析チャットセッション - ${params.sessionId.substring(0, 8)}...`,
  };
}

export default function SelfAnalysisChatSessionPage({ params }: ChatSessionPageProps) {
  return (
    <ChatPage
      key={`self-analysis-${params.sessionId}`}
      initialChatType={ChatTypeEnum.SELF_ANALYSIS}
      initialSessionId={params.sessionId}
    />
  );
} 
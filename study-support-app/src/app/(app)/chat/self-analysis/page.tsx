import { Metadata } from 'next';
import ChatPage from '@/components/chat/ChatPage';
import { ChatTypeEnum } from '@/types/chat';

export const metadata: Metadata = {
  title: '自己分析チャット',
  description: 'AIとの対話を通じて自己理解を深めましょう。',
};

export default function SelfAnalysisChatPage() {
  return <ChatPage initialChatType={ChatTypeEnum.SELF_ANALYSIS} />;
} 
import { Metadata } from 'next';
import ChatPage from '@/components/chat/ChatPage';
import { ChatTypeEnum } from '@/types/chat';

export const metadata: Metadata = {
  title: 'FAQチャット',
  description: 'よくある質問にAIが答えます。',
};

export default function Page() {
  return <ChatPage key="fixedChatPageKey" initialChatType={ChatTypeEnum.FAQ} />;
}
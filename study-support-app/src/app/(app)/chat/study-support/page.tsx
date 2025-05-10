import { Metadata } from 'next';
import ChatPage from '@/components/chat/ChatPage';
import { ChatTypeEnum } from '@/types/chat';

export const metadata: Metadata = {
  title: '学習支援チャット',
  description: 'AIがあなたの学習をサポートします。',
};

export default function StudySupportChatPage() {
  return <ChatPage initialChatType={ChatTypeEnum.STUDY_SUPPORT} />;
} 
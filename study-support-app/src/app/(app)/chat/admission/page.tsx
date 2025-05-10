import { Metadata } from 'next';
import ChatPage from '@/components/chat/ChatPage';
import { ChatTypeEnum } from '@/types/chat';

export const metadata: Metadata = {
  title: '総合型選抜チャット',
  description: 'AIが総合型選抜に関する相談に乗ります。',
};

export default function AdmissionChatPage() {
  return <ChatPage initialChatType={ChatTypeEnum.ADMISSION} />;
} 
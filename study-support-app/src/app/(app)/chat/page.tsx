import { Metadata } from 'next';
import GenericLandingPage from '@/components/chat/GenericLandingPage';

export const metadata: Metadata = {
  title: '一般チャットAI',
  description: 'AIと自由に対話して、様々なことを相談できます',
};

export default function GeneralChatPage() {
  return <GenericLandingPage chatType="general" />;
}
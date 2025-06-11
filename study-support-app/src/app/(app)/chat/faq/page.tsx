import { Metadata } from 'next';
import GenericLandingPage from '@/components/chat/GenericLandingPage';

export const metadata: Metadata = {
  title: 'FAQヘルプAI',
  description: 'よくある質問にAIが迅速にお答えします',
};

export default function FaqPage() {
  return <GenericLandingPage chatType="faq" />;
}
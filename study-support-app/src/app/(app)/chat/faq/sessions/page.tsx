import { Metadata } from 'next';
import GenericSessionsPage from '@/components/chat/GenericSessionsPage';

export const metadata: Metadata = {
  title: 'FAQセッション履歴',
  description: 'FAQチャットのセッション履歴を管理',
};

export default function FaqSessionsRoute() {
  return <GenericSessionsPage chatType="faq" />;
} 
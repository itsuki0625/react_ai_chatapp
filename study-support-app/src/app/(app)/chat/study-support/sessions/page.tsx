import { Metadata } from 'next';
import GenericSessionsPage from '@/components/chat/GenericSessionsPage';

export const metadata: Metadata = {
  title: '学習支援セッション履歴',
  description: '学習支援チャットのセッション履歴を管理',
};

export default function StudySupportSessionsRoute() {
  return <GenericSessionsPage chatType="study_support" />;
} 
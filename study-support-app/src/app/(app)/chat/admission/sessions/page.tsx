import { Metadata } from 'next';
import GenericSessionsPage from '@/components/chat/GenericSessionsPage';

export const metadata: Metadata = {
  title: '総合型選抜セッション履歴',
  description: '総合型選抜チャットのセッション履歴を管理',
};

export default function AdmissionSessionsRoute() {
  return <GenericSessionsPage chatType="admission" />;
} 
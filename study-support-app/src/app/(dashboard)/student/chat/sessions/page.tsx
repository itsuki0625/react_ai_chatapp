import { Metadata } from 'next';
import GenericSessionsPage from '@/components/feature/student/chat/GenericSessionsPage';

export const metadata: Metadata = {
  title: '一般チャットセッション履歴',
  description: '一般チャットのセッション履歴を管理',
};

export default function GeneralSessionsRoute() {
  return <GenericSessionsPage chatType="general" />;
} 
import { Metadata } from 'next';
import SelfAnalysisSessionsPage from '@/components/chat/SelfAnalysisSessionsPage';

export const metadata: Metadata = {
  title: '自己分析セッション履歴',
  description: '自己分析チャットのセッション履歴を管理',
};

export default function SelfAnalysisSessionsRoute() {
  return <SelfAnalysisSessionsPage />;
} 
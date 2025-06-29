import { Metadata } from 'next';
import SelfAnalysisLandingPage from '@/components/feature/student/chat/SelfAnalysisLandingPage';

export const metadata: Metadata = {
  title: '自己分析チャット',
  description: 'AIとの対話を通じて自己理解を深めましょう。',
};

export default function SelfAnalysisChatPage() {
  return <SelfAnalysisLandingPage />;
} 
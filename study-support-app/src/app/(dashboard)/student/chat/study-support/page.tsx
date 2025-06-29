import { Metadata } from 'next';
import GenericLandingPage from '@/components/feature/student/chat/GenericLandingPage';

export const metadata: Metadata = {
  title: '学習支援AI',
  description: 'あなたの学習をAIがパーソナライズしてサポートします',
};

export default function StudySupportPage() {
  return <GenericLandingPage chatType="study_support" />;
} 
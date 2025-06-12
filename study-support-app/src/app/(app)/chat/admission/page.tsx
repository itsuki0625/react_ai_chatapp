import { Metadata } from 'next';
import GenericLandingPage from '@/components/chat/GenericLandingPage';

export const metadata: Metadata = {
  title: '総合型選抜AI',
  description: '総合型選抜対策をAIがトータルサポートします',
};

export default function AdmissionPage() {
  return <GenericLandingPage chatType="admission" />;
} 
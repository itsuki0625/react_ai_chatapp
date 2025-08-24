'use client';

import { TeacherOnly } from '@/components/shared/TenantGuard';
import ChatViewer from '@/components/feature/teacher/ChatViewer';

interface PageProps {
  params: {
    id: string;
    sessionId: string;
  };
}

export default function TeacherChatViewerPage({ params }: PageProps) {
  return (
    <TeacherOnly>
      <ChatViewer 
        studentId={params.id} 
        sessionId={params.sessionId} 
      />
    </TeacherOnly>
  );
}
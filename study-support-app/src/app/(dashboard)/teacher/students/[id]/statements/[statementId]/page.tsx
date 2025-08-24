'use client';

import { TeacherOnly } from '@/components/shared/TenantGuard';
import StatementViewer from '@/components/feature/teacher/StatementViewer';

interface PageProps {
  params: {
    id: string;
    statementId: string;
  };
}

export default function TeacherStatementViewerPage({ params }: PageProps) {
  return (
    <TeacherOnly>
      <StatementViewer 
        studentId={params.id} 
        statementId={params.statementId} 
      />
    </TeacherOnly>
  );
}
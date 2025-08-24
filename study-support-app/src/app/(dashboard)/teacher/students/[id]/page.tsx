'use client';

import { TeacherOnly } from '@/components/shared/TenantGuard';
import StudentDetailPage from '@/components/feature/teacher/StudentDetailPage';

interface PageProps {
  params: {
    id: string;
  };
}

export default function TeacherStudentDetailPage({ params }: PageProps) {
  return (
    <TeacherOnly>
      <StudentDetailPage studentId={params.id} />
    </TeacherOnly>
  );
}
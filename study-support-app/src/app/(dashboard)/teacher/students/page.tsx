'use client';

import { TeacherOnly } from '@/components/shared/TenantGuard';
import TeacherStudentList from '@/components/feature/teacher/TeacherStudentList';

export default function TeacherStudentsPage() {
  return (
    <TeacherOnly>
      <TeacherStudentList />
    </TeacherOnly>
  );
}
'use client';

import { useParams } from 'next/navigation';
import SchoolDetailManagement from '@/components/feature/admin/SchoolDetailManagement';
import { AdminLayout } from '@/components/layout/AdminLayout';

export default function SchoolDetailPage() {
  const params = useParams();
  const schoolId = params.id as string;

  return (
    <AdminLayout>
      <SchoolDetailManagement schoolId={schoolId} />
    </AdminLayout>
  );
}

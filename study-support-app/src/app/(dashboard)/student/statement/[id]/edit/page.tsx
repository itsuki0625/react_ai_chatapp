'use client';

import { useParams } from 'next/navigation';
import StatementEditor from '@/components/feature/student/statement/StatementEditor';

interface Props {
  params: {
    id: string;
  };
}

export default function EditStatementPage() {
  const params = useParams();
  const id = typeof params.id === 'string' ? params.id : undefined;

  if (!id) {
    return <div className="p-4 text-red-500">無効なIDです。</div>;
  }

  return <StatementEditor statementId={id} />;
} 
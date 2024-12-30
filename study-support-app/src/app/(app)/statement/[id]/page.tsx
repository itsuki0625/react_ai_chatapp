'use client';

import { useEffect, useState } from 'react';
import StatementEditorPage from '@/components/statement/StatementEditorPage';

interface Props {
  params: {
    id: string;
  };
}

const getToken = () => {
  return localStorage.getItem('token');
};

export default function Page({ params }: Props) {
  const [statement, setStatement] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStatement() {
      try {
        const token = getToken();
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/statements/${params.id}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            credentials: 'include',
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch statement');
        }

        const data = await response.json();
        setStatement(data);
      } catch (err) {
        setError('志望理由書の取得に失敗しました');
        console.error('Error loading statement:', err);
      }
    }

    if (params.id) {
      loadStatement();
    }
  }, [params.id]);

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  if (!statement) {
    return <div className="p-4">Loading...</div>;
  }

  return <StatementEditorPage id={params.id} initialData={statement} />;
}
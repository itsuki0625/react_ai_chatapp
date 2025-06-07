'use client';

import { useParams } from 'next/navigation';
import AppShell from '@/components/statement/editor/AppShell';

// データ取得や元のロジックは一旦コメントアウトまたは削除し、
// あとでAppShell内部やZustandと連携するように再構築します。

// interface Props {
//   params: {
//     id: string;
//   };
// }

export default function EditStatementShellPage() {
  const params = useParams();
  const id = typeof params.id === 'string' ? params.id : undefined;

  console.log('[EditStatementShellPage] params:', params);
  console.log('[EditStatementShellPage] params.id:', params?.id); // params自体がnull/undefinedの可能性も考慮
  console.log('[EditStatementShellPage] id to pass to AppShell:', id);

  // ここで以前のデータ取得ロジック（fetchなど）を実行し、
  // draftIdなどの情報をAppShellに渡すこともできますが、
  // まずはAppShellが表示されることを確認します。

  // if (isLoading || sessionStatus === 'loading') { ... }
  // if (error) { ... }
  // if (!statement) { ... }

  return <AppShell draftIdFromParams={id} />;
} 
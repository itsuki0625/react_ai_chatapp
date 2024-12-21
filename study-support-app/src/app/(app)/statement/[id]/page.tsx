import StatementEditorPage from '@/components/statement/StatementEditorPage';

interface Props {
  params: {
    id: string;
  };
}

async function getStatement(id: string) {
    // データ取得ロジック
}
  
export default async function Page({ params }: Props) {
    try {
      const statement = await getStatement(params.id);
      return <StatementEditorPage id={params.id} initialData={statement} />;
    } catch (error) {
      return <div>エラーが発生しました</div>;
    }
}
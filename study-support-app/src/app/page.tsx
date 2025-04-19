import { redirect } from 'next/navigation';

export default function Home() {
  // ダッシュボードにリダイレクト
  redirect('/dashboard');
  
  // リダイレクトが機能しない場合のフォールバック
  return (
    <div className="flex items-center justify-center min-h-screen">
      <p>リダイレクト中...</p>
    </div>
  );
}

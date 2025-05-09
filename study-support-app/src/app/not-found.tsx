import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';

export default function NotFound() {
  return (
    <AppLayout>
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-4 sm:p-6">
        <div className="text-center space-y-6">
          <h1 className="text-6xl sm:text-8xl font-bold text-gray-900">404</h1>
          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-semibold text-gray-800">ページが見つかりません</h2>
            <p className="text-gray-600">お探しのページは存在しないか、移動した可能性があります。</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild variant="default" className="w-full sm:w-auto">
              <Link href="/dashboard" className="flex items-center gap-2">
                <Home className="h-4 w-4" />
                ダッシュボードに戻る
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full sm:w-auto">
              <Link href="/" className="flex items-center gap-2">
                トップページに戻る
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

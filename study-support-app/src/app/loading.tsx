import { AppLayout } from '@/components/layout/AppLayout';
import { Loader2 } from 'lucide-react';

export default function Loading() {
  return (
    <AppLayout>
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-4 sm:p-6">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl sm:text-2xl font-semibold text-gray-800">読み込み中...</h2>
            <p className="text-gray-600">しばらくお待ちください</p>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

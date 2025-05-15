import Link from 'next/link';
import Image from 'next/image';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="flex items-center gap-2 mb-6">
        <Image src="/logo_with_icon.svg" alt="SmartAO" width={64} height={64} className="h-12 sm:h-16 w-auto" />
      </div>

      <div className="bg-white shadow-md rounded-lg p-8 w-full max-w-md">
        <h2 className="text-2xl font-medium text-gray-800 mb-4">ようこそ</h2>
        <p className="text-gray-600 mb-6">
          SmartAOへようこそ。ログインして続行してください。
        </p>

        <div className="space-y-4">
          <Link
            href="/login"
            className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded text-center"
          >
            ログイン
          </Link>

          <Link
            href="/signup"
            className="block w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded text-center"
          >
            新規登録
          </Link>
        </div>
      </div>
    </div>
  );
}

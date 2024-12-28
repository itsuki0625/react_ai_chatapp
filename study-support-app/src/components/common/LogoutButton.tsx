import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

export default function LogoutButton() {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      const response = await apiClient.post('/api/v1/auth/logout'); 
      
      if (response.status === 200) {
        router.push('/login');
      } else {
        console.error('ログアウトに失敗しました');
      }
    } catch (error) {
      console.error('ログアウト中にエラーが発生しました:', error);
    }
  };

  return (
    <button
      onClick={handleLogout}
      className="px-4 py-2 text-white bg-red-600 rounded hover:bg-red-700"
    >
      ログアウト
    </button>
  );
} 
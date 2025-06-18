import { useEffect } from 'react';
import { signOut, useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export const useAuthError = () => {
  const { data: session, status } = useSession();
  const router = useRouter();

  const handleAuthError = async (error?: string) => {
    console.log('Authentication error detected:', error);
    
    try {
      // セッションを完全にクリア
      await signOut({ 
        redirect: false,
        callbackUrl: '/login'
      });
      
      // ローカルストレージとセッションストレージをクリア
      if (typeof window !== 'undefined') {
        localStorage.clear();
        sessionStorage.clear();
      }
      
      // ログインページにリダイレクト（セッション期限切れのメッセージ付き）
      router.push('/login?error=session_expired&status=logged_out');
      
    } catch (err) {
      console.error('Error during auth error handling:', err);
      
      // フォールバック: 強制的にページをリロード
      if (typeof window !== 'undefined') {
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = '/login?error=session_expired&status=logged_out';
      }
    }
  };

  // APIレスポンスの401エラーを自動検出
  useEffect(() => {
    const handleApiError = (event: Event) => {
      const customEvent = event as CustomEvent;
      if (customEvent.detail?.status === 401 || customEvent.detail?.error === 'Unauthorized') {
        handleAuthError('API_401_ERROR');
      }
    };

    // カスタムイベントリスナーを追加
    window.addEventListener('auth-error', handleApiError);
    
    return () => {
      window.removeEventListener('auth-error', handleApiError);
    };
  }, []);

  return {
    handleAuthError
  };
}; 
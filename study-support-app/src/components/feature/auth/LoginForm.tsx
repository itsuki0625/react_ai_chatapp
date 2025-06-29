import { useRouter, useSearchParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import React from 'react';
import { signIn, signOut, useSession } from 'next-auth/react';

export const LoginForm: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: session, status } = useSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string>('');
  const [sessionExpiredMessage, setSessionExpiredMessage] = useState<string | null>(null);

  // セッション期限切れの処理を簡素化
  const handleSessionExpired = () => {
    console.log('Session expired detected, clearing session...');
    
    setSessionExpiredMessage('セッションの有効期限が切れました。お手数ですが、再度ログインしてください。');
    setError('');
    
    // URLパラメータをクリア
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.delete('error');
      window.history.replaceState({}, '', url.toString());
    }
    
    // 非同期でsignOutを実行（エラーを無視）
    signOut({ 
      redirect: false,
      callbackUrl: '/login'
    }).catch(err => {
      console.error('Error during signOut (ignored):', err);
    });
  };

  // セッション状態の処理を簡素化
  useEffect(() => {
    console.log('セッション状態:', status, session);
    
    // エラー処理を最優先
    const errorParam = searchParams?.get('error');
    const hasSessionError = session?.error === 'RefreshAccessTokenError';
    
    if (errorParam === 'session_expired' || hasSessionError) {
      console.log('Session error detected:', { errorParam, hasSessionError });
      handleSessionExpired();
      return;
    }
    
    // 認証済みユーザーのリダイレクト処理
    if (status === 'authenticated' && session && !session.error) {
      // ログアウト直後の場合はリダイレクトを抑制
      const isLoggedOut = searchParams?.get('status') === 'logged_out';
      if (isLoggedOut) {
        console.log('ログアウト直後のため、リダイレクトを抑制');
        return;
      }
      
      console.log('認証済みユーザー:', session);
      
      // リダイレクト先を決定
      const redirectUrl = searchParams?.get('redirect') || getDashboardByRole(session.user.role);
      console.log('遷移先:', redirectUrl);
      router.push(redirectUrl);
    }
  }, [session, status, router, searchParams]);

  // ユーザーロールに基づいてダッシュボードURLを取得
  const getDashboardByRole = (role: string): string => {
    if (!role) return '/student/dashboard';
    
    if (role === '管理者') {
      return '/admin/dashboard';
    } else if (role === '教員') {
      return '/teacher/dashboard';
    } else {
      return '/student/dashboard';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSessionExpiredMessage(null);
    setDebugInfo('');

    console.log('=== LOGIN FORM SUBMIT START ===');
    setDebugInfo('フォーム送信開始');

    try {
      // テスト用の固定資格情報
      const testCredentials = {
        email: 'test@example.com',
        password: 'password'
      };
      
      // デバッグモードの判定
      const useTestCredentials = email === 'debug' || password === 'debug';
      const loginEmail = useTestCredentials ? testCredentials.email : email;
      const loginPassword = useTestCredentials ? testCredentials.password : password;
      
      console.log('ログイン情報:', { loginEmail, useTestCredentials });
      setDebugInfo(prev => prev + `\nログイン情報: ${loginEmail} (テストモード: ${useTestCredentials})`);
      
      if (useTestCredentials) {
        setDebugInfo(prev => prev + `\nテストモード: ${testCredentials.email}`);
      }
      
      // リダイレクト先の決定
      let redirectUrl = searchParams?.get('redirect') || searchParams?.get('redirect_to') || '/student/dashboard';
      redirectUrl = decodeURIComponent(redirectUrl);
      
      console.log('リダイレクト先:', redirectUrl);
      setDebugInfo(prev => prev + `\nリダイレクト先: ${redirectUrl}`);
      
      console.log('signIn関数呼び出し直前');
      setDebugInfo(prev => prev + '\nsignIn関数呼び出し直前');
      
      // NextAuthによるログイン
      console.log('signIn関数を呼び出し中...');
      const result = await signIn('credentials', {
        email: loginEmail,
        password: loginPassword,
        redirect: false,
        callbackUrl: redirectUrl
      });
      
      console.log('signIn関数呼び出し完了、結果:', result);
      setDebugInfo(prev => prev + `\nsignIn関数呼び出し完了`);
      setDebugInfo(prev => prev + `\nログイン結果: ${JSON.stringify(result)}`);
      
      if (result?.error) {
        console.error('ログインエラー:', result.error);
        setDebugInfo(prev => prev + `\nエラー発生: ${result.error}`);
        
        if (result.error === 'CredentialsSignin') {
          setError('ログイン情報が正しくありません。メールアドレスとパスワードを確認してください。');
        } else {
          setError('ログインに失敗しました: ' + result.error);
        }
        
        return;
      }
      
      if (!result?.ok) {
        console.log('ログイン結果がOKではない:', result);
        setError('ログイン処理中にエラーが発生しました。もう一度お試しください。');
        setDebugInfo(prev => prev + '\nログイン結果がOKではない');
        return;
      }
      
      console.log('ログイン成功');
      setDebugInfo(prev => prev + '\nログイン成功');
      
      // リダイレクト処理
      if (result?.url) {
        console.log('リダイレクト実行:', result.url);
        setDebugInfo(prev => prev + `\nリダイレクト実行: ${result.url}`);
        router.push(result.url);
      } else {
        // フォールバック
        console.log('フォールバックリダイレクト: /student/dashboard');
        setDebugInfo(prev => prev + '\nフォールバックリダイレクト: /student/dashboard');
        router.push('/student/dashboard');
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error('Login error in catch block:', err);
      setError('ログインに失敗しました: ' + errorMessage);
      setDebugInfo(prev => prev + `\n例外発生: ${errorMessage}`);
    } finally {
      console.log('=== LOGIN FORM SUBMIT END ===');
      setDebugInfo(prev => prev + '\nログイン処理終了');
      setIsLoading(false);
    }
  };

  // 完全リセット機能
  const handleCompleteReset = () => {
    if (typeof window !== 'undefined') {
      // 全ストレージをクリア
      localStorage.clear();
      sessionStorage.clear();
      
      // 全Cookieを削除
      document.cookie.split(";").forEach(c => {
        const eqPos = c.indexOf("=");
        const name = eqPos > -1 ? c.substr(0, eqPos).trim() : c.trim();
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
      });
      
      // ページリロード
      window.location.href = '/login';
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* セッション状態のデバッグ情報 */}
      {process.env.NODE_ENV !== 'production' && (
        <div className="p-2 bg-blue-50 text-blue-700 text-xs font-mono rounded">
          セッション状態: {status} | エラー: {searchParams?.get('error') || 'なし'}
        </div>
      )}
      
      {/* セッション切れメッセージの表示 */}
      {sessionExpiredMessage && (
        <div className="p-3 rounded bg-yellow-50 text-yellow-700 text-sm">
          {sessionExpiredMessage}
        </div>
      )}
      
      {error && (
        <div className="p-3 rounded bg-red-50 text-red-500 text-sm">
          {error}
        </div>
      )}
      
      {/* ローディング状態の表示 */}
      {status === 'loading' && (
        <div className="p-3 rounded bg-gray-50 text-gray-600 text-sm">
          認証状態を確認中...
        </div>
      )}
      
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          メールアドレス
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
      
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          パスワード
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
      
      <div>
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
            isLoading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
          } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
        >
          {isLoading ? 'ログイン中...' : 'ログイン'}
        </button>
      </div>
      
      {/* デバッグ情報 - 開発環境でのみ表示 */}
      {process.env.NODE_ENV !== 'production' && debugInfo && (
        <div className="mt-4 p-3 bg-gray-100 text-gray-700 font-mono text-xs whitespace-pre-wrap rounded">
          <strong>デバッグ情報:</strong>
          {debugInfo}
        </div>
      )}
      
      {/* 完全リセットボタン - 開発環境でのみ表示 */}
      {process.env.NODE_ENV !== 'production' && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-red-700 text-xs mb-2">デバッグ用: セッション/認証エラーが解決しない場合</p>
          <button
            type="button"
            onClick={handleCompleteReset}
            className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
          >
            完全リセット（全Cookie削除 + リロード）
          </button>
        </div>
      )}
      
      {/* サインアップへの案内 */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600">
          アカウントをお持ちでないですか？{' '}
          <a href="/signup" className="font-medium text-blue-600 hover:text-blue-500">
            新規登録はこちら
          </a>
        </p>
      </div>
    </form>
  );
}; 
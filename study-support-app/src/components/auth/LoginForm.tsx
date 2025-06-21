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

  // セッション期限切れの自動検出と処理
  const handleSessionExpired = () => {
    console.log('Session expired detected, setting message and clearing session...');
    
    setSessionExpiredMessage('セッションの有効期限が切れました。お手数ですが、再度ログインしてください。');
    setError('');
    
    // URLパラメータをクリア
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.delete('error');
      window.history.replaceState({}, '', url.toString());
    }
    
    // セッションとローカルストレージの即座のクリア
    if (typeof window !== 'undefined') {
      localStorage.clear();
      sessionStorage.clear();
      // NextAuthのCookieも削除
      document.cookie = 'next-auth.session-token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
      document.cookie = '__Secure-next-auth.session-token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; Secure;';
      document.cookie = 'next-auth.csrf-token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
      document.cookie = '__Host-next-auth.csrf-token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; Secure;';
    }
    
    // 非同期でsignOutを実行（失敗しても処理を続行）
    signOut({ 
      redirect: false,
      callbackUrl: '/login'
    }).then(() => {
      console.log('Session cleared successfully');
    }).catch(err => {
      console.error('Error during signOut:', err);
      // エラーが発生してもページは使用可能な状態にする
    });
  };

  // セッション状態を監視
  useEffect(() => {
    console.log('セッション状態:', status, session);
    
    // RefreshAccessTokenErrorまたはsession_expiredエラーがある場合は先に処理
    const errorParam = searchParams?.get('error');
    const hasSessionError = session?.error === 'RefreshAccessTokenError';
    
    if (errorParam === 'session_expired' || hasSessionError) {
      console.log('Session expired or refresh error detected:', { errorParam, hasSessionError });
      handleSessionExpired();
      return; // 早期リターンでその他の処理をスキップ
    }
    
    // ログアウト直後かどうかを確認
    const isLoggedOut = searchParams?.get('status') === 'logged_out';

    // ログアウト直後 *でない* 場合に、認証済みならリダイレクト
    if (status === 'authenticated' && session && !isLoggedOut && !hasSessionError) {
      console.log('認証済み (ログアウト直後ではない):', session);
      
      // ユーザーロールに基づいてリダイレクト先を決定
      const redirectUrl = searchParams?.get('redirect') || getDashboardByRole(session.user.role);
      console.log('遷移先:', redirectUrl);
      router.push(redirectUrl);
    } else if (isLoggedOut) {
        console.log('ログインページ表示 (ログアウト直後のためリダイレクト抑制)');
    }
  }, [session, status, router, searchParams]);
  
  // URLパラメータのエラーチェック処理は上記のuseEffectに統合済み

  // ユーザーロールに基づいてダッシュボードURLを取得
  const getDashboardByRole = (role: string): string => {
    if (!role) return '/dashboard';
    
    // 単一のロールに基づいて遷移先を決定
    if (role === '管理者') {
      return '/admin/dashboard';
    } else if (role === '教員') {
      return '/teacher/dashboard';
    } else {
      return '/dashboard';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSessionExpiredMessage(null);
    setDebugInfo('');

    try {
      // テスト用の固定資格情報
      const testCredentials = {
        email: 'test@example.com',
        password: 'password'
      };
      
      // 実際の入力値を使用するか、テスト用の資格情報を使用するか
      const useTestCredentials = email === 'debug' || password === 'debug';
      const loginEmail = useTestCredentials ? testCredentials.email : email;
      const loginPassword = useTestCredentials ? testCredentials.password : password;
      
      if (useTestCredentials) {
        setDebugInfo(prev => prev + `\nテストモード: ${testCredentials.email}`);
      }
      
      // デフォルトリダイレクト先はログイン後に適切なダッシュボードに変更される
      let redirectUrl = searchParams?.get('redirect') || searchParams?.get('redirect_to') || '/dashboard';
      
      // URLデコードして正しいパスを取得
      redirectUrl = decodeURIComponent(redirectUrl);
      
      console.log('リダイレクト先URL (デコード後):', redirectUrl);
      setDebugInfo(prev => prev + `\nリダイレクト先: ${redirectUrl}`);

      // NextAuthによるログイン
      console.log('ログイン試行:', loginEmail);
      setDebugInfo(prev => prev + `\nログイン試行: ${loginEmail}`);
      
      const result = await signIn('credentials', {
        email: loginEmail,
        password: loginPassword,
        redirect: false,
        callbackUrl: redirectUrl
      });
      
      console.log('ログイン結果:', result);
      setDebugInfo(prev => prev + `\nログイン結果: ${JSON.stringify(result)}`);
      
      if (result?.error) {
        console.error('ログインエラー詳細:', result.error);
        
        // エラータイプに基づいてメッセージをカスタマイズ
        if (result.error === 'CredentialsSignin') {
          setError('ログイン情報が正しくありません。メールアドレスとパスワードを確認してください。');
        } else {
          setError('ログインに失敗しました: ' + result.error);
        }
        
        setDebugInfo(prev => prev + `\nエラー: ${result.error}`);
        setIsLoading(false);
        return;
      }
      
      if (!result?.ok) {
        setError('ログイン処理中にエラーが発生しました。もう一度お試しください。');
        setDebugInfo(prev => prev + '\n結果がOKではありません');
        setIsLoading(false);
        return;
      }
      
      console.log('ログイン成功、セッション確立中...');
      setDebugInfo(prev => prev + '\nログイン成功、セッション確立中...');
      
      // ログイン成功後、result.url があればそのURLにリダイレクト
      if (result?.url) {
        // 必要であれば、ここで result.url から status=logged_out や error などの
        // 不要なクエリパラメータを削除する処理を追加できます。
        // 例:
        // const finalRedirectUrl = new URL(result.url, window.location.origin);
        // finalRedirectUrl.searchParams.delete('status');
        // finalRedirectUrl.searchParams.delete('error');
        // router.push(finalRedirectUrl.pathname + finalRedirectUrl.search);
        
        // 現状のログでは result.url にクエリパラメータが含まれていないため、そのまま使用
        router.push(result.url);
      } else {
        // result.url がないという予期せぬ状況の場合、フォールバックとしてダッシュボードへ
        // (あるいはエラー表示など、適切な処理)
        // このフォールバックも、status=logged_out を考慮する必要がある
        const fallbackRedirectUrl = getDashboardByRole(session?.user?.role || '');
        const url = new URL(fallbackRedirectUrl, window.location.origin);
        url.searchParams.delete('status'); // 安全のためにここでも削除
        router.push(url.pathname + url.search);
        console.warn("ログイン結果にリダイレクトURLが含まれていませんでした。フォールバック先に遷移します。");
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError('ログインに失敗しました: ' + errorMessage);
      console.error('Login error:', err);
      setDebugInfo(prev => prev + `\n例外発生: ${errorMessage}`);
    } finally {
      setIsLoading(false);
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
      
      {/* useSessionがloading状態の場合の表示 */}
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
            onClick={() => {
              // 完全なリセット
              if (typeof window !== 'undefined') {
                localStorage.clear();
                sessionStorage.clear();
                // 全てのCookieを削除
                document.cookie.split(";").forEach(c => {
                  const eqPos = c.indexOf("=");
                  const name = eqPos > -1 ? c.substr(0, eqPos).trim() : c.trim();
                  document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
                });
                // ページリロード
                window.location.href = '/login';
              }
            }}
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
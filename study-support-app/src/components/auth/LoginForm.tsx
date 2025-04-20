import { useRouter, useSearchParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import React from 'react';
import { signIn, useSession } from 'next-auth/react';

export const LoginForm: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: session, status } = useSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string>('');

  // セッション状態を監視
  useEffect(() => {
    console.log('セッション状態:', status, session);
    if (status === 'authenticated' && session) {
      console.log('認証済み:', session);
      
      // ユーザーロールに基づいてリダイレクト先を決定
      let redirectUrl = searchParams?.get('redirect') || getDashboardByRole(session.user.role);
      console.log('遷移先:', redirectUrl);
      router.push(redirectUrl);
    }
  }, [session, status, router, searchParams]);
  
  // ユーザーロールに基づいてダッシュボードURLを取得
  const getDashboardByRole = (roles: string[]): string => {
    if (!roles || roles.length === 0) return '/dashboard';
    
    // ロールの優先順位に基づいて遷移先を決定
    if (roles.includes('admin')) {
      return '/admin/dashboard';
    } else if (roles.includes('teacher')) {
      return '/teacher/dashboard';
    } else if (roles.includes('student')) {
      return '/dashboard';
    } else {
      return '/dashboard';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
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
      
      // セッションが確立されるまで待機
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // ここでsessionをチェック - 自動リダイレクトされなかった場合の処理
      if (status !== 'authenticated') {
        // セッションが更新されていない場合は手動でリロード
        router.refresh();
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
      {error && (
        <div className="p-3 rounded bg-red-50 text-red-500 text-sm">
          {error}
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
      
      {/* 簡易ヘルプ - メールとパスワードのヒント */}
      <div className="mt-4 text-xs text-gray-500">
        <p>テストユーザー: test@example.com / password</p>
        <p>管理者ユーザー: admin@example.com / admin123</p>
      </div>
    </form>
  );
}; 
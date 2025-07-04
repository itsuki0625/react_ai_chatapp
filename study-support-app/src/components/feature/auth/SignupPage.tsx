"use client";

import React, { useState, FormEvent, useEffect } from 'react';
import { Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { signIn } from 'next-auth/react';
import { API_BASE_URL } from '@/lib/config';

const SignupPage = () => {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState<string>('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const validatePassword = (password: string): string => {
    if (!password) return '';
    if (password.length < 8) return 'パスワードは8文字以上である必要があります。';
    if (!/(?=.*[a-z])/.test(password)) return 'パスワードには小文字を含める必要があります。';
    if (!/(?=.*[A-Z])/.test(password)) return 'パスワードには大文字を含める必要があります。';
    if (!/(?=.*\d)/.test(password)) return 'パスワードには数字を含める必要があります。';
    return 'strong';
  };

  useEffect(() => {
    const strength = validatePassword(formData.password);
    if (strength === 'strong') {
      setPasswordStrength('');
    } else {
      setPasswordStrength(strength);
    }
  }, [formData.password]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (!agreedToTerms) {
      setError('利用規約とプライバシーポリシーに同意する必要があります。');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('パスワードが一致しません');
      return;
    }

    const strength = validatePassword(formData.password);
    if (strength !== 'strong') {
      setError(strength || 'パスワードが要件を満たしていません。');
      return;
    }

    setIsLoading(true);

    const signupApiUrl = `/api/v1/auth/signup`;
    console.log('>>> [SignupPage] Attempting to fetch signup API:', signupApiUrl);

    try {
      // リクエストの詳細をログ出力
      const requestBody = {
        email: formData.email,
        password: formData.password,
        full_name: formData.name
      };
      
      console.log('Signup request details:', {
        url: signupApiUrl,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: { ...requestBody, password: '[REDACTED]' }, // パスワードは隠す
      });

      const response = await fetch(signupApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Response received:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        url: response.url
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        let errorMessage = 'アカウントの作成に失敗しました。もう一度お試しください。';
        
        // エラーレスポンスの詳細をログ出力
        console.error('Signup API Error:', {
          status: response.status,
          statusText: response.statusText,
          errorData: errorData,
          headers: Object.fromEntries(response.headers.entries()),
          url: response.url
        });
        
        if (typeof errorData?.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData?.detail)) {
          const firstError = errorData.detail[0];
          if (typeof firstError?.msg === 'string') {
            errorMessage = firstError.msg;
          }
        } else if (typeof errorData?.message === 'string') {
          errorMessage = errorData.message;
        }
        
        // 特定のエラーステータスに対するメッセージ
        if (response.status === 463) {
          errorMessage = 'アカウント作成中にエラーが発生しました。少し時間をおいてから再度お試しください。';
        } else if (response.status === 409) {
          errorMessage = 'このメールアドレスは既に登録されています。';
        } else if (response.status >= 500) {
          errorMessage = 'サーバーエラーが発生しました。しばらく時間をおいてから再度お試しください。';
        } else if (response.status === 422) {
          errorMessage = '入力内容に問題があります。すべての項目を正しく入力してください。';
        }
        
        setError(errorMessage);
        return;
      }

      console.log('Signup successful, attempting auto login...');
      
      const signInResult = await signIn('credentials', {
        email: formData.email,
        password: formData.password,
        redirect: false,
        callbackUrl: '/profile/setup'
      });

      if (signInResult?.error) {
        console.log('Auto login failed, redirecting to login page');
        router.push('/login');
        return;
      }

      await new Promise(resolve => setTimeout(resolve, 500));
      router.push('/profile/setup');

    } catch (err) {
      console.error("Signup error:", err);
      if (err instanceof Error) {
        console.error("Error details:", {
          name: err.name,
          message: err.message,
          cause: (err as any).cause
        });
      }
      setError('ネットワークエラーが発生しました。インターネット接続を確認してから再度お試しください。');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">
            アカウント作成
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            すでにアカウントをお持ちの方は
            <a href="/login" className="font-medium text-blue-600 hover:text-blue-500">
              ログイン
            </a>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="p-3 rounded bg-red-50 text-red-500 text-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              お名前
            </label>
            <div className="relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="name"
                name="name"
                type="text"
                autoComplete="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="山田 太郎"
              />
            </div>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              メールアドレス
            </label>
            <div className="relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="example@mail.com"
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              パスワード
            </label>
            <div className="relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                required
                value={formData.password}
                onChange={handleChange}
                className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            {passwordStrength && formData.password && (
              <p className="mt-1 text-xs text-red-600">{passwordStrength}</p>
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
              パスワード（確認）
            </label>
            <div className="relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="••••••••"
              />
            </div>
          </div>

          <div className="flex items-center">
            <input
              id="agree-terms"
              name="agree-terms"
              type="checkbox"
              required
              checked={agreedToTerms}
              onChange={(e) => setAgreedToTerms(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="agree-terms" className="ml-2 block text-sm text-gray-900">
              <a href="https://lp.smartao.jp/terms" target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 hover:text-blue-500">利用規約</a>、
              <a href="https://lp.smartao.jp/privacy-policy" target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 hover:text-blue-500">プライバシーポリシー</a>、
              <a href="https://lp.smartao.jp/tokushoho" target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 hover:text-blue-500">特定商取引法に基づく表記</a>
              に同意します
            </label>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                isLoading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
              } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
            >
              {isLoading ? 'アカウント作成中...' : 'アカウントを作成'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SignupPage;
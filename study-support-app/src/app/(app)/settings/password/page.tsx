"use client";

import React, { useState } from 'react';
import { ArrowLeft, Shield, Eye, EyeOff } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';

const PasswordChangePage = () => {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const validateForm = () => {
    let isValid = true;
    const newErrors = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    };

    if (!formData.currentPassword) {
      newErrors.currentPassword = '現在のパスワードを入力してください';
      isValid = false;
    }

    if (!formData.newPassword) {
      newErrors.newPassword = '新しいパスワードを入力してください';
      isValid = false;
    } else if (formData.newPassword.length < 8) {
      newErrors.newPassword = 'パスワードは8文字以上で入力してください';
      isValid = false;
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '確認用パスワードを入力してください';
      isValid = false;
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = '新しいパスワードと確認用パスワードが一致しません';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // 入力時にエラーをクリア
    if (errors[name as keyof typeof errors]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    if (status !== 'authenticated') {
      toast.error('認証されていません。');
      router.push('/login');
      return;
    }

    setIsLoading(true);
    
    try {
      console.log('パスワード変更リクエスト開始:', {
        hasAccessToken: !!session?.user?.accessToken,
        userEmail: session?.user?.email
      });
      
      await axios.post(`${API_BASE_URL}/api/v1/auth/change-password`, {
        current_password: formData.currentPassword,
        new_password: formData.newPassword
      }, {
        headers: {
          'Authorization': `Bearer ${session?.user?.accessToken || ''}`
        }
      });
      
      toast.success('パスワードを変更しました');
      
      // フォームをリセット
      setFormData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
      
      // 設定ページに戻る
      setTimeout(() => {
        router.push('/settings');
      }, 2000);
      
    } catch (error: any) {
      console.error('パスワード変更エラー:', error);
      console.error('エラー詳細:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers,
        config: error.config
      });
      
      if (error.response?.status === 400) {
        toast.error('現在のパスワードが正しくありません');
        setErrors(prev => ({
          ...prev,
          currentPassword: '現在のパスワードが正しくありません'
        }));
      } else if (error.response?.status === 401) {
        toast.error('認証に失敗しました。再度ログインしてください。');
        router.push('/login');
      } else {
        toast.error('パスワードの変更に失敗しました');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (status === 'unauthenticated') {
    router.push('/login');
    return null;
  }

  if (status === 'loading') {
    return (
      <div className="p-6 max-w-4xl mx-auto text-center">
        <p>読み込み中...</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <Link href="/settings" className="flex items-center text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft className="h-4 w-4 mr-1" />
          設定に戻る
        </Link>
      </div>
      
      <div className="flex items-center mb-6">
        <Shield className="h-5 w-5 text-gray-500 mr-2" />
        <h1 className="text-2xl font-bold text-gray-900">パスワード変更</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>パスワードを変更する</CardTitle>
          <CardDescription>
            セキュリティのため、定期的なパスワード変更をおすすめします
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="currentPassword">現在のパスワード</Label>
              <div className="relative">
                <Input
                  id="currentPassword"
                  name="currentPassword"
                  type={showCurrentPassword ? "text" : "password"}
                  value={formData.currentPassword}
                  onChange={handleChange}
                  className={errors.currentPassword ? "border-red-500" : ""}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                >
                  {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.currentPassword && (
                <p className="text-sm text-red-500">{errors.currentPassword}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="newPassword">新しいパスワード</Label>
              <div className="relative">
                <Input
                  id="newPassword"
                  name="newPassword"
                  type={showNewPassword ? "text" : "password"}
                  value={formData.newPassword}
                  onChange={handleChange}
                  className={errors.newPassword ? "border-red-500" : ""}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                >
                  {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.newPassword && (
                <p className="text-sm text-red-500">{errors.newPassword}</p>
              )}
              <p className="text-xs text-gray-500">パスワードは8文字以上で設定してください</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">新しいパスワード（確認）</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={errors.confirmPassword ? "border-red-500" : ""}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="text-sm text-red-500">{errors.confirmPassword}</p>
              )}
            </div>

            <div className="pt-4">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'パスワード変更中...' : 'パスワードを変更する'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default PasswordChangePage; 
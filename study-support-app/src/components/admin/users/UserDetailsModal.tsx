import React, { useState, useEffect } from 'react';
import { User, UserRole } from '@/types/user';
import { UserCreatePayload, UserUpdatePayload } from '@/services/adminService';

// --- formData の型定義を追加 ---
interface FormDataState {
  email?: string;
  name?: string;
  password?: string;
  role?: 'admin' | 'teacher' | 'student'; // 英語キーを使用
  status?: 'active' | 'inactive' | 'pending' | 'unpaid'; // 'unpaid' を追加
}
// --- ここまで ---

interface UserDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (userData: UserCreatePayload | UserUpdatePayload) => Promise<void>;
  user: User | null;
  mode: 'view' | 'edit' | 'add';
}

const UserDetailsModal: React.FC<UserDetailsModalProps> = ({
  isOpen,
  onClose,
  onSave,
  user,
  mode,
}) => {
  const [formData, setFormData] = useState<FormDataState>({});
  const [isSaving, setIsSaving] = useState(false);

  // 日本語ロール名を英語キーに変換するマップ
  const roleJpToEn: Record<string, 'admin' | 'teacher' | 'student'> = {
    "管理者": 'admin',
    "教員": 'teacher',
    "生徒": 'student',
  };
  // 英語キーを日本語ロール名に変換するマップ (APIへ送信する際に使用)
  const roleEnToJp: Record<'admin' | 'teacher' | 'student', string> = {
    admin: '管理者',
    teacher: '教員',
    student: '生徒',
  };

  useEffect(() => {
    if (mode === 'add') {
      setFormData({
        role: 'student', // デフォルトは英語キー
        status: 'pending',
      });
    } else if (user) {
      // user.role (日本語) を英語キーに変換して設定
      const roleKey = roleJpToEn[user.role] || 'student'; // 見つからない場合は student にフォールバック
      setFormData({
        email: user.email,
        name: user.name,
        role: roleKey, // 英語キーを設定
        status: user.status,
      });
    }
  }, [isOpen, mode, user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      if (!formData.email || !formData.name) {
         alert('メールアドレスと名前は必須です。');
         setIsSaving(false);
         return;
      }
      if (mode === 'add' && !formData.password) {
          alert('新規作成時はパスワードが必須です。');
          setIsSaving(false);
          return;
      }
      // formDataをAPIのスキーマに合わせてマッピング
      const payload: any = {
        email: formData.email!,
        full_name: formData.name!,
        role: roleEnToJp[formData.role as 'admin' | 'teacher' | 'student'] || formData.role,
        status: formData.status!,
      };
      // パスワードは新規作成時または編集時に入力がある場合のみ追加
      if (mode === 'add') {
        payload.password = formData.password!;
      } else if (mode === 'edit' && formData.password) {
        payload.password = formData.password;
      }
      await onSave(payload);
    } catch (error) {
      console.error('保存エラー (Modal):', error);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const isReadonly = mode === 'view';
  const title = mode === 'add' ? '新規ユーザー追加' : mode === 'edit' ? 'ユーザー編集' : 'ユーザー詳細';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">{title}</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">名前</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name || ''}
              onChange={handleChange}
              readOnly={isReadonly}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm disabled:bg-gray-100"
              disabled={isReadonly}
            />
          </div>
          <div className="mb-4">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">メールアドレス</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email || ''}
              onChange={handleChange}
              readOnly={isReadonly}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm disabled:bg-gray-100"
              disabled={isReadonly}
            />
          </div>
          {(mode === 'add' || mode === 'edit') && (
            <div className="mb-4">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                パスワード {mode === 'edit' ? '(変更する場合のみ入力)' : ''}
              </label>
              <input
                type="password"
                id="password"
                name="password"
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                required={mode === 'add'}
              />
            </div>
          )}
          <div className="mb-4">
            <label htmlFor="role" className="block text-sm font-medium text-gray-700">ロール</label>
            <select
              id="role"
              name="role"
              value={formData.role || ''}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm disabled:bg-gray-100"
              disabled={isReadonly}
            >
              <option value="student">生徒</option>
              <option value="teacher">先生</option>
              <option value="admin">管理者</option>
            </select>
          </div>
           <div className="mb-4">
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">ステータス</label>
            <select
              id="status"
              name="status"
              value={formData.status || ''}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm disabled:bg-gray-100"
              disabled={isReadonly}
            >
              <option value="active">アクティブ</option>
              <option value="inactive">非アクティブ</option>
              <option value="pending">保留中</option>
              <option value="unpaid">未決済</option>
            </select>
          </div>
          {mode === 'view' && user && (
            <>
             <div className="mb-2">
                <span className="text-sm font-medium text-gray-500">作成日時: </span>
                <span className="text-sm text-gray-900">{new Date(user.createdAt).toLocaleString()}</span>
              </div>
              <div className="mb-4">
                <span className="text-sm font-medium text-gray-500">最終ログイン: </span>
                <span className="text-sm text-gray-900">{user.lastLogin ? new Date(user.lastLogin).toLocaleString() : '-'}</span>
              </div>
            </>
          )}
          <div className="flex justify-end space-x-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
            >
              閉じる
            </button>
            {!isReadonly && (
              <button
                type="submit"
                disabled={isSaving}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isSaving ? '保存中...' : (mode === 'add' ? '作成' : '更新')}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserDetailsModal; 
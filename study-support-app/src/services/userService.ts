import { UserSettings } from '../types/user'; // UserSettings 型をインポート (必要に応じてパスを調整)
import { User } from '@/types/user'; // User 型をインポート
import { apiClient } from '@/lib/api';

/**
 * ユーザー設定を取得します。
 * @returns {Promise<UserSettings>} ユーザー設定情報
 */
export const fetchUserSettings = async (): Promise<UserSettings> => {
  try {
    const response = await apiClient.get<UserSettings>('/api/v1/auth/user-settings');
    return response.data as UserSettings;
  } catch (error) {
    console.error('ユーザー設定の取得に失敗しました:', error);
    throw error; // エラーを再スローするか、適切なエラーハンドリングを行う
  }
};

/**
 * ユーザー設定を更新します。
 * @param {Partial<UserSettings>} settings 更新する設定項目
 * @returns {Promise<UserSettings>} 更新後のユーザー設定情報
 */
export const updateUserSettings = async (settings: Partial<UserSettings>): Promise<UserSettings> => {
  try {
    const response = await apiClient.put<UserSettings>('/api/v1/auth/user-settings', settings);
    return response.data;
  } catch (error) {
    console.error('ユーザー設定の更新に失敗しました:', error);
    throw error; // エラーを再スローするか、適切なエラーハンドリングを行う
  }
};

// アイコンアップロード
export const uploadUserIcon = async (file: File): Promise<User> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post('/api/v1/users/me/icon', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('アイコンアップロードに失敗しました:', error);
    throw error;
  }
};

// アイコン削除
export const deleteUserIcon = async (): Promise<User> => {
  try {
    const response = await apiClient.delete('/api/v1/users/me/icon');
    return response.data;
  } catch (error) {
    console.error('アイコン削除に失敗しました:', error);
    throw error;
  }
}; 
import axios from 'axios'; // axios をインポート
import { getApiBaseUrl, getAxiosConfig } from './api'; // 設定関数をインポート
import { UserSettings } from '../types/user'; // UserSettings 型をインポート (必要に応じてパスを調整)

/**
 * ユーザー設定を取得します。
 * @returns {Promise<UserSettings>} ユーザー設定情報
 */
export const fetchUserSettings = async (): Promise<UserSettings> => {
  try {
    const url = `${getApiBaseUrl()}/api/v1/auth/user-settings`; // APIのベースURLを取得
    const config = await getAxiosConfig(); // axios の設定を取得 (await を追加)
    const response = await axios.get<UserSettings>(url, config); // axios を直接使用
    // Explicitly assert the type of response.data
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
    const url = `${getApiBaseUrl()}/api/v1/auth/user-settings`; // APIのベースURLを取得
    const config = await getAxiosConfig(); // axios の設定を取得 (await を追加)
    // Ensure the method matches the backend endpoint (likely PUT or PATCH)
    // The backend auth.py uses PUT for /user-settings
    const response = await axios.put<UserSettings>(url, settings, config); // Change to PUT
    return response.data;
  } catch (error) {
    console.error('ユーザー設定の更新に失敗しました:', error);
    throw error; // エラーを再スローするか、適切なエラーハンドリングを行う
  }
}; 
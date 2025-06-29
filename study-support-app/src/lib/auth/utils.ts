import { jwtDecode } from 'jwt-decode';
import { DecodedToken } from './types';

/**
 * ロールを正規化する関数
 */
export const normalizeRole = (roleInput: string | string[] | undefined): string => {
  if (Array.isArray(roleInput) && roleInput.length > 0) {
    return roleInput[0]; // 配列の場合、最初の要素を返す
  }
  if (typeof roleInput === 'string') {
    return roleInput;
  }
  return '不明';
};

/**
 * ユーザーの権限を判定する関数
 */
export const getUserPermissions = (role: string) => {
  const isAdmin = role === '管理者';
  const isTeacher = role === '教員';
  const isStudent = !isAdmin && !isTeacher;

  return {
    isAdmin,
    isTeacher,
    isStudent,
  };
};

/**
 * JWTトークンをデコードして情報を取得する
 */
export const decodeAuthToken = (token: string): {
  roles?: string[];
  permissions?: string[];
  decodedToken: DecodedToken;
} => {
  try {
    const decodedToken = jwtDecode<DecodedToken>(token);
    return {
      roles: decodedToken.roles,
      permissions: decodedToken.permissions,
      decodedToken,
    };
  } catch (error) {
    console.error('Failed to decode token:', error);
    return {
      decodedToken: {},
    };
  }
};

/**
 * トークンの有効期限をチェックする
 */
export const isTokenExpired = (
  accessTokenExpires: number | undefined,
  safetyMarginSeconds: number = 60
): boolean => {
  if (!accessTokenExpires) return true;
  
  const currentTime = Date.now();
  const expirationTime = accessTokenExpires * 1000 - safetyMarginSeconds * 1000;
  
  return currentTime >= expirationTime;
};

/**
 * エラーの種類を判定する
 */
export const getErrorType = (error: any): string => {
  if (error.name === 'AbortError') {
    return 'Request timeout';
  }
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    return 'Network connection error';
  }
  return error.message || 'Unknown error';
};

/**
 * 認証ヘッダーを生成する
 */
export const createAuthHeaders = (contentType: string = 'application/json') => ({
  'Content-Type': contentType,
  'Accept': 'application/json',
});

/**
 * フォームデータを作成する
 */
export const createFormData = (email: string, password: string): URLSearchParams => {
  const body = new URLSearchParams();
  body.append('username', email);
  body.append('password', password);
  return body;
}; 
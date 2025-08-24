/**
 * 学校テナント機能の設定管理
 */

export interface TenantConfig {
  // API設定
  apiBaseUrl: string;
  useMockData: boolean;
  mockDataFallback: boolean;
  
  // 認証設定
  requireAuthentication: boolean;
  
  // 機能フラグ
  enableSchoolAdmin: boolean;
  enableTeacherFeatures: boolean;
  enableAnalytics: boolean;
  
  // UI設定
  defaultPageSize: number;
  maxStudentsPerTeacher: number;
  
  // キャッシュ設定
  cacheTimeout: number;
  enableCaching: boolean;
}

/**
 * 環境別設定
 */
const environments = {
  development: {
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5050/api/v1',
    useMockData: process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true' || true,
    mockDataFallback: true,
    requireAuthentication: process.env.NODE_ENV === 'production',
    enableSchoolAdmin: true,
    enableTeacherFeatures: true,
    enableAnalytics: true,
    defaultPageSize: 20,
    maxStudentsPerTeacher: 50,
    cacheTimeout: 5 * 60 * 1000, // 5分
    enableCaching: false,
  },
  
  staging: {
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'https://stg-api.smartao.jp/api/v1',
    useMockData: process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true' || false,
    mockDataFallback: true,
    requireAuthentication: true,
    enableSchoolAdmin: true,
    enableTeacherFeatures: true,
    enableAnalytics: true,
    defaultPageSize: 20,
    maxStudentsPerTeacher: 50,
    cacheTimeout: 10 * 60 * 1000, // 10分
    enableCaching: true,
  },
  
  production: {
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.smartao.jp/api/v1',
    useMockData: false,
    mockDataFallback: true, // 緊急時のフォールバック
    requireAuthentication: true,
    enableSchoolAdmin: true,
    enableTeacherFeatures: true,
    enableAnalytics: true,
    defaultPageSize: 20,
    maxStudentsPerTeacher: 100,
    cacheTimeout: 15 * 60 * 1000, // 15分
    enableCaching: true,
  }
};

/**
 * 現在の環境設定を取得
 */
function getEnvironment(): keyof typeof environments {
  const env = process.env.NODE_ENV as keyof typeof environments;
  return environments[env] ? env : 'development';
}

/**
 * テナント設定を取得
 */
export function getTenantConfig(): TenantConfig {
  const env = getEnvironment();
  const config = environments[env];
  
  // 環境変数による上書き
  return {
    ...config,
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || config.apiBaseUrl,
    useMockData: process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true' || config.useMockData,
    enableSchoolAdmin: process.env.NEXT_PUBLIC_ENABLE_SCHOOL_ADMIN !== 'false' && config.enableSchoolAdmin,
    enableTeacherFeatures: process.env.NEXT_PUBLIC_ENABLE_TEACHER_FEATURES !== 'false' && config.enableTeacherFeatures,
    enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS !== 'false' && config.enableAnalytics,
  };
}

/**
 * 機能フラグチェック
 */
export function isFeatureEnabled(feature: keyof Pick<TenantConfig, 'enableSchoolAdmin' | 'enableTeacherFeatures' | 'enableAnalytics'>): boolean {
  const config = getTenantConfig();
  return config[feature];
}

/**
 * デバッグモードチェック
 */
export function isDebugMode(): boolean {
  return process.env.NODE_ENV === 'development' || 
         process.env.NEXT_PUBLIC_DEBUG === 'true';
}

/**
 * Mock データ使用判定
 */
export function shouldUseMockData(): boolean {
  const config = getTenantConfig();
  
  // 開発環境では環境変数またはデフォルトでMock使用
  if (process.env.NODE_ENV === 'development') {
    return process.env.NEXT_PUBLIC_USE_MOCK_DATA !== 'false';
  }
  
  // 本番環境では明示的に有効にした場合のみ
  return config.useMockData;
}

/**
 * API エラー時のフォールバック判定
 */
export function shouldFallbackToMock(): boolean {
  const config = getTenantConfig();
  return config.mockDataFallback && isDebugMode();
}

// エクスポート
export const tenantConfig = getTenantConfig();

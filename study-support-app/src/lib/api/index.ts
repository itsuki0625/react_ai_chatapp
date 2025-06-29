// API統合エクスポートファイル
// すべてのAPIクライアントと関数をここから利用可能

// 基本APIクライアント
export { apiClient, default as defaultApiClient } from './client';

// 型定義
export * from './types';

// API関数群
export { chatApi } from './endpoints/chat';
export { applicationApi, statementApi } from './endpoints/application';
export { contentAPI } from './endpoints/content';

// 下位互換性のため、元のapi-clientからのインポート形式も提供
// これにより段階的な移行が可能
export {
  // 基本クライアント
  apiClient as legacyApiClient,
} from './client';

// 一時的に元のapi-client.tsからもエクスポート（移行期間中）
// TODO: 移行完了後に削除
export {
  dashboardApi,
  universityApi,
  admissionApi,
  contentApi,
  studyPlanApi,
  quizApi,
  authApi,
  adminNotificationSettingsApi,
} from '../api-client'; 
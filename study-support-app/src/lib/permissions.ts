// 権限名の定数
export const PERMISSIONS = {
  // チャット関連
  CHAT_SESSION_READ: 'chat_session_read',
  CHAT_MESSAGE_SEND: 'chat_message_send',
  
  // ステートメント関連
  STATEMENT_REVIEW_REQUEST: 'statement_review_request',
  STATEMENT_MANAGE_OWN: 'statement_manage_own',
  
  // コンテンツ関連
  CONTENT_READ: 'content_read',
  CONTENT_MANAGE: 'content_manage',
  
  // FAQ関連
  FAQ_READ: 'faq_read',
  
  // 申請関連
  APPLICATION_CREATE: 'application_create',
  APPLICATION_MANAGE_OWN: 'application_manage_own',
  
  // 管理者権限
  ADMIN_ALL: 'admin_all',
} as const;

// 各ルートに必要な権限のマッピング
export const ROUTE_PERMISSIONS: Record<string, string[]> = {
  // チャット関連
  '/student/chat': [PERMISSIONS.CHAT_SESSION_READ],
  '/student/chat/admission': [PERMISSIONS.CHAT_SESSION_READ],
  '/student/chat/self-analysis': [PERMISSIONS.CHAT_SESSION_READ],
  '/student/chat/study-support': [PERMISSIONS.CHAT_SESSION_READ],
  '/student/chat/faq': [PERMISSIONS.FAQ_READ],
  
  // ステートメント関連
  '/student/statement': [PERMISSIONS.STATEMENT_MANAGE_OWN],
  
  // コンテンツ関連
  '/student/contents': [PERMISSIONS.CONTENT_READ],
  
  // 申請関連
  '/student/application': [PERMISSIONS.APPLICATION_MANAGE_OWN],
} as const;

/**
 * 指定されたルートに対してユーザーが必要な権限を持っているかチェック
 * @param pathname - チェックするルート
 * @param userPermissions - ユーザーの権限リスト
 * @param isAdmin - 管理者かどうか
 * @param isTeacher - 教師かどうか
 * @returns 権限があるかどうか
 */
export function hasRoutePermission(
  pathname: string,
  userPermissions: string[],
  isAdmin: boolean = false,
  isTeacher: boolean = false
): boolean {
  // 管理者は全ての権限を持つ
  if (isAdmin) {
    return true;
  }
  
  // 教師は学生向けコンテンツにアクセス可能
  if (isTeacher) {
    return true;
  }
  
  // 該当するルート権限を見つける
  const matchingRoute = Object.keys(ROUTE_PERMISSIONS).find(route => 
    pathname.startsWith(route)
  );
  
  if (!matchingRoute) {
    // 権限設定がないルートは基本的にアクセス可能
    return true;
  }
  
  const requiredPermissions = ROUTE_PERMISSIONS[matchingRoute];
  
  // 必要な権限のいずれかを持っているかチェック
  return requiredPermissions.some(permission => 
    userPermissions.includes(permission)
  );
}

/**
 * 権限不足時のリダイレクト先を決定
 * @param pathname - 現在のルート
 * @param userStatus - ユーザーのステータス
 * @returns リダイレクト先URL
 */
export function getPermissionRedirectUrl(pathname: string, userStatus: string): string {
  // ステータスが非アクティブの場合は課金ページへ
  if (userStatus !== 'active') {
    return '/student/subscription/plans';
  }
  
  // 権限不足の場合はダッシュボードへ
  return '/student/dashboard';
} 
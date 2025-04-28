'use client'; // Client Component としてマーク

import { useSession } from 'next-auth/react';
import { UserRole } from '@/types/user'; // user.ts から UserRole 型をインポート

/**
 * 認証状態とユーザーロール/権限に関する情報を提供するカスタムフック
 * @returns {object} - 認証セッション、ロード状態、認証済みフラグ、ユーザーロール、管理者フラグ、権限チェック関数を含むオブジェクト
 */
export function useAuthHelpers() {
  const { data: session, status } = useSession();

  // セッション情報のロード状態
  const isLoading = status === 'loading';
  // 認証済みかどうか
  const isAuthenticated = status === 'authenticated';

  // セッションからユーザーロールを取得
  const userRole = session?.user?.role as UserRole | undefined;

  // 管理者かどうかを判定
  const isAdmin = !isLoading && isAuthenticated && userRole === '管理者';

  // ★ セッションから権限リストを取得
  const permissions = session?.user?.permissions ?? [];

  // ★ 指定された権限を持っているかチェックする関数
  const hasPermission = (permissionName: string): boolean => {
    // ローディング中または未認証の場合は権限なし
    if (isLoading || !isAuthenticated) return false;
    // 管理者は全ての権限を持つ
    if (isAdmin) return true;
    // 権限リストに含まれているかチェック
    return permissions.includes(permissionName);
  };

  return {
    session,
    status, // 'loading', 'authenticated', 'unauthenticated'
    isLoading,
    isAuthenticated,
    userRole,
    isAdmin,
    permissions, // ★ 権限リストも返すようにする (デバッグや高度な制御用)
    hasPermission, // ★ 権限チェック関数を追加
  };
} 
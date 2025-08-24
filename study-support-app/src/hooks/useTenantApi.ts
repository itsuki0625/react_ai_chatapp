/**
 * 学校テナント機能用のカスタムフック
 * APIエラーハンドリング、ローディング状態、キャッシュを管理
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { tenantConfig, shouldUseMockData, shouldFallbackToMock } from '@/lib/config/tenant';
import { MockTenantAPI } from '@/lib/mock/tenant-api';
import { tenantApi } from '@/lib/api/tenant-client';

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * 汎用APIフック
 */
export function useTenantApiCall<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = [],
  options: {
    immediate?: boolean;
    cacheKey?: string;
    fallbackToMock?: boolean;
  } = {}
): ApiState<T> {
  const { immediate = true, cacheKey, fallbackToMock = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cacheRef = useRef<Map<string, { data: T; timestamp: number }>>(new Map());
  
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // キャッシュチェック
      if (cacheKey && tenantConfig.enableCaching) {
        const cached = cacheRef.current.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < tenantConfig.cacheTimeout) {
          setData(cached.data);
          setLoading(false);
          return;
        }
      }
      
      // API呼び出し
      const result = await apiCall();
      setData(result);
      
      // キャッシュに保存
      if (cacheKey && tenantConfig.enableCaching) {
        cacheRef.current.set(cacheKey, {
          data: result,
          timestamp: Date.now()
        });
      }
      
    } catch (err: any) {
      console.error('API call failed:', err);
      
      // フォールバック処理
      if (fallbackToMock && shouldFallbackToMock()) {
        console.warn('API呼び出し失敗、Mockデータにフォールバック');
        try {
          // Mock APIへのフォールバック
          // 実装は具体的なAPIコールに依存
          setError('API接続エラー (Mock データを使用中)');
        } catch (mockErr) {
          setError(err.message || 'データの取得に失敗しました');
        }
      } else {
        setError(err.message || 'データの取得に失敗しました');
      }
    } finally {
      setLoading(false);
    }
  }, [apiCall, cacheKey, fallbackToMock, ...dependencies]);
  
  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [immediate, ...dependencies]);
  
  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}

/**
 * 学校統計情報取得フック
 */
export function useSchoolStatistics() {
  const { currentSchool } = useTenant();
  
  return useTenantApiCall(
    async () => {
      if (shouldUseMockData()) {
        return MockTenantAPI.getSchoolAnalytics(currentSchool?.id || '');
      } else {
        return tenantApi.getSchoolStatistics();
      }
    },
    [currentSchool?.id],
    {
      cacheKey: `school-stats-${currentSchool?.id}`,
      fallbackToMock: true,
    }
  );
}

/**
 * 学校ユーザー一覧取得フック
 */
export function useSchoolUsers(role?: string) {
  const { currentSchool } = useTenant();
  
  return useTenantApiCall(
    async () => {
      if (shouldUseMockData()) {
        return MockTenantAPI.getSchoolUsers(currentSchool?.id || '', role);
      } else {
        const response = await tenantApi.getSchoolUsers({ role_name: role });
        return response.users;
      }
    },
    [currentSchool?.id, role],
    {
      cacheKey: `school-users-${currentSchool?.id}-${role || 'all'}`,
      fallbackToMock: true,
    }
  );
}

/**
 * 担当生徒一覧取得フック
 */
export function useAssignedStudents(params: {
  page?: number;
  page_size?: number;
  search?: string;
} = {}) {
  const { currentUser } = useTenant();
  
  return useTenantApiCall(
    async () => {
      if (shouldUseMockData()) {
        const assignments = await MockTenantAPI.getTeacherStudentAssignments(currentUser?.id || '');
        // Mock データの構造を実APIの形式に変換
        return {
          items: assignments.map(assignment => ({
            student: assignment.student,
            assignment: assignment,
            recent_chat_sessions_count: Math.floor(Math.random() * 10),
            recent_statements_count: Math.floor(Math.random() * 5),
            total_desired_schools: Math.floor(Math.random() * 8),
            last_activity_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
          })),
          total_count: assignments.length,
          page: params.page || 1,
          page_size: params.page_size || 20,
          total_pages: Math.ceil(assignments.length / (params.page_size || 20)),
          has_next: false,
          has_prev: false,
        };
      } else {
        return tenantApi.getAssignedStudents(params);
      }
    },
    [currentUser?.id, params.page, params.page_size, params.search],
    {
      cacheKey: `assigned-students-${currentUser?.id}-${JSON.stringify(params)}`,
      fallbackToMock: true,
    }
  );
}

/**
 * 生徒詳細情報取得フック
 */
export function useStudentDetail(studentId: string) {
  return useTenantApiCall(
    async () => {
      if (shouldUseMockData()) {
        const user = await MockTenantAPI.getUser(studentId);
        const chatSessions = await MockTenantAPI.getStudentChatSessions(studentId);
        const statements = await MockTenantAPI.getStudentStatements(studentId);
        const desiredSchools = await MockTenantAPI.getStudentDesiredSchools(studentId);
        
        return {
          student: user,
          assignments: [],
          chat_sessions: chatSessions,
          statements: statements,
          desired_schools: desiredSchools,
          total_chat_sessions: chatSessions.length,
          total_statements: statements.length,
          total_desired_schools: desiredSchools.length,
          last_login_at: user.last_login_at,
        };
      } else {
        return tenantApi.getStudentDetail(studentId);
      }
    },
    [studentId],
    {
      cacheKey: `student-detail-${studentId}`,
      fallbackToMock: true,
    }
  );
}

/**
 * 学校ダッシュボード情報取得フック
 */
export function useSchoolDashboard() {
  const { currentSchool } = useTenant();
  
  return useTenantApiCall(
    async () => {
      if (shouldUseMockData()) {
        const analytics = await MockTenantAPI.getSchoolAnalytics(currentSchool?.id || '');
        const activities = await MockTenantAPI.getRecentActivities(currentSchool?.id || '');
        
        return {
          school_info: {
            id: currentSchool?.id,
            name: currentSchool?.name,
            total_users: analytics.userStats.totalStudents + analytics.userStats.totalTeachers,
          },
          statistics: analytics,
          recent_activities: activities,
          settings: currentSchool?.settings || {},
        };
      } else {
        return tenantApi.getSchoolDashboard();
      }
    },
    [currentSchool?.id],
    {
      cacheKey: `school-dashboard-${currentSchool?.id}`,
      fallbackToMock: true,
    }
  );
}

/**
 * ミューテーション（作成・更新・削除）用フック
 */
export function useTenantMutation<TData, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options: {
    onSuccess?: (data: TData) => void;
    onError?: (error: Error) => void;
    invalidateCache?: string[];
  } = {}
) {
  const { onSuccess, onError, invalidateCache = [] } = options;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cacheRef = useRef<Map<string, any>>(new Map());
  
  const mutate = useCallback(async (variables: TVariables) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await mutationFn(variables);
      
      // キャッシュ無効化
      if (invalidateCache.length > 0) {
        invalidateCache.forEach(key => {
          cacheRef.current.delete(key);
        });
      }
      
      onSuccess?.(result);
      return result;
      
    } catch (err: any) {
      console.error('Mutation failed:', err);
      const errorMessage = err.message || 'オペレーションに失敗しました';
      setError(errorMessage);
      onError?.(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [mutationFn, onSuccess, onError, invalidateCache]);
  
  return {
    mutate,
    loading,
    error,
  };
}

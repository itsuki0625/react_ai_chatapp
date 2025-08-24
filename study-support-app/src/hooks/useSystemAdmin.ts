/**
 * システム管理者用カスタムフック
 * 全学校の管理機能を提供
 */

import { useState, useEffect, useCallback } from 'react';
import { systemAdminApi, SystemSchool, SystemOverview } from '@/lib/api/system-admin-client';

export interface UseSystemAdminState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * 全学校一覧取得フック
 */
export function useSystemSchools(params: {
  search?: string;
  active_only?: boolean;
  auto_fetch?: boolean;
} = {}) {
  const { search, active_only = true, auto_fetch = true } = params;
  const [state, setState] = useState<UseSystemAdminState<SystemSchool[]>>({
    data: null,
    loading: false,
    error: null,
    refetch: async () => {}
  });

  const fetchSchools = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const schools = await systemAdminApi.getAllSchools({
        search,
        active_only,
        limit: 100
      });
      
      setState(prev => ({ 
        ...prev, 
        data: schools, 
        loading: false 
      }));
      
    } catch (err: any) {
      setState(prev => ({ 
        ...prev, 
        error: err.message || 'データの取得に失敗しました', 
        loading: false 
      }));
    }
  }, [search, active_only]);

  useEffect(() => {
    if (auto_fetch) {
      fetchSchools();
    }
  }, [auto_fetch, fetchSchools]);

  return {
    ...state,
    refetch: fetchSchools
  };
}

/**
 * システム統計概要取得フック
 */
export function useSystemOverview(auto_fetch = true) {
  const [state, setState] = useState<UseSystemAdminState<SystemOverview>>({
    data: null,
    loading: false,
    error: null,
    refetch: async () => {}
  });

  const fetchOverview = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const overview = await systemAdminApi.getSystemAnalyticsOverview();
      
      setState(prev => ({ 
        ...prev, 
        data: overview, 
        loading: false 
      }));
      
    } catch (err: any) {
      setState(prev => ({ 
        ...prev, 
        error: err.message || '統計データの取得に失敗しました', 
        loading: false 
      }));
    }
  }, []);

  useEffect(() => {
    if (auto_fetch) {
      fetchOverview();
    }
  }, [auto_fetch, fetchOverview]);

  return {
    ...state,
    refetch: fetchOverview
  };
}

/**
 * 学校詳細情報取得フック
 */
export function useSchoolDetail(schoolId: string | null, auto_fetch = true) {
  const [state, setState] = useState<UseSystemAdminState<SystemSchool>>({
    data: null,
    loading: false,
    error: null,
    refetch: async () => {}
  });

  const fetchSchoolDetail = useCallback(async () => {
    if (!schoolId) return;
    
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const school = await systemAdminApi.getSchoolDetail(schoolId);
      
      setState(prev => ({ 
        ...prev, 
        data: school, 
        loading: false 
      }));
      
    } catch (err: any) {
      setState(prev => ({ 
        ...prev, 
        error: err.message || '学校情報の取得に失敗しました', 
        loading: false 
      }));
    }
  }, [schoolId]);

  useEffect(() => {
    if (auto_fetch && schoolId) {
      fetchSchoolDetail();
    }
  }, [auto_fetch, schoolId, fetchSchoolDetail]);

  return {
    ...state,
    refetch: fetchSchoolDetail
  };
}

/**
 * 学校ステータス変更フック
 */
export function useSchoolStatusToggle() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleStatus = useCallback(async (schoolId: string, isActive: boolean) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await systemAdminApi.updateSchoolStatus(schoolId, !isActive);
      
      setLoading(false);
      return result;
      
    } catch (err: any) {
      setError(err.message || 'ステータスの更新に失敗しました');
      setLoading(false);
      throw err;
    }
  }, []);

  return {
    toggleStatus,
    loading,
    error
  };
}

/**
 * システム管理者用ミューテーションフック
 */
export function useSystemAdminMutation<TData, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: Error, variables: TVariables) => void;
    onSettled?: (data: TData | undefined, error: Error | null, variables: TVariables) => void;
  } = {}
) {
  const { onSuccess, onError, onSettled } = options;
  
  const [state, setState] = useState({
    loading: false,
    error: null as string | null,
    data: undefined as TData | undefined
  });

  const mutate = useCallback(async (variables: TVariables) => {
    try {
      setState({ loading: true, error: null, data: undefined });
      
      const data = await mutationFn(variables);
      
      setState({ loading: false, error: null, data });
      
      onSuccess?.(data, variables);
      onSettled?.(data, null, variables);
      
      return data;
      
    } catch (err: any) {
      const error = new Error(err.message || 'オペレーションに失敗しました');
      
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error.message 
      }));
      
      onError?.(error, variables);
      onSettled?.(undefined, error, variables);
      
      throw error;
    }
  }, [mutationFn, onSuccess, onError, onSettled]);

  return {
    mutate,
    ...state
  };
}

/**
 * 学校作成フック
 */
export function useCreateSchool(options: {
  onSuccess?: (school: SystemSchool) => void;
  onError?: (error: Error) => void;
} = {}) {
  return useSystemAdminMutation(
    async (schoolData: Parameters<typeof systemAdminApi.createSchool>[0]) => {
      return await systemAdminApi.createSchool(schoolData);
    },
    options
  );
}

/**
 * 学校更新フック
 */
export function useUpdateSchool(options: {
  onSuccess?: (school: SystemSchool) => void;
  onError?: (error: Error) => void;
} = {}) {
  return useSystemAdminMutation(
    async (params: { schoolId: string; schoolData: Parameters<typeof systemAdminApi.updateSchool>[1] }) => {
      return await systemAdminApi.updateSchool(params.schoolId, params.schoolData);
    },
    options
  );
}

/**
 * 学校削除フック
 */
export function useDeleteSchool(options: {
  onSuccess?: (result: { success: boolean; message: string }) => void;
  onError?: (error: Error) => void;
} = {}) {
  return useSystemAdminMutation(
    async (schoolId: string) => {
      return await systemAdminApi.deleteSchool(schoolId);
    },
    options
  );
}

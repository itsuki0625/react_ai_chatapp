/**
 * システム管理者用APIクライアント
 * 全学校を横断した管理機能を提供
 */

import { apiClient } from './client';

export interface SystemSchool {
  id: string;
  name: string;
  school_code: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  details: {
    address: string;
    prefecture: string;
    city: string;
    principal_name: string;
  } | null;
  statistics: {
    users: Record<string, number>;
    total_users: number;
    assignments: {
      total: number;
      active: number;
    };
  };
  settings: {
    allow_student_chat: boolean;
    enable_analytics: boolean;
  } | null;
}

export interface SystemOverview {
  schools: {
    total: number;
    active: number;
    inactive: number;
  };
  users: {
    total: number;
    by_role: Record<string, number>;
    active_this_month: number;
  };
  assignments: {
    total: number;
    active: number;
    inactive: number;
  };
  generated_at: string;
}

export interface SchoolUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  last_login_at: string | null;
  roles: string[];
}

export class SystemAdminApiClient {
  
  /**
   * 全学校一覧を取得
   */
  async getAllSchools(params: {
    skip?: number;
    limit?: number;
    search?: string;
    active_only?: boolean;
  } = {}): Promise<SystemSchool[]> {
    const response = await apiClient.get('/api/v1/admin/tenant/schools', { params });
    return response.data;
  }
  
  /**
   * 学校詳細情報を取得
   */
  async getSchoolDetail(schoolId: string): Promise<SystemSchool> {
    const response = await apiClient.get(`/api/v1/admin/tenant/schools/${schoolId}`);
    return response.data;
  }
  
  /**
   * 学校のユーザー一覧を取得
   */
  async getSchoolUsers(schoolId: string, params: {
    role?: string;
    limit?: number;
  } = {}): Promise<SchoolUser[]> {
    const response = await apiClient.get(`/api/v1/admin/tenant/schools/${schoolId}/users`, { params });
    return response.data;
  }
  
  /**
   * システム全体の統計概要を取得
   */
  async getSystemAnalyticsOverview(): Promise<SystemOverview> {
    const response = await apiClient.get('/api/v1/admin/tenant/analytics/overview');
    return response.data;
  }
  
  /**
   * 学校の有効/無効状態を変更
   */
  async updateSchoolStatus(schoolId: string, isActive: boolean): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.put(`/api/v1/admin/tenant/schools/${schoolId}/status`, isActive);
    return response.data;
  }
  
  /**
   * 新規学校を作成
   */
  async createSchool(schoolData: {
    name: string;
    school_code: string;
    details?: {
      address?: string;
      prefecture?: string;
      city?: string;
      zip_code?: string;
      principal_name?: string;
      website_url?: string;
    };
    settings?: {
      allow_student_chat?: boolean;
      require_statement_approval?: boolean;
      enable_analytics?: boolean;
      enable_teacher_student_assignment?: boolean;
    };
  }): Promise<SystemSchool> {
    const response = await apiClient.post('/api/v1/admin/tenant/schools', schoolData);
    return response.data;
  }
  
  /**
   * 学校情報を更新
   */
  async updateSchool(schoolId: string, schoolData: {
    name?: string;
    school_code?: string;
    details?: {
      address?: string;
      prefecture?: string;
      city?: string;
      zip_code?: string;
      principal_name?: string;
      website_url?: string;
    };
    settings?: {
      allow_student_chat?: boolean;
      require_statement_approval?: boolean;
      enable_analytics?: boolean;
      enable_teacher_student_assignment?: boolean;
    };
  }): Promise<SystemSchool> {
    const response = await apiClient.put(`/api/v1/admin/tenant/schools/${schoolId}`, schoolData);
    return response.data;
  }
  
  /**
   * 学校を削除
   */
  async deleteSchool(schoolId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.delete(`/api/v1/admin/tenant/schools/${schoolId}`);
    return response.data;
  }
  
  /**
   * 学校管理者を追加
   */
  async addSchoolAdmin(schoolId: string, adminData: {
    email: string;
    full_name: string;
    password?: string;
    send_invitation?: boolean;
  }): Promise<SchoolUser> {
    const response = await apiClient.post(`/api/v1/admin/tenant/schools/${schoolId}/admins`, adminData);
    return response.data;
  }
  
  /**
   * 学校管理者を削除
   */
  async removeSchoolAdmin(schoolId: string, adminId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.delete(`/api/v1/admin/tenant/schools/${schoolId}/admins/${adminId}`);
    return response.data;
  }
  
  /**
   * 学校間データ比較レポートを取得
   */
  async getSchoolComparisonReport(schoolIds: string[]): Promise<{
    schools: SystemSchool[];
    comparison: {
      user_growth: Record<string, number[]>;
      activity_comparison: Record<string, any>;
      performance_metrics: Record<string, any>;
    };
    generated_at: string;
  }> {
    const response = await apiClient.post('/api/v1/admin/tenant/analytics/comparison', { school_ids: schoolIds });
    return response.data;
  }
  
  /**
   * システム全体のヘルスチェック
   */
  async getSystemHealthCheck(): Promise<{
    overall_status: 'healthy' | 'warning' | 'critical';
    checks: Array<{
      name: string;
      status: 'pass' | 'warning' | 'fail';
      message: string;
      details?: any;
    }>;
    generated_at: string;
  }> {
    const response = await apiClient.get('/api/v1/admin/tenant/health-check');
    return response.data;
  }
  
  /**
   * テナント間データ移行
   */
  async migrateSchoolData(sourceSchoolId: string, targetSchoolId: string, options: {
    migrate_users: boolean;
    migrate_assignments: boolean;
    migrate_settings: boolean;
    dry_run: boolean;
  }): Promise<{
    success: boolean;
    message: string;
    migrated_count: Record<string, number>;
    errors: string[];
  }> {
    const response = await apiClient.post(`/api/v1/admin/tenant/schools/${sourceSchoolId}/migrate`, {
      target_school_id: targetSchoolId,
      ...options
    });
    return response.data;
  }
}

// シングルトンインスタンス
export const systemAdminApi = new SystemAdminApiClient();

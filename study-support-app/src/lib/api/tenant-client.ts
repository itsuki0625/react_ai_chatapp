/**
 * 学校テナント機能用のAPIクライアント
 * MockAPIから実APIへの切り替えに対応
 */

import { apiClient } from './client';
import { 
  School, 
  SchoolUser, 
  SchoolStats,
  TeacherStudentAssignment,
  StudentChatSession,
  StudentStatement,
  StudentDesiredSchool,
  Activity,
  AnalyticsData,
  SchoolSettings
} from '@/types/tenant';

export class TenantApiClient {
  
  /**
   * GETリクエスト
   */
  async get<T>(url: string, config?: any): Promise<T> {
    const response = await apiClient.get(url, config);
    return response.data;
  }
  
  /**
   * POSTリクエスト
   */
  async post<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await apiClient.post(url, data, config);
    return response.data;
  }
  
  /**
   * PUTリクエスト
   */
  async put<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await apiClient.put(url, data, config);
    return response.data;
  }
  
  /**
   * DELETEリクエスト
   */
  async delete<T>(url: string, config?: any): Promise<T> {
    const response = await apiClient.delete(url, config);
    return response.data;
  }
  
  // ========= 学校管理者用API =========
  
  /**
   * 学校ダッシュボード情報を取得
   */
  async getSchoolDashboard(): Promise<{
    school_info: any;
    statistics: SchoolStats;
    recent_activities: Activity[];
    settings: SchoolSettings;
  }> {
    return this.get('/school-admin/dashboard');
  }
  
  /**
   * 学校統計情報を取得
   */
  async getSchoolStatistics(): Promise<SchoolStats> {
    return this.get('/school-admin/statistics');
  }
  
  /**
   * 学校内ユーザー一覧を取得
   */
  async getSchoolUsers(params: {
    role_name?: string;
    search_query?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    users: SchoolUser[];
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
  }> {
    return this.get('/school-admin/users', { params });
  }
  
  /**
   * 学校内の教員一覧を取得
   */
  async getSchoolTeachers(limit: number = 50): Promise<SchoolUser[]> {
    return this.get('/school-admin/teachers', { params: { limit } });
  }
  
  /**
   * 学校内の生徒一覧を取得
   */
  async getSchoolStudents(limit: number = 100): Promise<SchoolUser[]> {
    return this.get('/school-admin/students', { params: { limit } });
  }
  
  /**
   * 学校内の担当関係一覧を取得
   */
  async getSchoolAssignments(params: {
    teacher_id?: string;
    student_id?: string;
    limit?: number;
  }): Promise<TeacherStudentAssignment[]> {
    return this.get('/school-admin/assignments', { params });
  }
  
  /**
   * 新しい担当関係を作成
   */
  async createTeacherStudentAssignment(data: {
    teacher_id: string;
    student_id: string;
    school_id: string;
    assignment_type?: 'primary' | 'secondary' | 'subject_specific';
    subject?: string;
    notes?: string;
  }): Promise<TeacherStudentAssignment> {
    return this.post('/school-admin/assignments', data);
  }
  
  /**
   * 複数の担当関係を一括作成
   */
  async createBulkAssignments(data: {
    teacher_id: string;
    student_ids: string[];
    assignment_type?: 'primary' | 'secondary' | 'subject_specific';
    subject?: string;
    notes?: string;
  }): Promise<{
    success_count: number;
    failed_count: number;
    created_assignments: TeacherStudentAssignment[];
    errors: any[];
  }> {
    return this.post('/school-admin/assignments/bulk', data);
  }
  
  /**
   * 担当関係を削除
   */
  async removeTeacherStudentAssignment(assignmentId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    return this.delete(`/school-admin/assignments/${assignmentId}`);
  }
  
  /**
   * 学校設定を取得
   */
  async getSchoolSettings(): Promise<SchoolSettings> {
    return this.get('/school-admin/settings');
  }
  
  /**
   * 学校設定を更新
   */
  async updateSchoolSettings(settings: Partial<SchoolSettings>): Promise<SchoolSettings> {
    return this.put('/school-admin/settings', settings);
  }
  
  // ========= 先生用API =========
  
  /**
   * 担当生徒一覧を取得
   */
  async getAssignedStudents(params: {
    page?: number;
    page_size?: number;
    search?: string;
  }): Promise<{
    items: Array<{
      student: SchoolUser;
      assignment: TeacherStudentAssignment;
      recent_chat_sessions_count: number;
      recent_statements_count: number;
      total_desired_schools: number;
      last_activity_at?: string;
    }>;
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  }> {
    return this.get('/teacher/students', { params });
  }
  
  /**
   * 生徒の詳細情報を取得
   */
  async getStudentDetail(studentId: string): Promise<{
    student: SchoolUser;
    assignments: TeacherStudentAssignment[];
    chat_sessions: StudentChatSession[];
    statements: StudentStatement[];
    desired_schools: StudentDesiredSchool[];
    total_chat_sessions: number;
    total_statements: number;
    total_desired_schools: number;
    last_login_at?: string;
  }> {
    return this.get(`/teacher/students/${studentId}`);
  }
  
  /**
   * 生徒のチャットセッション一覧を取得
   */
  async getStudentChatSessions(
    studentId: string,
    params: {
      limit?: number;
      session_type?: string;
    }
  ): Promise<StudentChatSession[]> {
    return this.get(`/teacher/students/${studentId}/chat-sessions`, { params });
  }
  
  /**
   * 生徒の志望理由書一覧を取得
   */
  async getStudentStatements(
    studentId: string,
    limit: number = 10
  ): Promise<StudentStatement[]> {
    return this.get(`/teacher/students/${studentId}/statements`, { 
      params: { limit }
    });
  }
  
  /**
   * 生徒の志望校一覧を取得
   */
  async getStudentDesiredSchools(
    studentId: string,
    limit: number = 20
  ): Promise<StudentDesiredSchool[]> {
    return this.get(`/teacher/students/${studentId}/desired-schools`, { 
      params: { limit }
    });
  }
  
  /**
   * 自分の担当関係一覧を取得
   */
  async getMyAssignments(limit: number = 50): Promise<TeacherStudentAssignment[]> {
    return this.get('/teacher/assignments', { params: { limit } });
  }
  
  // ========= チャット詳細API =========
  
  /**
   * チャットセッションの詳細とメッセージを取得
   */
  async getChatSessionDetail(sessionId: string): Promise<{
    session: StudentChatSession;
    messages: Array<{
      id: string;
      sender_type: 'user' | 'assistant' | 'system';
      content: string;
      timestamp: string;
      metadata?: any;
    }>;
  }> {
    return this.get(`/chat/sessions/${sessionId}`);
  }
  
  /**
   * 志望理由書の詳細内容を取得
   */
  async getStatementDetail(statementId: string): Promise<{
    statement: StudentStatement;
    content: string;
    feedback?: Array<{
      id: string;
      type: 'suggestion' | 'correction' | 'praise';
      message: string;
      line_number?: number;
      created_at: string;
    }>;
    revisions: Array<{
      id: string;
      version: number;
      content: string;
      created_at: string;
      summary?: string;
    }>;
  }> {
    return this.get(`/statements/${statementId}`);
  }
}

// シングルトンインスタンス
export const tenantApi = new TenantApiClient();

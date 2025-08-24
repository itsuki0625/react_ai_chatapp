'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useSession } from 'next-auth/react';
import { 
  School, 
  SchoolUser, 
  TeacherStudentAssignment,
  Activity,
  AnalyticsData 
} from '@/types/tenant';
import { MockTenantAPI } from '@/lib/mock/tenant-api';
import { tenantApi } from '@/lib/api/tenant-client';

interface TenantContextType {
  // Current tenant (school) information
  currentSchool: School | null;
  availableSchools: School[];
  currentUser: SchoolUser | null;
  
  // Role and permission checks
  isSystemAdmin: boolean;
  isSchoolAdmin: boolean;
  isTeacher: boolean;
  isStudent: boolean;
  
  // Permission methods
  canAccessUser: (userId: string) => boolean;
  canViewStudentData: (studentId: string) => boolean;
  canManageSchool: () => boolean;
  hasPermission: (permissions: string[]) => boolean;
  
  // Data access methods
  getSchoolUsers: (role?: string) => Promise<SchoolUser[]>;
  getTeacherAssignments: (teacherId: string) => Promise<TeacherStudentAssignment[]>;
  getRecentActivities: () => Promise<Activity[]>;
  getSchoolAnalytics: () => Promise<AnalyticsData>;
  
  // School admin methods
  getSchoolStatistics: () => Promise<any>;
  createTeacherStudentAssignment: (data: any) => Promise<TeacherStudentAssignment>;
  
  // Teacher methods
  getAssignedStudents: (params?: any) => Promise<any>;
  getStudentDetail: (studentId: string) => Promise<any>;
  getStudentChatSessions: (studentId: string, params?: any) => Promise<any>;
  getStudentStatements: (studentId: string) => Promise<any>;
  getStudentDesiredSchools: (studentId: string) => Promise<any>;
  
  // Settings
  loading: boolean;
  error: string | null;
  switchSchool: (schoolId: string) => void;
  refreshData: () => Promise<void>;
  
  // Config
  useMockData: boolean;
  toggleMockData: () => void;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

interface TenantProviderProps {
  children: ReactNode;
  initialUseMockData?: boolean;
}

export function TenantProvider({ 
  children, 
  initialUseMockData = process.env.NODE_ENV === 'development' 
}: TenantProviderProps) {
  const { data: session, status } = useSession();
  
  // State management
  const [currentSchool, setCurrentSchool] = useState<School | null>(null);
  const [availableSchools, setAvailableSchools] = useState<School[]>([]);
  const [currentUser, setCurrentUser] = useState<SchoolUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [useMockData, setUseMockData] = useState(initialUseMockData);
  
  // API client selection
  const apiClient = useMockData ? MockTenantAPI : tenantApi;
  
  // Role checks
  const isSystemAdmin = currentUser?.roles?.includes('管理者') || false;
  const isSchoolAdmin = currentUser?.roles?.includes('学校管理者') || false;
  const isTeacher = currentUser?.roles?.includes('教員') || false;
  const isStudent = currentUser?.roles?.includes('フリー') || 
                   currentUser?.roles?.includes('スタンダード') || 
                   currentUser?.roles?.includes('プレミアム') || false;
  
  // Initialize user data
  useEffect(() => {
    if (status === 'loading') return;
    
    if (status === 'authenticated' && session?.user?.email) {
      initializeUserData(session.user.email);
    } else {
      setCurrentUser(null);
      setCurrentSchool(null);
      setLoading(false);
    }
  }, [status, session, useMockData]);
  
  const initializeUserData = async (email: string) => {
    try {
      setLoading(true);
      setError(null);
      
      if (useMockData) {
        // Mock APIを使用
        const user = await MockTenantAPI.getCurrentUser(email);
        const schools = await MockTenantAPI.getAvailableSchools(user.id);
        
        setCurrentUser(user);
        setAvailableSchools(schools);
        
        if (user.school_id && schools.length > 0) {
          const userSchool = schools.find(s => s.id === user.school_id);
          setCurrentSchool(userSchool || schools[0]);
        }
      } else {
        // 実APIを使用
        try {
          // 現在のユーザー情報を取得
          const userResponse = await tenantApi.get('/auth/me');
          
          // 利用可能な学校一覧を取得
          let schools: School[] = [];
          if (isSystemAdmin) {
            schools = await tenantApi.get('/admin/schools');
          } else {
            // 所属学校のみ
            if (userResponse.school_id) {
              const school = await tenantApi.get(`/schools/${userResponse.school_id}`);
              schools = [school];
            }
          }
          
          setCurrentUser(userResponse);
          setAvailableSchools(schools);
          
          if (userResponse.school_id && schools.length > 0) {
            const userSchool = schools.find(s => s.id === userResponse.school_id);
            setCurrentSchool(userSchool || schools[0]);
          }
          
        } catch (apiError: any) {
          console.warn('実API接続失敗、Mockデータにフォールバック:', apiError);
          
          // APIエラー時はMockデータにフォールバック
          const user = await MockTenantAPI.getCurrentUser(email);
          const schools = await MockTenantAPI.getAvailableSchools(user.id);
          
          setCurrentUser(user);
          setAvailableSchools(schools);
          
          if (user.school_id && schools.length > 0) {
            const userSchool = schools.find(s => s.id === user.school_id);
            setCurrentSchool(userSchool || schools[0]);
          }
        }
      }
      
    } catch (error: any) {
      console.error('ユーザーデータ初期化エラー:', error);
      setError(error.message || 'データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };
  
  // Permission methods
  const canAccessUser = (userId: string): boolean => {
    if (isSystemAdmin) return true;
    if (isSchoolAdmin && currentUser?.school_id && currentSchool?.id) {
      // 同じ学校のユーザーかチェック
      return true; // 実装時は実際のユーザー情報でチェック
    }
    if (isTeacher) {
      // 担当生徒かチェック
      return true; // 実装時は実際の担当関係でチェック
    }
    return currentUser?.id === userId;
  };
  
  const canViewStudentData = (studentId: string): boolean => {
    if (isSystemAdmin || isSchoolAdmin) return true;
    if (isTeacher) {
      // 担当生徒かチェック
      return true; // 実装時は実際の担当関係でチェック
    }
    return false;
  };
  
  const canManageSchool = (): boolean => {
    return isSystemAdmin || isSchoolAdmin;
  };
  
  const hasPermission = (permissions: string[]): boolean => {
    if (isSystemAdmin) return true;
    
    // 実装時は実際の権限チェック
    const userPermissions = currentUser?.permissions || [];
    return permissions.every(perm => userPermissions.includes(perm));
  };
  
  // Data access methods
  const getSchoolUsers = async (role?: string): Promise<SchoolUser[]> => {
    if (!currentSchool) return [];
    
    if (useMockData) {
      return MockTenantAPI.getSchoolUsers(currentSchool.id, role);
    } else {
      const response = await tenantApi.getSchoolUsers({ role_name: role });
      return response.users;
    }
  };
  
  const getTeacherAssignments = async (teacherId: string): Promise<TeacherStudentAssignment[]> => {
    if (useMockData) {
      return MockTenantAPI.getTeacherStudentAssignments(teacherId);
    } else {
      return tenantApi.getSchoolAssignments({ teacher_id: teacherId });
    }
  };
  
  const getRecentActivities = async (): Promise<Activity[]> => {
    if (!currentSchool) return [];
    
    if (useMockData) {
      return MockTenantAPI.getRecentActivities(currentSchool.id);
    } else {
      // 実APIでは学校ダッシュボードから取得
      const dashboard = await tenantApi.getSchoolDashboard();
      return dashboard.recent_activities;
    }
  };
  
  const getSchoolAnalytics = async (): Promise<AnalyticsData> => {
    if (!currentSchool) throw new Error('学校が選択されていません');
    
    if (useMockData) {
      return MockTenantAPI.getSchoolAnalytics(currentSchool.id);
    } else {
      return tenantApi.getSchoolStatistics();
    }
  };
  
  // School admin methods
  const getSchoolStatistics = async () => {
    if (useMockData) {
      return MockTenantAPI.getSchoolAnalytics(currentSchool?.id || '');
    } else {
      return tenantApi.getSchoolStatistics();
    }
  };
  
  const createTeacherStudentAssignment = async (data: any): Promise<TeacherStudentAssignment> => {
    if (useMockData) {
      return MockTenantAPI.createTeacherStudentAssignment(data);
    } else {
      return tenantApi.createTeacherStudentAssignment(data);
    }
  };
  
  // Teacher methods
  const getAssignedStudents = async (params?: any) => {
    if (useMockData) {
      const assignments = await MockTenantAPI.getTeacherStudentAssignments(currentUser?.id || '');
      return assignments; // Mockデータの構造に合わせて変換
    } else {
      return tenantApi.getAssignedStudents(params || {});
    }
  };
  
  const getStudentDetail = async (studentId: string) => {
    if (useMockData) {
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
        total_desired_schools: desiredSchools.length
      };
    } else {
      return tenantApi.getStudentDetail(studentId);
    }
  };
  
  const getStudentChatSessions = async (studentId: string, params?: any) => {
    if (useMockData) {
      return MockTenantAPI.getStudentChatSessions(studentId);
    } else {
      return tenantApi.getStudentChatSessions(studentId, params || {});
    }
  };
  
  const getStudentStatements = async (studentId: string) => {
    if (useMockData) {
      return MockTenantAPI.getStudentStatements(studentId);
    } else {
      return tenantApi.getStudentStatements(studentId);
    }
  };
  
  const getStudentDesiredSchools = async (studentId: string) => {
    if (useMockData) {
      return MockTenantAPI.getStudentDesiredSchools(studentId);
    } else {
      return tenantApi.getStudentDesiredSchools(studentId);
    }
  };
  
  // Utility methods
  const switchSchool = (schoolId: string) => {
    const school = availableSchools.find(s => s.id === schoolId);
    if (school) {
      setCurrentSchool(school);
    }
  };
  
  const refreshData = async () => {
    if (session?.user?.email) {
      await initializeUserData(session.user.email);
    }
  };
  
  const toggleMockData = () => {
    setUseMockData(prev => !prev);
    // データをリフレッシュ
    if (session?.user?.email) {
      initializeUserData(session.user.email);
    }
  };
  
  const value: TenantContextType = {
    currentSchool,
    availableSchools,
    currentUser,
    isSystemAdmin,
    isSchoolAdmin,
    isTeacher,
    isStudent,
    canAccessUser,
    canViewStudentData,
    canManageSchool,
    hasPermission,
    getSchoolUsers,
    getTeacherAssignments,
    getRecentActivities,
    getSchoolAnalytics,
    getSchoolStatistics,
    createTeacherStudentAssignment,
    getAssignedStudents,
    getStudentDetail,
    getStudentChatSessions,
    getStudentStatements,
    getStudentDesiredSchools,
    loading,
    error,
    switchSchool,
    refreshData,
    useMockData,
    toggleMockData,
  };
  
  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
}

// 便利なフック
export function useSchoolAdmin() {
  const context = useTenant();
  if (!context.isSchoolAdmin) {
    throw new Error('useSchoolAdmin can only be used by school administrators');
  }
  return context;
}

export function useTeacher() {
  const context = useTenant();
  if (!context.isTeacher) {
    throw new Error('useTeacher can only be used by teachers');
  }
  return context;
}
export interface School {
  id: string;
  name: string;
  code: string;
  address: string;
  prefecture: string;
  city: string;
  zipCode: string;
  principalName: string;
  websiteUrl?: string;
  isActive: boolean;
  settings: SchoolSettings;
  stats: SchoolStats;
  createdAt: string;
  updatedAt: string;
}

export interface SchoolSettings {
  allowStudentChat: boolean;
  requireStatementApproval: boolean;
  enableAnalytics: boolean;
  enableTeacherStudentAssignment: boolean;
  customBranding: {
    logo?: string;
    primaryColor: string;
    secondaryColor: string;
    accentColor: string;
  };
  notifications: {
    emailEnabled: boolean;
    pushEnabled: boolean;
    digestFrequency: 'daily' | 'weekly' | 'monthly';
  };
}

export interface SchoolStats {
  totalStudents: number;
  totalTeachers: number;
  totalSchoolAdmins: number;
  activeStudents: number;
  activeTeachers: number;
  statementsInProgress: number;
  completedStatements: number;
  totalChatSessions: number;
  monthlyNewUsers: number;
  averageStatementCompletionDays: number;
}

export interface SchoolUser {
  id: string;
  email: string;
  fullName: string;
  role: 'school_admin' | 'teacher' | 'student';
  schoolId: string;
  isActive: boolean;
  grade?: string;
  className?: string;
  studentNumber?: string;
  profileImageUrl?: string;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TeacherStudentAssignment {
  id: string;
  teacherId: string;
  studentId: string;
  schoolId: string;
  assignmentType: 'primary' | 'secondary' | 'subject_specific';
  subject?: string;
  isActive: boolean;
  assignedAt: string;
  assignedBy: string;
}

export interface StudentChatSession {
  id: string;
  userId: string;
  type: 'self_analysis' | 'statement_support' | 'general';
  title: string;
  status: 'active' | 'completed' | 'archived';
  messageCount: number;
  lastMessageAt: string;
  createdAt: string;
}

export interface StudentStatement {
  id: string;
  userId: string;
  title: string;
  universityName: string;
  departmentName: string;
  status: 'draft' | 'in_review' | 'completed' | 'submitted';
  wordCount: number;
  targetWordCount: number;
  progress: number;
  createdAt: string;
  updatedAt: string;
  submissionDeadline?: string;
}

export interface StudentDesiredSchool {
  id: string;
  userId: string;
  universityName: string;
  departmentName: string;
  preferenceOrder: number;
  admissionType: string;
  examDate?: string;
  status: 'considering' | 'decided' | 'applied' | 'accepted' | 'rejected';
  createdAt: string;
}

export interface Activity {
  id: string;
  schoolId: string;
  userId: string;
  userName: string;
  userRole: string;
  type: 'login' | 'statement_completed' | 'chat_started' | 'user_registered' | 'assignment_created';
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface AnalyticsData {
  monthlyProgress: {
    month: string;
    completedStatements: number;
    newUsers: number;
    activeSessions: number;
  }[];
  userActivity: {
    date: string;
    activeUsers: number;
    loginCount: number;
    chatSessions: number;
  }[];
  statementProgress: {
    status: string;
    count: number;
    percentage: number;
  }[];
  topPerformingStudents: {
    id: string;
    name: string;
    completedStatements: number;
    averageScore: number;
  }[];
}
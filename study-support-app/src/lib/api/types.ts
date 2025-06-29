// API リクエスト/レスポンス関連の型定義

// 共通API レスポンス型
export type ApiResponse<T> = {
  data: T;
  status: number;
  message?: string;
};

// セッション関連
export interface SessionWithToken {
  accessToken?: string;
  user?: {
    accessToken?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

// アプリケーション関連
export interface ApplicationData {
  university_id: string;
  department_id: string;
  admission_method_id: string;
  priority: number;
  notes?: string;
}

export interface DocumentData {
  id?: string;
  name: string;
  type: string;
  status?: string;
  dueDate?: string;
  notes?: string;
  [key: string]: unknown;
}

export interface ScheduleData {
  id?: string;
  title: string;
  date: string;
  time?: string;
  location?: string;
  type: string;
  notes?: string;
  [key: string]: unknown;
}

// 志望理由書関連
export interface StatementData {
  id?: string;
  title: string;
  content: string;
  university?: string;
  department?: string;
  status?: string;
  feedback?: FeedbackData[];
  createdAt?: string;
  updatedAt?: string;
  [key: string]: unknown;
}

export interface FeedbackData {
  id?: string;
  content: string;
  createdBy?: string;
  createdAt?: string;
  [key: string]: unknown;
}

// チャット関連
export interface StreamChatMessage {
  message: string;
  session_id?: string;
  session_type?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  [key: string]: unknown;
}

// 大学・学部関連
export interface Department {
  id: string;
  name: string;
  university_id: string;
  faculty_name?: string;
  description?: string;
  [key: string]: unknown;
}

export interface University {
  id: string;
  name: string;
  location?: string;
  type?: string;
  ranking?: number;
  departments?: Department[];
  prefecture?: string;
  address?: string;
  website_url?: string;
  description?: string;
  is_national?: boolean;
  logo_url?: string;
  [key: string]: unknown;
}

export interface AdmissionMethod {
  id: string;
  name: string;
  university_id: string;
  description?: string;
  category?: string;
  [key: string]: unknown;
}

// コンテンツ関連
export interface Content {
  id: string;
  title: string;
  description?: string;
  type: string;
  url?: string;
  category_id?: string;
  [key: string]: unknown;
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  [key: string]: unknown;
}

export interface Faq {
  id: string;
  question: string;
  answer: string;
  category?: string;
  [key: string]: unknown;
}

export interface Review {
  id?: string;
  rating: number;
  comment?: string;
  user_id?: string;
  [key: string]: unknown;
}

// 学習計画関連
export interface StudyPlan {
  id?: string;
  title: string;
  description?: string;
  startDate?: string;
  endDate?: string;
  goals?: StudyGoal[];
  [key: string]: unknown;
}

export interface StudyGoal {
  id?: string;
  title: string;
  description?: string;
  dueDate?: string;
  status?: string;
  [key: string]: unknown;
}

export interface StudyProgress {
  goalId: string;
  status: string;
  completedAt?: string;
  notes?: string;
  [key: string]: unknown;
}

// クイズ関連
export interface Quiz {
  id?: string;
  title: string;
  description?: string;
  category?: string;
  difficulty?: string;
  duration?: number;
  questions?: QuizQuestion[];
  [key: string]: unknown;
}

export interface QuizQuestion {
  id?: string;
  question: string;
  options: string[];
  correctAnswer: string | number;
  explanation?: string;
  [key: string]: unknown;
}

export interface QuizAnswer {
  questionId: string;
  answerId?: string;
  answerText?: string;
  [key: string]: unknown;
}

export interface QuizResult {
  id: string;
  score: number;
  correctAnswers: number;
  totalQuestions: number;
  completedAt: string;
  [key: string]: unknown;
}

// ユーザー設定関連
export interface UserSettings {
  id: string;
  email: string;
  name: string;
  profileImage?: string;
  notificationSettings?: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  subscription?: {
    status: string;
    plan: string;
    renewalDate?: string;
  };
  [key: string]: unknown;
}

// 通知設定関連
export interface NotificationSettingUser {
  id: string;
  user_id: string;
  notification_type: string;
  email_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  created_at: string;
  updated_at: string;
  user?: {
    id: string;
    email: string;
    full_name?: string | null;
  };
}

export interface NotificationSettingList {
  total: number;
  items: NotificationSettingUser[];
}

export interface NotificationSettingUpdateData {
  email_enabled?: boolean;
  push_enabled?: boolean;
  in_app_enabled?: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
}

// チェックリスト関連（types/api.tsから統合）
export interface ChecklistItem {
  status: boolean;
  feedback: string;
}

export interface ChecklistEvaluation {
  checklist: {
    [key: string]: ChecklistItem;
  };
  overall_status: boolean;
  general_feedback: string;
}

// Generic interface for API responses that return a list of items with pagination/total count
export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  // You can add more fields if your API provides them, like `pages`, `has_next`, `has_prev`
} 
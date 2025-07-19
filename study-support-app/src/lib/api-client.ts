import axios, { AxiosRequestHeaders } from 'axios';
import { API_BASE_URL } from '@/lib/config';
import { getSession } from 'next-auth/react';
import { ChatSession as ChatSessionType, ChatSubmitRequest, ChatTypeValue } from "@/types/chat";
import { AxiosResponse } from "axios";

// 各種レスポンス型を定義
type ApiResponse<T> = {
  data: T;
  status: number;
  message?: string;
};

// セッション型を定義
interface SessionWithToken {
  accessToken?: string;
  user?: {
    accessToken?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // 重要: CORSでクッキーを送信するために必要
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',  // AJAXリクエストであることを明示
  },
  timeout: 30000,  // 30秒のタイムアウト
});

// ★★★ 変更: リクエストインターセプターのコメントアウトを解除し、実装 ★★★
apiClient.interceptors.request.use(
  async (config) => {
    // クライアントサイドでのみ実行
    if (typeof window !== 'undefined') {
      try {
        const session = await getSession() as SessionWithToken | null;
        console.log('[ApiClientInterceptor] Session fetched:', session); // セッション情報をログ出力

        // NextAuth v5 以降など、session.accessToken が直接存在しない場合があるため
        // session?.user?.accessToken のような構造も考慮する
        // session オブジェクトと accessToken の実際の構造に合わせて調整してください
        const accessToken = session?.accessToken || session?.user?.accessToken;

        if (accessToken) {
          // config.headers が undefined の場合を考慮
          if (!config.headers) {
            config.headers = {} as AxiosRequestHeaders;
          }
          config.headers.Authorization = `Bearer ${accessToken}`;
          console.log('[ApiClientInterceptor] Authorization header added with token:', accessToken.substring(0, 20) + '...'); // トークンの一部をログ出力
        } else {
          console.warn('[ApiClientInterceptor] No access token found in session. Headers:', config.headers);
          // どのパスへのリクエストでトークンがないかログ出力
          if (config.url) {
            console.warn(`[ApiClientInterceptor] Request to ${config.url} without token.`);
          }
          // セッションはあるがトークンがない場合、その旨をより詳しくログに出す
          if (session && !accessToken) {
            console.warn('[ApiClientInterceptor] Session exists, but accessToken is missing. Session details:', session);
          }
        }
      } catch (error) {
        console.error('[ApiClientInterceptor] Failed to get session or attach token:', error);
        // セッション取得に失敗した場合でもリクエストは続行させるか、
        // エラーを投げて中断させるかは要件による
        if (config.url) {
          console.error(`[ApiClientInterceptor] Error occurred for request to ${config.url}`);
        }
      }
    }
    // ★★★ 変更: 型アサーションを削除 (不要) ★★★
    return config;
  },
  (error) => {
    // リクエストエラーの処理
    console.error('[ApiClientInterceptor] API Request Error:', error);
    return Promise.reject(error);
  }
);
// ★★★ 変更ここまで ★★★

// レスポンスインターセプター - 認証エラーの自動処理
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      console.error("API Response Error: 401 Unauthorized - Session expired");
      
      // クライアントサイドでの認証エラー処理
      if (typeof window !== 'undefined') {
        // カスタムイベントを発行して、useAuthErrorフックで処理させる
        const authErrorEvent = new CustomEvent('auth-error', {
          detail: {
            status: 401,
            error: 'Unauthorized',
            originalError: error
          }
        });
        window.dispatchEvent(authErrorEvent);
      }
    }
    return Promise.reject(error);
  }
);

// サーバーコンポーネント用のAuthorizationヘッダー付きリクエスト関数 (変更なし)
// export const withAuth = async (config: any) => {
//   if (typeof window === 'undefined') {
//     const session = await auth();
//     if (session?.accessToken) {
//       if (!config.headers) {
//         config.headers = {};
//       }
//       config.headers.Authorization = `Bearer ${session.accessToken}`;
//     }
//   }
//   return config;
// };

// クライアントサイドで認証ヘッダーを追加するヘルパー関数 - 不要になったため削除
// export const getAuthHeaders = () => {
//   const token = localStorage.getItem('token');
//   return {
//     headers: {
//       'Authorization': `Bearer ${token}`,
//       'Content-Type': 'application/json',
//     },
//     withCredentials: true
//   };
// };

// API リクエスト/レスポンスデータ型
// This ApplicationData is used for the createApplication payload.
// It should match the backend's ApplicationCreate schema.
interface ApplicationData {
  university_id: string; // UUID as string
  department_id: string; // UUID as string
  admission_method_id: string; // UUID as string
  priority: number;
  notes?: string;
  // Fields like name, university (name), department (name) are typically part of the response,
  // or resolved by the backend, not sent in the create payload if IDs are used.
  // Other fields like id, course, deadline, status, documents, schedules are also not expected for creation.
}

interface DocumentData {
  id?: string;
  name: string;
  type: string;
  status?: string;
  dueDate?: string;
  notes?: string;
  [key: string]: unknown;
}

interface ScheduleData {
  id?: string;
  title: string;
  date: string;
  time?: string;
  location?: string;
  type: string;
  notes?: string;
  [key: string]: unknown;
}

interface StatementData {
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

interface FeedbackData {
  id?: string;
  content: string;
  createdBy?: string;
  createdAt?: string;
  [key: string]: unknown;
}

// ダッシュボード関連API
export const dashboardApi = {
  getStudentDashboard: async () => {
    return apiClient.get('/api/v1/dashboard/student');
  },
  getTeacherDashboard: async () => {
    return apiClient.get('/api/v1/dashboard/teacher');
  },
  getAdminDashboard: async () => {
    return apiClient.get('/api/v1/dashboard/admin');
  },
  getProgress: async () => {
    return apiClient.get('/api/v1/dashboard/progress');
  },
  getEvents: async () => {
    return apiClient.get('/api/v1/dashboard/events');
  },
  getApplications: async () => {
    return apiClient.get('/api/v1/dashboard/applications');
  },
  getRecommendations: async () => {
    return apiClient.get('/api/v1/dashboard/recommendations');
  },
  getAiAnalysis: async () => {
    return apiClient.get('/api/v1/dashboard/ai-analysis');
  }
};

// 志望校管理API
export const applicationApi = {
  getApplications: async () => {
    return apiClient.get('/api/v1/applications/');
  },
  getApplication: async (id: string) => {
    return apiClient.get(`/api/v1/applications/${id}/`);
  },
  createApplication: async (data: ApplicationData) => {
    return apiClient.post('/api/v1/applications/', data);
  },
  updateApplication: async (id: string, data: ApplicationData) => {
    return apiClient.put(`/api/v1/applications/${id}/`, data);
  },
  deleteApplication: async (id: string) => {
    return apiClient.delete(`/api/v1/applications/${id}/`);
  },
  addDocument: async (applicationId: string, data: DocumentData) => {
    return apiClient.post(`/api/v1/applications/${applicationId}/documents/`, data);
  },
  updateDocument: async (applicationId: string, documentId: string, data: DocumentData) => {
    return apiClient.put(`/api/v1/applications/${applicationId}/documents/${documentId}/`, data);
  },
  deleteDocument: async (applicationId: string, documentId: string) => {
    return apiClient.delete(`/api/v1/applications/${applicationId}/documents/${documentId}/`);
  },
  addSchedule: async (applicationId: string, data: ScheduleData) => {
    return apiClient.post(`/api/v1/applications/${applicationId}/schedules/`, data);
  },
  updateSchedule: async (applicationId: string, scheduleId: string, data: ScheduleData) => {
    return apiClient.put(`/api/v1/applications/${applicationId}/schedules/${scheduleId}/`, data);
  },
  deleteSchedule: async (applicationId: string, scheduleId: string) => {
    return apiClient.delete(`/api/v1/applications/${applicationId}/schedules/${scheduleId}/`);
  },
  reorderApplications: async (data: { application_order: Record<string, number> }) => {
    return apiClient.put('/api/v1/applications/reorder/', data);
  },
  getStatistics: async () => {
    return apiClient.get('/api/v1/applications/statistics/');
  },
  getDeadlines: async () => {
    return apiClient.get('/api/v1/applications/deadlines/');
  }
};

// 志望理由書管理API
export const statementApi = {
  getStatements: async () => {
    return apiClient.get('/api/v1/statements/');
  },
  getStatement: async (id: string) => {
    return apiClient.get(`/api/v1/statements/${id}/`);
  },
  createStatement: async (data: StatementData) => {
    return apiClient.post('/api/v1/statements/', data);
  },
  updateStatement: async (id: string, data: StatementData) => {
    return apiClient.put(`/api/v1/statements/${id}/`, data);
  },
  deleteStatement: async (id: string) => {
    return apiClient.delete(`/api/v1/statements/${id}/`);
  },
  requestFeedback: async (id: string, data: { message?: string }) => {
    return apiClient.post(`/api/v1/statements/${id}/feedback/request/`, data);
  },
  getFeedback: async (id: string) => {
    return apiClient.get(`/api/v1/statements/${id}/feedback/`);
  },
  provideFeedback: async (id: string, data: { content: string }) => {
    return apiClient.post(`/api/v1/statements/${id}/feedback/`, data);
  },
  improveWithAI: async (id: string) => {
    return apiClient.post(`/api/v1/statements/${id}/ai-improve/`, {});
  },
  getTemplates: async () => {
    return apiClient.get('/api/v1/statements/templates/');
  },
  getExamples: async () => {
    return apiClient.get('/api/v1/statements/examples/');
  }
};

// チャットメッセージや操作のタイプ定義
interface StreamChatMessage {
  message: string;
  session_id?: string;
  session_type?: string;
}

interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  [key: string]: unknown;
}

// チャットAPI
const chatApiBase = {
  // チャットメッセージ送信 (ストリーミングなしの通常のPOSTリクエスト)
  sendChatMessage: async (token: string, data: ChatSubmitRequest): Promise<AxiosResponse<any>> => {
    return apiClient.post("/api/v1/chat/", data, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // チャットセッションリスト取得 (アクティブなもの)
  getActiveSessions: async (token: string, chatType: ChatTypeValue): Promise<AxiosResponse<ChatSessionType[]>> => {
    return apiClient.get<ChatSessionType[]>("/api/v1/chat/sessions/", {
      headers: { Authorization: `Bearer ${token}` },
      params: { chat_type: chatType, status: 'ACTIVE' },
    });
  },

  // 特定のチャットセッションのメッセージ履歴取得
  getSessionMessages: async (token: string, sessionId: string): Promise<AxiosResponse<any[]>> => { // any[] は ChatMessage[] になるべき
    return apiClient.get<any[]>(`/api/v1/chat/sessions/${sessionId}/messages/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // チャットセッションをアーカイブする
  archiveSession: async (token: string, sessionId: string): Promise<AxiosResponse<ChatSessionType>> => {
    return apiClient.patch<ChatSessionType>(`/api/v1/chat/sessions/${sessionId}/archive/`, {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // アーカイブ済みチャットセッションリスト取得
  getArchivedSessions: async (token: string, chatType: ChatTypeValue): Promise<AxiosResponse<ChatSessionType[]>> => {
    return apiClient.get<ChatSessionType[]>("/api/v1/chat/sessions/archived/", {
      headers: { Authorization: `Bearer ${token}` },
      params: { chat_type: chatType }, // chat_type でフィルタリング
    });
  },

  // チャットセッションをアーカイブ解除する
  unarchiveSession: async (token: string, sessionId: string): Promise<AxiosResponse<ChatSessionType>> => {
    return apiClient.patch<ChatSessionType>(`/api/v1/chat/sessions/${sessionId}/unarchive/`, {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  // 他のチャット関連API呼び出し関数があればここに追加
  // 例: createNewSession, updateSessionTitle など
};

// 既存の chatApi のエクスポート方法に合わせて調整する
// もし chatApi が apiClient をラップしたオブジェクトとしてエクスポートされているなら、そこにマージする
// 例: export const chatApi = { ...apiClient, ...chatApiBase };
// ここでは chatApiBase を chatApi としてエクスポートすると仮定する (既存の構造による)
export const chatApi = chatApiBase;

// Department 型を先に定義 (University が参照するため)
interface Department { // Corresponds to DepartmentResponse from backend schema
  id: string;
  name: string;
  department_code: string;  // 必須フィールドを追加
  university_id: string; 
  is_active: boolean;  // 必須フィールドを追加
  [key: string]: unknown; 
}

interface University { // Corresponds to UniversityResponse from backend schema
  id: string;
  name: string;
  location?: string; 
  type?: string; 
  ranking?: number; 
  departments?: Department[]; // Added based on backend schema UniversityResponse
  prefecture?: string; 
  address?: string;    
  website_url?: string;
  description?: string;
  is_national?: boolean;
  logo_url?: string;   
  [key: string]: unknown;
}

interface AdmissionMethod { // Corresponds to AdmissionMethodResponse from backend schema
  id: string;
  name: string;
  university_id: string; 
  description?: string; 
  category?: string;    
  [key: string]: unknown;
}

// ★★★ 新しく追加するAPIグループ ★★★
export const admissionApi = {
  getAllAdmissionMethods: async () => {
    // Assuming AdmissionMethod[] is the expected response type, similar to University[]
    // The actual response type should be verified with backend for /api/v1/admissions/
    return apiClient.get<ApiResponse<AdmissionMethod[]>>('/api/v1/admissions/');
  },
};
// ★★★ 追加ここまで ★★★

// 大学情報API
export const universityApi = {
  getUniversities: async () => {
    return apiClient.get<ApiResponse<University[]>>('/api/v1/universities');
  },
  getUniversity: async (id: string) => {
    return apiClient.get<ApiResponse<University>>(`/api/v1/universities/${id}`);
  },
  getDepartments: async (universityId: string) => {
    return apiClient.get<ApiResponse<Department[]>>(`/api/v1/universities/${universityId}/departments`);
  },
  getAdmissionMethods: async (universityId: string) => {
    return apiClient.get<ApiResponse<AdmissionMethod[]>>(`/api/v1/universities/${universityId}/admission-methods`);
  },
  searchUniversities: async (query: string) => {
    return apiClient.get<ApiResponse<University[]>>(`/api/v1/universities/search?q=${encodeURIComponent(query)}`);
  },
  getRecommendedUniversities: async () => {
    return apiClient.get<ApiResponse<University[]>>('/api/v1/universities/recommended');
  }
};

interface Content {
  id: string;
  title: string;
  description?: string;
  type: string;
  url?: string;
  category_id?: string;
  [key: string]: unknown;
}

interface Category {
  id: string;
  name: string;
  description?: string;
  [key: string]: unknown;
}

interface Faq {
  id: string;
  question: string;
  answer: string;
  category?: string;
  [key: string]: unknown;
}

interface Review {
  id?: string;
  rating: number;
  comment?: string;
  user_id?: string;
  [key: string]: unknown;
}

// 学習コンテンツAPI
export const contentApi = {
  getContents: async (categoryId?: string) => {
    const url = categoryId 
      ? `/api/v1/contents/categories/${categoryId}/` 
      : '/api/v1/contents/';
    return apiClient.get<ApiResponse<Content[]>>(url);
  },
  getContent: async (id: string) => {
    return apiClient.get<ApiResponse<Content>>(`/api/v1/contents/${id}/`);
  },
  getCategories: async () => {
    return apiClient.get<ApiResponse<Category[]>>('/api/v1/contents/categories/');
  },
  getFaqs: async () => {
    return apiClient.get<ApiResponse<Faq[]>>('/api/v1/contents/faqs/');
  },
  getFaq: async (id: string) => {
    return apiClient.get<ApiResponse<Faq>>(`/api/v1/contents/faqs/${id}/`);
  },
  recordView: async (contentId: string) => {
    return apiClient.post(`/api/v1/contents/${contentId}/view/`, {});
  },
  getReviews: async (contentId: string) => {
    return apiClient.get<ApiResponse<Review[]>>(`/api/v1/contents/${contentId}/reviews/`);
  },
  addReview: async (contentId: string, data: Review) => {
    return apiClient.post<ApiResponse<Review>>(`/api/v1/contents/${contentId}/reviews/`, data);
  },
  getRecommended: async () => {
    return apiClient.get<ApiResponse<Content[]>>('/api/v1/contents/recommended/');
  },
  getHistory: async () => {
    return apiClient.get<ApiResponse<Content[]>>('/api/v1/contents/history/');
  }
};

interface StudyPlan {
  id?: string;
  title: string;
  description?: string;
  startDate?: string;
  endDate?: string;
  goals?: StudyGoal[];
  [key: string]: unknown;
}

interface StudyGoal {
  id?: string;
  title: string;
  description?: string;
  dueDate?: string;
  status?: string;
  [key: string]: unknown;
}

interface StudyProgress {
  goalId: string;
  status: string;
  completedAt?: string;
  notes?: string;
  [key: string]: unknown;
}

// 学習計画API
export const studyPlanApi = {
  getPlans: async () => {
    return apiClient.get<ApiResponse<StudyPlan[]>>('/api/v1/study-plans');
  },
  getPlan: async (id: string) => {
    return apiClient.get<ApiResponse<StudyPlan>>(`/api/v1/study-plans/${id}`);
  },
  createPlan: async (data: StudyPlan) => {
    return apiClient.post<ApiResponse<StudyPlan>>('/api/v1/study-plans', data);
  },
  updatePlan: async (id: string, data: StudyPlan) => {
    return apiClient.put<ApiResponse<StudyPlan>>(`/api/v1/study-plans/${id}`, data);
  },
  deletePlan: async (id: string) => {
    return apiClient.delete<ApiResponse<void>>(`/api/v1/study-plans/${id}`);
  },
  addGoal: async (planId: string, data: StudyGoal) => {
    return apiClient.post<ApiResponse<StudyGoal>>(`/api/v1/study-plans/${planId}/goals`, data);
  },
  updateGoal: async (planId: string, goalId: string, data: StudyGoal) => {
    return apiClient.put<ApiResponse<StudyGoal>>(`/api/v1/study-plans/${planId}/goals/${goalId}`, data);
  },
  deleteGoal: async (planId: string, goalId: string) => {
    return apiClient.delete<ApiResponse<void>>(`/api/v1/study-plans/${planId}/goals/${goalId}`);
  },
  getProgress: async (planId: string) => {
    return apiClient.get<ApiResponse<StudyProgress[]>>(`/api/v1/study-plans/${planId}/progress`);
  },
  updateProgress: async (planId: string, data: StudyProgress[]) => {
    return apiClient.post<ApiResponse<StudyProgress[]>>(`/api/v1/study-plans/${planId}/progress`, data);
  },
  getTemplates: async () => {
    return apiClient.get<ApiResponse<StudyPlan[]>>('/api/v1/study-plans/templates');
  },
  generateWithAI: async (data: { subject?: string; duration?: string; level?: string }) => {
    return apiClient.post<ApiResponse<StudyPlan>>('/api/v1/study-plans/ai-generate', data);
  }
};

interface Quiz {
  id?: string;
  title: string;
  description?: string;
  category?: string;
  difficulty?: string;
  duration?: number;
  questions?: QuizQuestion[];
  [key: string]: unknown;
}

interface QuizQuestion {
  id?: string;
  question: string;
  options: string[];
  correctAnswer: string | number;
  explanation?: string;
  [key: string]: unknown;
}

interface QuizAnswer {
  questionId: string;
  answerId?: string;
  answerText?: string;
  [key: string]: unknown;
}

interface QuizResult {
  id: string;
  score: number;
  correctAnswers: number;
  totalQuestions: number;
  completedAt: string;
  [key: string]: unknown;
}

// クイズ・テストAPI
export const quizApi = {
  getQuizzes: async () => {
    return apiClient.get<ApiResponse<Quiz[]>>('/api/v1/quizzes/');
  },
  getQuiz: async (id: string) => {
    return apiClient.get<ApiResponse<Quiz>>(`/api/v1/quizzes/${id}/`);
  },
  createQuiz: async (data: Quiz) => {
    return apiClient.post<ApiResponse<Quiz>>('/api/v1/quizzes/', data);
  },
  updateQuiz: async (id: string, data: Quiz) => {
    return apiClient.put<ApiResponse<Quiz>>(`/api/v1/quizzes/${id}/`, data);
  },
  deleteQuiz: async (id: string) => {
    return apiClient.delete<ApiResponse<void>>(`/api/v1/quizzes/${id}/`);
  },
  addQuestion: async (quizId: string, data: QuizQuestion) => {
    return apiClient.post<ApiResponse<QuizQuestion>>(`/api/v1/quizzes/${quizId}/questions/`, data);
  },
  updateQuestion: async (quizId: string, questionId: string, data: QuizQuestion) => {
    return apiClient.put<ApiResponse<QuizQuestion>>(`/api/v1/quizzes/${quizId}/questions/${questionId}/`, data);
  },
  deleteQuestion: async (quizId: string, questionId: string) => {
    return apiClient.delete<ApiResponse<void>>(`/api/v1/quizzes/${quizId}/questions/${questionId}/`);
  },
  startAttempt: async (quizId: string) => {
    return apiClient.post<ApiResponse<{ attemptId: string }>>(`/api/v1/quizzes/${quizId}/attempt/`, {});
  },
  submitAnswers: async (quizId: string, data: { answers: QuizAnswer[] }) => {
    return apiClient.post<ApiResponse<QuizResult>>(`/api/v1/quizzes/${quizId}/submit/`, data);
  },
  getResults: async (quizId: string) => {
    return apiClient.get<ApiResponse<QuizResult[]>>(`/api/v1/quizzes/${quizId}/results/`);
  },
  getRecommended: async () => {
    return apiClient.get<ApiResponse<Quiz[]>>('/api/v1/quizzes/recommended/');
  },
  getHistory: async () => {
    return apiClient.get<ApiResponse<QuizResult[]>>('/api/v1/quizzes/history/');
  },
  getAnalysis: async () => {
    return apiClient.get<ApiResponse<{ strengths: string[]; weaknesses: string[] }>>('/api/v1/quizzes/analysis/');
  }
};

interface UserSettings {
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

// ★★★ 追加: 認証・ユーザー関連API ★★★
export const authApi = {
  // 既存の認証系API（例: login, signup）もここに移すのが望ましい

  /**
   * 現在のユーザーの設定情報とサブスクリプション情報を取得
   */
  getUserSettings: async () => {
    return apiClient.get<ApiResponse<UserSettings>>('/api/v1/auth/user-settings');
  },

  // 他の認証関連API（パスワード変更、2FAなど）も追加
};

// バックエンドの schemas.NotificationSettingUser と NotificationSettingList に対応する型定義
// (これはAPIレスポンスの型なので、必要に応じて src/types/ ディレクトリなどに別途定義しても良い)
interface NotificationSettingUser {
  id: string;
  user_id: string;
  notification_type: string; // NotificationType enum (string)
  email_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  quiet_hours_start?: string | null; // ISO datetime string or null
  quiet_hours_end?: string | null;   // ISO datetime string or null
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
  user?: { // 簡易的なユーザー情報
    id: string;
    email: string;
    full_name?: string | null;
  };
}

interface NotificationSettingList {
  total: number;
  items: NotificationSettingUser[];
}

// バックエンドの schemas.NotificationSettingUpdate に対応する型定義
interface NotificationSettingUpdateData {
  email_enabled?: boolean;
  push_enabled?: boolean;
  in_app_enabled?: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
}

export const adminNotificationSettingsApi = {
  getAllNotificationSettings: async (params?: {
    skip?: number;
    limit?: number;
    userId?: string;
  }): Promise<AxiosResponse<NotificationSettingList>> => {
    return apiClient.get('/api/v1/admin/notification-settings/', { params });
  },

  getNotificationSettingById: async (
    settingId: string
  ): Promise<AxiosResponse<NotificationSettingUser>> => {
    return apiClient.get(`/api/v1/admin/notification-settings/${settingId}`);
  },

  updateNotificationSettingById: async (
    settingId: string,
    data: NotificationSettingUpdateData
  ): Promise<AxiosResponse<NotificationSettingUser>> => {
    return apiClient.put(`/api/v1/admin/notification-settings/${settingId}`, data);
  },
}; 
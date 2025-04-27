import axios, { AxiosRequestHeaders } from 'axios';
import { API_BASE_URL } from '@/lib/config';
// import { auth } from '@/auth'; // サーバーサイドでのみ使用
import { getSession } from 'next-auth/react'; // ★★★ 変更: コメントアウト解除 ★★★

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // 重要: CORSでクッキーを送信するために必要
  headers: {
    'Content-Type': 'application/json',
  },
});

// ★★★ 変更: リクエストインターセプターのコメントアウトを解除し、実装 ★★★
apiClient.interceptors.request.use(
  async (config) => {
    // クライアントサイドでのみ実行
    if (typeof window !== 'undefined') {
      try {
        const session = await getSession();
        // NextAuth v5 以降など、session.accessToken が直接存在しない場合があるため
        // session?.user?.accessToken のような構造も考慮する
        // session オブジェクトと accessToken の実際の構造に合わせて調整してください
        const accessToken = (session as any)?.accessToken || (session?.user as any)?.accessToken; // session から accessToken を取得

        if (accessToken) {
          // config.headers が undefined の場合を考慮
          if (!config.headers) {
            config.headers = {} as AxiosRequestHeaders;
          }
          config.headers.Authorization = `Bearer ${accessToken}`;
          console.log('Authorization header added with token.'); // デバッグ用ログ
        } else {
          // トークンがない場合でもクッキー認証にフォールバックする可能性があるため、
          // ここでは警告に留める。セッション自体がない場合も同様。
          console.warn('Session found but no access token, or no session found. Proceeding without Authorization header.');
        }
      } catch (error) {
        console.error('Failed to get session or attach token:', error);
        // セッション取得に失敗した場合でもリクエストは続行させるか、
        // エラーを投げて中断させるかは要件による
      }
    }
    // ★★★ 変更: 型アサーションを削除 (不要) ★★★
    return config;
  },
  (error) => {
    // リクエストエラーの処理
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);
// ★★★ 変更ここまで ★★★

// レスポンスインターセプター - 401時のリダイレクトを一旦コメントアウト
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // if (error.response?.status === 401) {
    //   // 認証エラー時の処理
    //   // リフレッシュトークンの使用は auth.ts で行われるため
    //   // ここではログインページへのリダイレクトのみ
    //   if (typeof window !== 'undefined') {
    //     // window.location.href = '/login'; // 一旦コメントアウト
    //     console.error("API Response Error: 401 Unauthorized. Redirect disabled for debugging.");
    //   }
    // }
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
    return apiClient.get('/api/v1/applications');
  },
  getApplication: async (id: string) => {
    return apiClient.get(`/api/v1/applications/${id}`);
  },
  createApplication: async (data: any) => {
    return apiClient.post('/api/v1/applications', data);
  },
  updateApplication: async (id: string, data: any) => {
    return apiClient.put(`/api/v1/applications/${id}`, data);
  },
  deleteApplication: async (id: string) => {
    return apiClient.delete(`/api/v1/applications/${id}`);
  },
  addDocument: async (applicationId: string, data: any) => {
    return apiClient.post(`/api/v1/applications/${applicationId}/documents`, data);
  },
  updateDocument: async (applicationId: string, documentId: string, data: any) => {
    return apiClient.put(`/api/v1/applications/${applicationId}/documents/${documentId}`, data);
  },
  deleteDocument: async (applicationId: string, documentId: string) => {
    return apiClient.delete(`/api/v1/applications/${applicationId}/documents/${documentId}`);
  },
  addSchedule: async (applicationId: string, data: any) => {
    return apiClient.post(`/api/v1/applications/${applicationId}/schedules`, data);
  },
  updateSchedule: async (applicationId: string, scheduleId: string, data: any) => {
    return apiClient.put(`/api/v1/applications/${applicationId}/schedules/${scheduleId}`, data);
  },
  deleteSchedule: async (applicationId: string, scheduleId: string) => {
    return apiClient.delete(`/api/v1/applications/${applicationId}/schedules/${scheduleId}`);
  },
  reorderApplications: async (data: any) => {
    return apiClient.put('/api/v1/applications/reorder', data);
  },
  getStatistics: async () => {
    return apiClient.get('/api/v1/applications/statistics');
  },
  getDeadlines: async () => {
    return apiClient.get('/api/v1/applications/deadlines');
  }
};

// 志望理由書管理API
export const statementApi = {
  getStatements: async () => {
    return apiClient.get('/api/v1/statements');
  },
  getStatement: async (id: string) => {
    return apiClient.get(`/api/v1/statements/${id}`);
  },
  createStatement: async (data: any) => {
    return apiClient.post('/api/v1/statements', data);
  },
  updateStatement: async (id: string, data: any) => {
    return apiClient.put(`/api/v1/statements/${id}`, data);
  },
  deleteStatement: async (id: string) => {
    return apiClient.delete(`/api/v1/statements/${id}`);
  },
  requestFeedback: async (id: string, data: any) => {
    return apiClient.post(`/api/v1/statements/${id}/feedback/request`, data);
  },
  getFeedback: async (id: string) => {
    return apiClient.get(`/api/v1/statements/${id}/feedback`);
  },
  provideFeedback: async (id: string, data: any) => {
    return apiClient.post(`/api/v1/statements/${id}/feedback`, data);
  },
  improveWithAI: async (id: string) => {
    return apiClient.post(`/api/v1/statements/${id}/ai-improve`, {});
  },
  getTemplates: async () => {
    return apiClient.get('/api/v1/statements/templates');
  },
  getExamples: async () => {
    return apiClient.get('/api/v1/statements/examples');
  }
};

// チャットAPI
export const chatApi = {
  sendMessage: async (message: string) => {
    return apiClient.post('/api/v1/chat', { message });
  },
  sendStreamMessage: async (message: string, sessionId?: string, sessionType?: string) => {
    // Stream APIは fetch を直接使っているので Authorization ヘッダーを明示的に設定する必要あり
    const token = localStorage.getItem('token'); // Stream APIではlocalStorageを使っている → これも修正が必要かも
    return fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`, // ここも同様の問題がある可能性
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        session_type: sessionType
      }),
      credentials: 'include'
    });
  },
  getSessions: async () => {
    return apiClient.get('/api/v1/chat/sessions');
  },
  getArchivedSessions: async () => {
    return apiClient.get('/api/v1/chat/sessions/archived');
  },
  getSessionMessages: async (sessionId: string) => {
    return apiClient.get(`/api/v1/chat/sessions/${sessionId}/messages`);
  },
  archiveSession: async (sessionId: string) => {
    return apiClient.patch(`/api/v1/chat/sessions/${sessionId}/archive`, {});
  },
  getChecklist: async (chatId: string) => {
    return apiClient.get(`/api/v1/chat/${chatId}/checklist`);
  },
  startSelfAnalysis: async (message: string) => {
    return apiClient.post('/api/v1/chat/self-analysis', { message });
  },
  getSelfAnalysisReport: async () => {
    return apiClient.get('/api/v1/chat/self-analysis/report');
  },
  startAdmissionChat: async (message: string) => {
    return apiClient.post('/api/v1/chat/admission', { message });
  },
  startStudySupportChat: async (message: string) => {
    return apiClient.post('/api/v1/chat/study-support', { message });
  },
  getChatAnalysis: async () => {
    return apiClient.get('/api/v1/chat/analysis');
  }
};

// 大学情報API
export const universityApi = {
  getUniversities: async () => {
    return apiClient.get('/api/v1/universities');
  },
  getUniversity: async (id: string) => {
    return apiClient.get(`/api/v1/universities/${id}`);
  },
  getDepartments: async (universityId: string) => {
    return apiClient.get(`/api/v1/universities/${universityId}/departments`);
  },
  getAdmissionMethods: async (universityId: string) => {
    return apiClient.get(`/api/v1/universities/${universityId}/admission-methods`);
  },
  searchUniversities: async (query: string) => {
    return apiClient.get(`/api/v1/universities/search?q=${encodeURIComponent(query)}`);
  },
  getRecommendedUniversities: async () => {
    return apiClient.get('/api/v1/universities/recommended');
  }
};

// 学習コンテンツAPI
export const contentApi = {
  getContents: async (categoryId?: string) => {
    const url = categoryId 
      ? `/api/v1/contents/categories/${categoryId}` 
      : '/api/v1/contents';
    return apiClient.get(url);
  },
  getContent: async (id: string) => {
    return apiClient.get(`/api/v1/contents/${id}`);
  },
  getCategories: async () => {
    return apiClient.get('/api/v1/contents/categories');
  },
  getFaqs: async () => {
    return apiClient.get('/api/v1/contents/faqs');
  },
  getFaq: async (id: string) => {
    return apiClient.get(`/api/v1/contents/faqs/${id}`);
  },
  recordView: async (contentId: string) => {
    return apiClient.post(`/api/v1/contents/${contentId}/view`, {});
  },
  getReviews: async (contentId: string) => {
    return apiClient.get(`/api/v1/contents/${contentId}/reviews`);
  },
  addReview: async (contentId: string, data: any) => {
    return apiClient.post(`/api/v1/contents/${contentId}/reviews`, data);
  },
  getRecommended: async () => {
    return apiClient.get('/api/v1/contents/recommended');
  },
  getHistory: async () => {
    return apiClient.get('/api/v1/contents/history');
  }
};

// 学習計画API
export const studyPlanApi = {
  getPlans: async () => {
    return apiClient.get('/api/v1/study-plans');
  },
  getPlan: async (id: string) => {
    return apiClient.get(`/api/v1/study-plans/${id}`);
  },
  createPlan: async (data: any) => {
    return apiClient.post('/api/v1/study-plans', data);
  },
  updatePlan: async (id: string, data: any) => {
    return apiClient.put(`/api/v1/study-plans/${id}`, data);
  },
  deletePlan: async (id: string) => {
    return apiClient.delete(`/api/v1/study-plans/${id}`);
  },
  addGoal: async (planId: string, data: any) => {
    return apiClient.post(`/api/v1/study-plans/${planId}/goals`, data);
  },
  updateGoal: async (planId: string, goalId: string, data: any) => {
    return apiClient.put(`/api/v1/study-plans/${planId}/goals/${goalId}`, data);
  },
  deleteGoal: async (planId: string, goalId: string) => {
    return apiClient.delete(`/api/v1/study-plans/${planId}/goals/${goalId}`);
  },
  getProgress: async (planId: string) => {
    return apiClient.get(`/api/v1/study-plans/${planId}/progress`);
  },
  updateProgress: async (planId: string, data: any) => {
    return apiClient.post(`/api/v1/study-plans/${planId}/progress`, data);
  },
  getTemplates: async () => {
    return apiClient.get('/api/v1/study-plans/templates');
  },
  generateWithAI: async (data: any) => {
    return apiClient.post('/api/v1/study-plans/ai-generate', data);
  }
};

// クイズ・テストAPI
export const quizApi = {
  getQuizzes: async () => {
    return apiClient.get('/api/v1/quizzes');
  },
  getQuiz: async (id: string) => {
    return apiClient.get(`/api/v1/quizzes/${id}`);
  },
  createQuiz: async (data: any) => {
    return apiClient.post('/api/v1/quizzes', data);
  },
  updateQuiz: async (id: string, data: any) => {
    return apiClient.put(`/api/v1/quizzes/${id}`, data);
  },
  deleteQuiz: async (id: string) => {
    return apiClient.delete(`/api/v1/quizzes/${id}`);
  },
  addQuestion: async (quizId: string, data: any) => {
    return apiClient.post(`/api/v1/quizzes/${quizId}/questions`, data);
  },
  updateQuestion: async (quizId: string, questionId: string, data: any) => {
    return apiClient.put(`/api/v1/quizzes/${quizId}/questions/${questionId}`, data);
  },
  deleteQuestion: async (quizId: string, questionId: string) => {
    return apiClient.delete(`/api/v1/quizzes/${quizId}/questions/${questionId}`);
  },
  startAttempt: async (quizId: string) => {
    return apiClient.post(`/api/v1/quizzes/${quizId}/attempt`, {});
  },
  submitAnswers: async (quizId: string, data: any) => {
    return apiClient.post(`/api/v1/quizzes/${quizId}/submit`, data);
  },
  getResults: async (quizId: string) => {
    return apiClient.get(`/api/v1/quizzes/${quizId}/results`);
  },
  getRecommended: async () => {
    return apiClient.get('/api/v1/quizzes/recommended');
  },
  getHistory: async () => {
    return apiClient.get('/api/v1/quizzes/history');
  },
  getAnalysis: async () => {
    return apiClient.get('/api/v1/quizzes/analysis');
  }
}; 
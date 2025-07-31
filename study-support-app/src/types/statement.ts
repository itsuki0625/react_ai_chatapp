// 志望理由書のステータス
export enum StatementStatus {
  DRAFT = "draft",
  REVIEW = "review", 
  REVIEWED = "reviewed",
  FINAL = "final"
}

// 志望理由書のメインデータ型（フロントエンド表示用）
export interface PersonalStatement {
  id: string;
  title: string;
  content: string;
  status: StatementStatus;
  universityName: string;
  departmentName: string;
  keywords: string[];
  submissionDeadline?: string;
  createdAt: string;
  updatedAt: string;
  wordCount: number;
  feedbackCount: number;
  selfAnalysisChatId?: string;
}

// バックエンドAPI用の志望理由書型
export interface StatementApiResponse {
  id: string;
  user_id: string;
  title: string;
  content: string;
  status: StatementStatus;
  desired_department_id?: string;
  self_analysis_chat_id?: string;
  submission_deadline?: string;
  keywords: string[];
  university_name?: string;
  department_name?: string;
  feedback_count: number;
  word_count: number;
  created_at: string;
  updated_at: string;
}

// API レスポンスをフロントエンド型に変換するヘルパー関数
export const convertToPersonalStatement = (apiResponse: StatementApiResponse): PersonalStatement => {
  return {
    id: apiResponse.id,
    title: apiResponse.title,
    content: apiResponse.content,
    status: apiResponse.status,
    universityName: apiResponse.university_name || '',
    departmentName: apiResponse.department_name || '',
    keywords: apiResponse.keywords || [],
    submissionDeadline: apiResponse.submission_deadline,
    createdAt: apiResponse.created_at,
    updatedAt: apiResponse.updated_at,
    wordCount: apiResponse.word_count,
    feedbackCount: apiResponse.feedback_count,
    selfAnalysisChatId: apiResponse.self_analysis_chat_id,
  };
};

// AIチャットセッション
export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

// チャットメッセージ
export interface ChatMessage {
  id: string;
  sessionId: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

// 志望校情報
export interface DesiredUniversity {
  id: string;
  universityName: string;
  departmentName: string;
  priority: number;
}

// フィードバック
export interface Feedback {
  id: string;
  statementId: string;
  authorName: string;
  content: string;
  createdAt: string;
  type: "teacher" | "ai";
} 
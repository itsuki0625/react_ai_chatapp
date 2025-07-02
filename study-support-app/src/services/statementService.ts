// Placeholder for Statement API service functions
import { PersonalStatement, StatementStatus, Feedback, StatementApiResponse, convertToPersonalStatement } from '@/types/statement';
import { API_BASE_URL } from '@/lib/config';
import { fetchWithAuth } from '@/lib/fetchWithAuth';
// import { PersonalStatementCreate, PersonalStatementUpdate } from '@/types/personal_statement';

export interface CreateStatementRequest {
  title: string;
  content: string;
  status: StatementStatus;
  desired_department_id?: string;
  self_analysis_chat_id?: string;
  submission_deadline?: string;
  keywords?: string[];
}

export interface UpdateStatementRequest {
  title?: string;
  content?: string;
  status?: StatementStatus;
  desired_department_id?: string;
  self_analysis_chat_id?: string;
  submission_deadline?: string;
  keywords?: string[];
}

// AI機能用のインターフェース
export interface StatementChatRequest {
  statement_id: string;
  message: string;
  chat_history: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
  }>;
}

export interface StatementChatResponse {
  response: string;
  suggestions: string[];
  session_id: string;
}

export interface StatementImprovementRequest {
  statement_id: string;
  improvement_type: 'general' | 'structure' | 'expression' | 'logic';
  specific_focus?: string;
}

export interface StatementImprovementResponse {
  original_text: string;
  improved_text: string;
  changes: Array<{
    id: string;
    type: 'add' | 'delete' | 'modify';
    original: string;
    improved: string;
    line_number: number;
  }>;
  explanation: string;
}

// StatementApiResponseを使用するため削除
// export interface StatementResponse は StatementApiResponse に統一

// 志望理由書一覧を取得
export const getStatements = async (): Promise<StatementApiResponse[]> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    throw new Error(`Failed to fetch statements: ${response.status}`);
  }

  return response.json();
};

// 特定の志望理由書を取得
export const getStatement = async (id: string): Promise<StatementApiResponse> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${id}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    if (response.status === 404) {
      throw new Error('Statement not found.');
    }
    throw new Error(`Failed to fetch statement: ${response.status}`);
  }

  return response.json();
};

// 新しい志望理由書を作成
export const createStatement = async (data: CreateStatementRequest): Promise<StatementApiResponse> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to create statement: ${errorData.detail || response.status}`);
  }

  return response.json();
};

// 志望理由書を更新
export const updateStatement = async (id: string, data: UpdateStatementRequest): Promise<StatementApiResponse> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    if (response.status === 404) {
      throw new Error('Statement not found.');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to update statement: ${errorData.detail || response.status}`);
  }

  return response.json();
};

// 志望理由書を削除
export const deleteStatement = async (id: string): Promise<void> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${id}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    if (response.status === 404) {
      throw new Error('Statement not found.');
    }
    throw new Error(`Failed to delete statement: ${response.status}`);
  }
};

// フィードバック一覧を取得
export const getFeedbacks = async (statementId: string): Promise<Feedback[]> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${statementId}/feedback`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    throw new Error(`Failed to fetch feedbacks: ${response.status}`);
  }

  return response.json();
};

// フィードバックを作成
export const createFeedback = async (statementId: string, content: string): Promise<Feedback> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${statementId}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      content,
      personal_statement_id: statementId
    }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to create feedback: ${errorData.detail || response.status}`);
  }

  return response.json();
};

// 自己分析チャット取得
export const getSelfAnalysisChats = async (): Promise<{ 
  id: string; 
  title: string; 
  updatedAt: string; 
}[]> => {
  try {
    const response = await fetchWithAuth('/api/v1/chat/sessions?chat_type=self_analysis');
    const sessions = await response.json();
    
    return sessions.map((session: any) => ({
      id: session.id,
      title: session.title || '無題のチャット',
      updatedAt: session.updated_at || session.created_at
    }));
  } catch (error) {
    console.error('Failed to fetch self analysis chats:', error);
    return [];
  }
};

// AI機能を追加
export const sendStatementChatMessage = async (
  statementId: string,
  message: string,
  chatHistory: StatementChatRequest['chat_history'] = []
): Promise<StatementChatResponse> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${statementId}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      statement_id: statementId,
      message,
      chat_history: chatHistory,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'AIチャットの送信に失敗しました');
  }

  return response.json();
};

export const improveStatementWithAI = async (
  statementId: string,
  improvementType: StatementImprovementRequest['improvement_type'] = 'general',
  specificFocus?: string
): Promise<StatementImprovementResponse> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${statementId}/improve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      statement_id: statementId,
      improvement_type: improvementType,
      specific_focus: specificFocus,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'AI改善提案の取得に失敗しました');
  }

  return response.json();
};

// Add placeholder functions for create and update if needed later
// export const createStatement = async (data: PersonalStatementCreate): Promise<PersonalStatementResponse> => { ... };
// export const updateStatement = async (id: string, data: PersonalStatementUpdate): Promise<PersonalStatementResponse> => { ... }; 
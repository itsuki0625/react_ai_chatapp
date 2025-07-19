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

export interface AIImprovementRequest {
  personal_statement_id: string;
  focus_areas?: string[];
}

export interface AIImprovementResponse {
  statement_id: string;
  user_message: string;
  current_step: string;
  step_results: Record<string, any>;
  improvements: Record<string, any>;
  status: string;
}

export interface AIChatRequest {
  message: string;
  chat_history: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
  current_content: string;
}

export interface AIChatResponse {
  ai_message: string;
  current_step: string;
  suggestions: AISuggestion[];
  status: string;
}

export interface AISuggestion {
  type: 'replacement' | 'improvement' | 'general';
  original?: string;
  improved?: string;
  content?: string;
  reason: string;
  step: string;
}

export interface StepImprovement {
  step: string;
  title: string;
  content: string;
  suggestions: string[];
  changes: Array<{
    original: string;
    improved: string;
    reason: string;
  }>;
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

// AI添削機能を使用して志望理由書を改善
export const improveStatementWithAI = async (
  statementId: string,
  request: AIImprovementRequest
): Promise<AIImprovementResponse> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${statementId}/ai-improve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    if (response.status === 404) {
      throw new Error('Statement not found.');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to improve statement: ${errorData.detail || response.status}`);
  }

  return response.json();
};

// 対話型AI添削 - ユーザーメッセージに基づいた改善提案
export const chatWithAIForImprovement = async (
  statementId: string,
  request: AIChatRequest
): Promise<AIChatResponse> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/statements/${statementId}/ai-chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication required.');
    }
    if (response.status === 404) {
      throw new Error('Statement not found.');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to chat with AI: ${errorData.detail || response.status}`);
  }

  return response.json();
};

// AI添削結果を解析して構造化された改善案を生成
export const parseAIImprovements = (response: AIImprovementResponse): StepImprovement[] => {
  const improvements: StepImprovement[] = [];
  
  const stepNames = {
    'analysis': '分析',
    'structure': '構成',
    'content': '内容',
    'expression': '表現',
    'coherence': '一貫性',
    'polish': '仕上げ'
  };

  // バックエンドの improvements データを使用
  const improvementsData = response.improvements || response.step_results;
  
  for (const [stepKey, stepResult] of Object.entries(improvementsData)) {
    if (stepResult && typeof stepResult === 'object') {
      // contentからJSONを抽出して要約を生成
      const extractSummary = (content: string): string => {
        try {
          // 複数のJSONパターンを試行
          let jsonData = null;
          
          // パターン1: ```json...``` 形式
          const jsonMatch = content.match(/```json\s*({[\s\S]*?})\s*```/);
          if (jsonMatch) {
            jsonData = JSON.parse(jsonMatch[1]);
          }
          
          // パターン2: 単純なJSONオブジェクト
          if (!jsonData) {
            const simpleJsonMatch = content.match(/({[\s\S]*})/);
            if (simpleJsonMatch) {
              try {
                jsonData = JSON.parse(simpleJsonMatch[1]);
              } catch (e) {
                // シンプルJSON解析に失敗
              }
            }
          }
          
          if (jsonData) {
            // chatのsummaryがあれば優先的に使用
            if (jsonData.chat?.summary) {
              return jsonData.chat.summary;
            }
            
            // ステップ別の要約を生成
            if (stepKey === 'analysis' && jsonData.analysis) {
              const analysis = jsonData.analysis;
              const priorityAreas = analysis.priority_areas || analysis.priorityAreas || [];
              const score = analysis.overall_score || analysis.overallScore || analysis.score;
              return `全体スコア: ${score || 'N/A'}/10。優先改善エリア: ${priorityAreas.join(', ') || '内容・構成・表現'}`;
            }
            
            if (stepKey === 'structure' && jsonData.structure) {
              const structure = jsonData.structure;
              const improvementsCount = structure.improvements?.length || structure.suggestions?.length || 0;
              return `段落構成の改善案を${improvementsCount}件提案しました。論理的な流れを強化し、より説得力のある構成に改善します。`;
            }
            
            if (stepKey === 'content' && jsonData.content) {
              const content = jsonData.content;
              const themes = content.key_themes?.length || content.themes?.length || 0;
              const suggestions = content.suggestions?.length || 0;
              return `内容の充実度を高めるため${Math.max(themes, suggestions)}件の改善案を提案しました。エピソードの深掘りと大学との関連性を強化します。`;
            }
            
            if (stepKey === 'expression' && jsonData.expression) {
              const expression = jsonData.expression;
              const improvements = expression.sentence_improvements?.length || 
                                 expression.improvements?.length || 
                                 expression.suggestions?.length || 0;
              return `表現力向上のため${improvements}箇所の文章改善と語彙・文法・語調の調整案を提案しました。`;
            }
            
            if (stepKey === 'coherence' && jsonData.coherence) {
              const coherence = jsonData.coherence;
              const suggestions = coherence.final_suggestions?.length || 
                                coherence.suggestions?.length || 
                                coherence.improvements?.length || 0;
              return `論理的一貫性を高めるため${suggestions}項目の構成改善案を提案しました。段落間の繋がりを強化します。`;
            }
            
            if (stepKey === 'polish' && jsonData.polish) {
              const polish = jsonData.polish;
              const grade = polish.grade || polish.final_score || 'B+';
              const score = polish.final_score || polish.score || 'N/A';
              return `全体的な品質向上のための最終調整案を提案しました。現在の評価: ${grade} (スコア: ${score})`;
            }
            
            // 汎用的な要約生成（ステップ特有の情報がない場合）
            const suggestions = jsonData.suggestions || jsonData.improvements || [];
            if (suggestions.length > 0) {
              return `${suggestions.length}件の具体的な改善提案を行いました。`;
            }
          }
        } catch (error) {
          console.error('JSON parsing error:', error);
        }
        
        // JSONパースに失敗した場合の改善されたフォールバック処理
        if (content.length > 0) {
          // コンテンツから簡単な統計情報を抽出
          const sentences = content.split(/[。！？]/).filter(s => s.trim().length > 0).length;
          const words = content.replace(/\s+/g, '').length;
          
          // ステップ別の詳細なデフォルトメッセージ
          const defaultMessages = {
            'analysis': `志望理由書の全体分析を完了しました。${sentences}文、${words}文字の分析結果をもとに、構成、内容、表現の改善点を特定しました。`,
            'structure': `文章構成の分析を完了しました。段落構成と論理的な流れについて、より説得力のある構成への改善案を提案します。`,
            'content': `内容分析を完了しました。エピソードの具体性、大学との関連性、独自性の観点から改善点を特定し、内容の充実化案を提案します。`,
            'expression': `表現力分析を完了しました。文体、語彙選択、文法表現について、より洗練された表現への改善案を提案します。`,
            'coherence': `論理的一貫性の分析を完了しました。段落間の繋がりと全体的な整合性について、より一貫した論理構成への改善案を提案します。`,
            'polish': `最終仕上げ分析を完了しました。全体的な品質向上と読みやすさの観点から、完成度を高めるための調整案を提案します。`
          };
          
          return defaultMessages[stepKey as keyof typeof defaultMessages] || 
                 `${stepKey}ステップの詳細な分析と改善案を準備しました。`;
        }
        
        return `${stepKey}ステップの分析を実行中です。しばらくお待ちください。`;
      };

      const improvement: StepImprovement = {
        step: stepKey,
        title: stepNames[stepKey as keyof typeof stepNames] || stepKey,
        content: extractSummary(stepResult.content || ''),
        suggestions: stepResult.suggestions || [],
        changes: stepResult.changes || []
      };

      improvements.push(improvement);
    }
  }

  return improvements;
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

// Add placeholder functions for create and update if needed later
// export const createStatement = async (data: PersonalStatementCreate): Promise<PersonalStatementResponse> => { ... };
// export const updateStatement = async (id: string, data: PersonalStatementUpdate): Promise<PersonalStatementResponse> => { ... }; 
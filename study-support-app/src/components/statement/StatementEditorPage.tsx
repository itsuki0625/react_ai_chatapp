"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from "next-auth/react";
import { Button } from '@/components/common/Button';
import { API_BASE_URL } from '@/lib/config';
import { toast } from 'react-hot-toast';

export enum PersonalStatementStatus {
  DRAFT = "draft",
  REVIEW = "review",
  REVIEWED = "reviewed",
  FINAL = "final"
}

// ApplicationList.tsx から持ってきた型定義を追加
interface DocumentResponse {
  id: string;
  desired_department_id: string;
  name: string;
  status: string;
  deadline: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface ScheduleResponse {
  id: string;
  desired_department_id: string;
  event_name: string;
  date: string;
  type: string;
  location?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

interface ApplicationDepartmentInfo {
    id: string;
    department_id: string;
    department_name: string;
    faculty_name: string;
}

interface ApplicationDetailResponse {
  id: string;
  user_id: string;
  university_id: string;
  department_id: string;
  admission_method_id: string;
  priority: number;
  created_at: string;
  updated_at: string;
  university_name: string;
  department_name: string;
  admission_method_name: string;
  notes?: string;
  documents: DocumentResponse[];
  schedules: ScheduleResponse[];
  department_details: ApplicationDepartmentInfo[];
}
// 型定義ここまで

// 実際に使用するデータ構造に合わせた型定義に変更
interface FormattedDepartment {
  applicationId: string;
  desiredDepartmentId: string;
  universityName: string;
  departmentName: string;
  priority: number;
}

// ChatSessionSummaryに対応するフロントエンドの型定義 (APIのレスポンスに合わせて調整が必要)
interface SelfAnalysisChat {
  id: string; // UUID
  title: string | null;
  chat_type: string; // "self_analysis" など
  created_at: string; // ISO date string
  updated_at: string | null; // ISO date string
  // APIのレスポンスに含まれる他のフィールドも必要に応じて追加
}

interface Props {
  id?: string;
  initialData?: {
    id: string;
    content: string;
    status: PersonalStatementStatus;
    desired_department_id?: string;
    self_analysis_chat_id?: string; // 追加
  };
}

export default function StatementEditorPage({ id, initialData }: Props) {
  const router = useRouter();
  const { data: session, status: sessionStatus } = useSession();
  const [content, setContent] = useState(initialData?.content || '');
  const [status, setStatus] = useState<PersonalStatementStatus>(initialData?.status || PersonalStatementStatus.DRAFT);
  const [desiredDepartments, setDesiredDepartments] = useState<FormattedDepartment[]>([]);
  const [selectedDesiredDepartmentId, setSelectedDesiredDepartmentId] = useState(initialData?.desired_department_id || '');

  // 自己分析チャット関連のStateを追加
  const [selfAnalysisChats, setSelfAnalysisChats] = useState<SelfAnalysisChat[]>([]);
  const [selectedSelfAnalysisChatId, setSelectedSelfAnalysisChatId] = useState<string | undefined>(initialData?.self_analysis_chat_id || undefined);
  const [isLoadingSelfAnalysisChats, setIsLoadingSelfAnalysisChats] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    if (sessionStatus === 'authenticated' && session?.user?.accessToken) {
      fetchDesiredDepartments(controller.signal);
    } else if (sessionStatus === 'unauthenticated') {
      setError("認証が必要です。ログインしてください。");
      setIsLoading(false);
    }
    return () => controller.abort();
  }, [sessionStatus, session]);

  useEffect(() => {
    const controller = new AbortController();
    if (sessionStatus === 'authenticated' && session?.user?.accessToken) {
      fetchSelfAnalysisChats(controller.signal);
    }
    return () => controller.abort();
  }, [sessionStatus, session]);

  const fetchDesiredDepartments = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true);
    setError(null);
    try {
      const token = session?.user?.accessToken;
      if (!token) {
        setError("認証トークンが見つかりません。");
        setIsLoading(false);
        return;
      }
      const response = await fetch(
        `${API_BASE_URL}/api/v1/applications/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          signal,
        }
      );
      if (!response.ok) {
        const errorData = await response.text();
        console.error("API Error Response (DesiredDepartments):", errorData);
        throw new Error(`志望校リストの取得に失敗しました (${response.status})`);
      }
      const data: ApplicationDetailResponse[] = await response.json();
      const formattedData = data.map((app) => {
        const desiredDeptInfo = app.department_details?.[0];
        if (!desiredDeptInfo) {
          console.warn(`Application ${app.id} has no department_details`);
          return null;
        }
        return {
          applicationId: app.id,
          desiredDepartmentId: desiredDeptInfo.id,
          universityName: app.university_name,
          departmentName: desiredDeptInfo.department_name,
          priority: app.priority,
        };
      })
      .filter((item): item is FormattedDepartment => item !== null)
      .sort((a, b) => a.priority - b.priority);
      setDesiredDepartments(formattedData);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Error fetching desired departments:', err);
        setError(err.message || '志望校リストの取得中にエラーが発生しました。');
      }
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  const fetchSelfAnalysisChats = useCallback(async (signal?: AbortSignal) => {
    setIsLoadingSelfAnalysisChats(true);
    try {
      const token = session?.user?.accessToken;
      if (!token) {
        setIsLoadingSelfAnalysisChats(false);
        return;
      }
      const response = await fetch(
        `${API_BASE_URL}/api/v1/chat/sessions?chat_type=self_analysis`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          signal,
        }
      );
      if (!response.ok) {
        const errorData = await response.text();
        console.error("API Error Response (SelfAnalysisChats):", errorData);
        throw new Error(`自己分析チャットリストの取得に失敗しました (${response.status})`);
      }
      const data: SelfAnalysisChat[] = await response.json();
      setSelfAnalysisChats(data.sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime()));
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Error fetching self-analysis chats:', err);
      }
    } finally {
      setIsLoadingSelfAnalysisChats(false);
    }
  }, [session]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (sessionStatus !== 'authenticated' || !session?.user?.accessToken) {
      setError("認証が必要です。再度ログインしてください。");
      return;
    }
    if (!id && !selectedDesiredDepartmentId) { 
        setError("関連付ける志望校・学部を選択してください。");
        return;
    }

    try {
      const url = id
        ? `${API_BASE_URL}/api/v1/statements/${id}`
        : `${API_BASE_URL}/api/v1/statements/`;

      const token = session?.user?.accessToken;
      if (!token) {
        setError("認証トークンが見つかりません。");
        return;
      }

      const requestData: any = {
        content: id ? content : "",
        status: id ? status : PersonalStatementStatus.DRAFT,
      };

      if (selectedDesiredDepartmentId) {
        requestData.desired_department_id = selectedDesiredDepartmentId;
      } else if (id && !initialData?.desired_department_id) {
        // 編集時で、元々紐付いていなかった場合はキー自体を送らない (またはnullを送るかAPI仕様による)
      } else if (id && initialData?.desired_department_id) {
        // 編集時で、元々紐付いていたものを解除する場合はnullを送るかAPI仕様による
        requestData.desired_department_id = null;
      }

      if (selectedSelfAnalysisChatId) {
        requestData.self_analysis_chat_id = selectedSelfAnalysisChatId;
      } else {
        // 関連付けを解除する場合、または新規で選択しない場合はnullを送るかキー自体を送らない
        requestData.self_analysis_chat_id = null; 
      }
      
      const response = await fetch(url, {
        method: id ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Save Error:", errorData);
        throw new Error(`志望理由書の保存に失敗しました: ${errorData.detail || JSON.stringify(errorData)}`);
      }

      // router.push('/statement'); // この行をコメントアウトまたは削除
      toast.success(id ? '志望理由書を更新しました。' : '志望理由書を作成しました。'); // 成功メッセージを表示

    } catch (error) {
      console.error('Error saving statement:', error);
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('志望理由書の保存中に不明なエラーが発生しました。');
      }
    }
  };

  if (sessionStatus === 'loading' || isLoading || isLoadingSelfAnalysisChats) {
    return <div className="max-w-4xl mx-auto p-6 text-center">データを読み込み中...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {id ? '志望理由書を編集' : '新しい志望理由書を作成'}
      </h1>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 border border-red-300 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="desired-department" className="block text-sm font-medium text-gray-700 mb-2">
            関連付ける志望校・学部（志望順位順）
          </label>
          <select
            id="desired-department"
            value={selectedDesiredDepartmentId}
            onChange={(e) => setSelectedDesiredDepartmentId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            required={!id}
          >
            <option value="" disabled={!!id && !!initialData?.desired_department_id}>選択してください</option>
            {desiredDepartments.map((dept) => (
              <option key={dept.desiredDepartmentId} value={dept.desiredDepartmentId}>
                {`${dept.priority}. ${dept.universityName} - ${dept.departmentName}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="self-analysis-chat" className="block text-sm font-medium text-gray-700 mb-2">
            関連付ける自己分析チャット (任意)
          </label>
          <select
            id="self-analysis-chat"
            value={selectedSelfAnalysisChatId || ""} 
            onChange={(e) => setSelectedSelfAnalysisChatId(e.target.value || undefined)} 
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">チャットを選択しない</option>
            {selfAnalysisChats.map((chat) => (
              <option key={chat.id} value={chat.id}>
                {chat.title || `無題のチャット (${new Date(chat.updated_at || chat.created_at).toLocaleDateString()})`}
              </option>
            ))}
          </select>
        </div>

        {id && (
          <>
            <div>
              <label htmlFor="statement-content" className="block text-sm font-medium text-gray-700 mb-2">
                志望理由
              </label>
              <textarea
                id="statement-content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={15}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="志望理由を入力してください..."
                required={!!id}
              />
            </div>

            <div>
              <label htmlFor="statement-status" className="block text-sm font-medium text-gray-700 mb-2">
                ステータス
              </label>
              <select
                id="statement-status"
                value={status}
                onChange={(e) => setStatus(e.target.value as PersonalStatementStatus)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                {Object.values(PersonalStatementStatus).map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </>
        )}

        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/statement')}
          >
            キャンセル
          </Button>
          <Button type="submit">
            {id ? '更新' : '作成'}
          </Button>
        </div>
      </form>
    </div>
  );
}
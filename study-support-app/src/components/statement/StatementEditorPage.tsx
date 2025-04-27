"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/common/Button';
import { API_BASE_URL } from '@/lib/config';

enum PersonalStatementStatus {
  DRAFT = "DRAFT",
  REVIEW = "REVIEW",
  REVIEWED = "REVIEWED",
  FINAL = "FINAL"
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

interface Props {
  id?: string;
  initialData?: {
    id: string;
    content: string;
    status: PersonalStatementStatus;
    desired_department_id?: string;
  };
}

const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

export default function StatementEditorPage({ id, initialData }: Props) {
  const router = useRouter();
  const [content, setContent] = useState(initialData?.content || '');
  const [status, setStatus] = useState<PersonalStatementStatus>(initialData?.status || PersonalStatementStatus.DRAFT);
  const [desiredDepartments, setDesiredDepartments] = useState<FormattedDepartment[]>([]);
  const [selectedDesiredDepartmentId, setSelectedDesiredDepartmentId] = useState(initialData?.desired_department_id || '');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchDesiredDepartments(controller.signal);
    return () => controller.abort();
  }, []);

  const fetchDesiredDepartments = async (signal?: AbortSignal) => {
    setIsLoading(true);
    setError(null);
    try {
      const token = getToken();
      if (!token) {
        setError("認証が必要です。");
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
        console.error("API Error Response:", errorData);
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
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Error fetching desired departments:', error);
        setError(error.message || '志望校リストの取得中にエラーが発生しました。');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!selectedDesiredDepartmentId) {
      setError("志望校・学部を選択してください。");
      return;
    }

    try {
      const url = id
        ? `${API_BASE_URL}/api/v1/statements/${id}`
        : `${API_BASE_URL}/api/v1/statements/`;

      const token = getToken();
      if (!token) {
        setError("認証が必要です。");
        return;
      }

      const requestData = {
        content,
        status,
        desired_department_id: selectedDesiredDepartmentId,
      };

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

      router.push('/statement');
    } catch (error) {
      console.error('Error saving statement:', error);
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('志望理由書の保存中に不明なエラーが発生しました。');
      }
    }
  };

  if (isLoading) {
    return <div className="max-w-4xl mx-auto p-6 text-center">志望校リストを読み込み中...</div>;
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
            required
          >
            <option value="" disabled>選択してください</option>
            {desiredDepartments.map((dept) => (
              <option key={dept.desiredDepartmentId} value={dept.desiredDepartmentId}>
                {`${dept.priority}. ${dept.universityName} - ${dept.departmentName}`}
              </option>
            ))}
          </select>
        </div>

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
            required
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
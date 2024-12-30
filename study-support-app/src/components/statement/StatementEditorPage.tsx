"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/common/Button';

enum PersonalStatementStatus {
  DRAFT = "DRAFT",
  REVIEW = "REVIEW",
  REVIEWED = "REVIEWED",
  FINAL = "FINAL"
}

interface DesiredDepartment {
  id: string;
  desired_department_id: string;
  department: {
    id: string;
    name: string;
    university: {
      name: string;
    };
  };
  priority: number;
}

interface Props {
  id?: string;
  initialData?: {
    id: string;
    content: string;
    status: PersonalStatementStatus;
    desired_department_id?: string;
    desired_department?: {
      id: string;
      department: {
        id: string;
        name: string;
        university: {
          name: string;
        };
      };
    };
  };
}

const getToken = () => {
  return localStorage.getItem('token');
};

export default function StatementEditorPage({ id, initialData }: Props) {
  const router = useRouter();
  const [content, setContent] = useState(initialData?.content || '');
  const [status, setStatus] = useState<PersonalStatementStatus>(initialData?.status || 'DRAFT');
  const [desiredDepartments, setDesiredDepartments] = useState<DesiredDepartment[]>([]);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(initialData?.desired_department_id || '');

  useEffect(() => {
    const controller = new AbortController();
    fetchDesiredDepartments(controller.signal);
    return () => controller.abort();
  }, []);

  const fetchDesiredDepartments = async (signal?: AbortSignal) => {
    try {
      const token = getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/applications/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          credentials: 'include',
          signal,
        }
      );
      if (!response.ok) throw new Error('Failed to fetch desired departments');
      const data = await response.json();

      const formattedData = data.map((app: any) => {
        const desiredDept = app.desired_departments?.[0];
        if (!desiredDept) return null;

        return {
          id: app.id,
          desired_department_id: desiredDept.id,
          department: {
            id: app.department_id,
            name: app.department_name,
            university: {
              name: app.university_name
            }
          },
          priority: app.priority
        };
      })
      .filter((item: any) => item !== null)
      .sort((a: DesiredDepartment, b: DesiredDepartment) => a.priority - b.priority);

      setDesiredDepartments(formattedData);
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Error fetching desired departments:', error);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const url = id
        ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/statements/${id}`
        : `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/statements/`;

      const token = getToken();
      
      const requestData = {
        content,
        status,
        desired_department_id: selectedDepartmentId,
      };
      console.log('Request Data:', requestData);
      
      const response = await fetch(url, {
        method: id ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to save statement: ${JSON.stringify(errorData)}`);
      }
      
      router.push('/statement');
    } catch (error) {
      console.error('Error saving statement:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {id ? '志望理由書を編集' : '新しい志望理由書を作成'}
      </h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            志望校・学部（志望順位順）
          </label>
          <select
            value={selectedDepartmentId}
            onChange={(e) => setSelectedDepartmentId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">選択してください</option>
            {desiredDepartments.map((dept) => (
              <option key={dept.id} value={dept.desired_department_id}>
                {`${dept.priority}. ${dept.department.university.name} - ${dept.department.name}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            志望理由
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={15}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="志望理由を入力してください..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ステータス
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as PersonalStatementStatus)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="DRAFT">下書き</option>
            <option value="REVIEW">レビュー依頼</option>
            <option value="REVIEWED">レビュー済み</option>
            <option value="FINAL">完成</option>
          </select>
        </div>

        <div className="flex justify-end space-x-4">
          <Button
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
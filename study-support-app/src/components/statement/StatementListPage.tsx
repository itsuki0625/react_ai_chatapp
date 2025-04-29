"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Edit2, Trash2, MessageSquare } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { API_BASE_URL } from '@/lib/config';

interface PersonalStatement {
  id: string;
  content: string;
  status: 'DRAFT' | 'REVIEW' | 'REVIEWED' | 'FINAL';
  created_at: string;
  updated_at: string;
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
  feedbacks?: {
    id: string;
    content: string;
    created_at: string;
  }[];
}

const getToken = () => {
  return localStorage.getItem('token');
};

export default function StatementListPage() {
  const router = useRouter();
  const [statements, setStatements] = useState<PersonalStatement[]>([]);

  useEffect(() => {
    fetchStatements();
  }, []);

  const fetchStatements = async () => {
    try {
      const token = getToken();
      const response = await fetch(
        `${API_BASE_URL}/api/v1/statements/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          credentials: 'include',
        }
      );
      if (!response.ok) throw new Error('Failed to fetch statements');
      const data = await response.json();
      console.log('API Response:', data);
      setStatements(data);
    } catch (error) {
      console.error('Error fetching statements:', error);
    }
  };

  const getStatusBadgeColor = (status: PersonalStatement['status']) => {
    switch (status) {
      case 'DRAFT': return 'bg-gray-100 text-gray-800';
      case 'REVIEW': return 'bg-yellow-100 text-yellow-800';
      case 'REVIEWED': return 'bg-blue-100 text-blue-800';
      case 'FINAL': return 'bg-green-100 text-green-800';
    }
  };

  const getStatusText = (status: PersonalStatement['status']) => {
    switch (status) {
      case 'DRAFT': return '下書き';
      case 'REVIEW': return 'レビュー中';
      case 'REVIEWED': return 'レビュー済み';
      case 'FINAL': return '完成';
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('この志望理由書を削除してもよろしいですか？')) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/statements/${id}/`,
        {
          method: 'DELETE',
          credentials: 'include',
        }
      );
      if (!response.ok) throw new Error('Failed to delete statement');
      fetchStatements();
    } catch (error) {
      console.error('Error deleting statement:', error);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">志望理由書一覧</h1>
          <p className="mt-1 text-sm text-gray-500">
            作成した志望理由書の管理と編集ができます
          </p>
        </div>
        <Button
          onClick={() => router.push('/statement/new')}
          className="flex items-center"
        >
          <Plus className="h-5 w-5 mr-2" />
          新規作成
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statements.map((statement) => (
          <Card key={statement.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    {statement.desired_department?.department?.university?.name || '大学名未設定'}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {statement.desired_department?.department?.name || '学部・学科未設定'}
                  </p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(statement.status)}`}>
                  {getStatusText(statement.status)}
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 line-clamp-3 mb-4">
                {statement.content}
              </p>
              <div className="flex items-center justify-between mt-4">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => router.push(`/statement/${statement.id}`)}
                    className="text-gray-400 hover:text-blue-600"
                  >
                    <Edit2 className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(statement.id)}
                    className="text-gray-400 hover:text-red-600"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <MessageSquare className="h-4 w-4 mr-1" />
                  {statement.feedbacks?.length || 0}件のフィードバック
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
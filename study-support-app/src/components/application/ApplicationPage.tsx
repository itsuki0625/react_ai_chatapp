"use client";

import React, { useState, useEffect } from 'react';
import { Calendar, FileCheck, School, Clock, Plus, ChevronDown, Edit2, Trash2, AlertCircle } from 'lucide-react';
import { DesiredSchoolForm } from '@/components/application/DesiredSchoolForm';

interface Application {
  id: string;
  university_id: string;
  department_id: string;
  admission_method_id: string;
  priority: number;
  university_name: string;
  department_name: string;
  admission_method_name: string;
  status: string;
  documents: {
    id: string;
    name: string;
    status: 'DRAFT' | 'SUBMITTED' | 'REVIEWED' | 'APPROVED';
    deadline: string;
    notes?: string;
  }[];
  schedules: {
    id: string;
    event_name: string;
    date: string;
    event_type: string;
    notes?: string;
  }[];
}

const getToken = () => {
  return localStorage.getItem('token');
};

export default function ApplicationPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingApplication, setEditingApplication] = useState<Application | null>(null);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const token = getToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/applications/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch applications');
      }

      const data = await response.json();
      setApplications(data);
    } catch (error) {
      setError('志望校情報の取得に失敗しました');
      console.error('Error fetching applications:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateApplication = async (formData: any) => {
    try {
      const token = getToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/applications/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to create application');
      }

      await fetchApplications();
      setShowForm(false);
    } catch (error) {
      setError('志望校の登録に失敗しました');
      console.error('Error creating application:', error);
    }
  };

  const handleDeleteApplication = async (id: string) => {
    try {
      const token = getToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/applications/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete application');
      }

      await fetchApplications();
    } catch (error) {
      setError('志望校の削除に失敗しました');
      console.error('Error deleting application:', error);
    }
  };

  const handleEditApplication = async (id: string, formData: any) => {
    try {
      const token = getToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/applications/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to update application');
      }

      await fetchApplications();
      setEditingApplication(null);
    } catch (error) {
      setError('志望校の更新に失敗しました');
      console.error('Error updating application:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT': return 'bg-yellow-100 text-yellow-800';
      case 'SUBMITTED': return 'bg-blue-100 text-blue-800';
      case 'APPROVED': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDocumentStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT': return 'bg-gray-100 text-gray-800';
      case 'SUBMITTED': return 'bg-yellow-100 text-yellow-800';
      case 'REVIEWED': return 'bg-blue-100 text-blue-800';
      case 'APPROVED': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const isUpcoming = (date: string) => {
    const eventDate = new Date(date);
    const now = new Date();
    const diff = eventDate.getTime() - now.getTime();
    return diff > 0 && diff < 7 * 24 * 60 * 60 * 1000; // 1週間以内
  };

  if (isLoading) {
    return <div className="p-6">Loading...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-500">{error}</div>;
  }

  return (
    <div className="p-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">出願管理</h1>
          <p className="mt-1 text-sm text-gray-500">
            志望校の情報や出願書類を管理できます
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="h-5 w-5 mr-2" />
          志望校を追加
        </button>
      </div>

      {/* 出願状況サマリー */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">志望校数</p>
              <p className="text-2xl font-bold">{applications.length}</p>
            </div>
            <School className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        {/* 他のサマリー情報... */}
      </div>

      {/* 志望校リスト */}
      <div className="bg-white rounded-lg shadow">
        {applications.map((app) => (
          <div key={app.id} className="border-b border-gray-200 last:border-b-0">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <span className="text-lg font-semibold text-gray-900">
                    {app.priority}志望
                  </span>
                  <h3 className="text-lg font-medium text-gray-900">
                    {app.university_name} {app.department_name}
                  </h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(app.status)}`}>
                    {app.admission_method_name}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setEditingApplication(app)}
                    className="p-2 text-gray-400 hover:text-blue-600"
                  >
                    <Edit2 className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDeleteApplication(app.id)}
                    className="p-2 text-gray-400 hover:text-red-600"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* 提出書類 */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">提出書類</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {app.documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                        <p className="text-xs text-gray-500">
                          提出期限: {new Date(doc.deadline).toLocaleDateString()}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDocumentStatusColor(doc.status)}`}>
                        {doc.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* スケジュール */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">スケジュール</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {app.schedules.map((event) => (
                    <div key={event.id} className="flex items-center bg-gray-50 p-3 rounded-md">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{event.event_name}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(event.date).toLocaleDateString()}
                        </p>
                      </div>
                      {isUpcoming(event.date) && (
                        <AlertCircle className="h-5 w-5 text-yellow-500" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 志望校追加/編集フォーム */}
      {(showForm || editingApplication) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg max-w-2xl w-full mx-4">
            <h2 className="text-xl font-bold mb-4">
              {editingApplication ? '志望校を編集' : '志望校を追加'}
            </h2>
            <DesiredSchoolForm
              onSubmit={editingApplication 
                ? (data) => handleEditApplication(editingApplication.id, data)
                : handleCreateApplication
              }
              onCancel={() => {
                setShowForm(false);
                setEditingApplication(null);
              }}
              initialData={editingApplication}
            />
          </div>
        </div>
      )}
    </div>
  );
}
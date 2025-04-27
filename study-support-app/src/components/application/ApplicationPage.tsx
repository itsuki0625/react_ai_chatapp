"use client";

import React, { useState, useEffect } from 'react';
import { Calendar, FileCheck, School, Clock, Plus, ChevronDown, Edit2, Trash2, AlertCircle } from 'lucide-react';
import { DesiredSchoolForm } from '@/components/application/DesiredSchoolForm';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription, DialogClose, DialogTrigger } from '@/components/ui/dialog';
import { API_BASE_URL } from '@/lib/config';
import { apiClient } from '@/lib/api/client';
import { Subscription } from '@/types/subscription';
import { PlanSelection } from '@/components/subscription/PlanSelection';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

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
    type: string;
  }[];
}

interface DocumentFormData {
  name: string;
  deadline: string;
  status: 'DRAFT' | 'SUBMITTED' | 'REVIEWED' | 'APPROVED';
  notes?: string;
}

interface ScheduleFormData {
  event_name: string;
  date: string;
  type: string;
}

const getToken = () => {
  return localStorage.getItem('token');
};

// 日付をYYYY-MM-DD形式に変換する関数を追加
const formatDateForInput = (dateString: string) => {
  // UTCの日付文字列をJST（UTC+9）として解釈
  const date = new Date(dateString);
  const jstDate = new Date(date.getTime() + (9 * 60 * 60 * 1000));
  
  // 日付部分（YYYY-MM-DD）
  const dateValue = jstDate.toISOString().split('T')[0];
  // 時間部分（HH:mm）
  const timeValue = jstDate.toTimeString().slice(0, 5);
  
  return { dateValue, timeValue };
};

// 日付と時間を表示するためのフォーマット関数
const formatDateTime = (dateString: string) => {
  const date = new Date(dateString);
  const jstDate = new Date(date.getTime() + (9 * 60 * 60 * 1000));
  
  return jstDate.toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Tokyo'
  });
};

// ユーザーサブスクリプション取得 API 関数 (直接定義または別ファイルからインポート)
const fetchUserSubscription = async (): Promise<Subscription | null> => {
  try {
    const response = await apiClient.get<Subscription | null>('/subscriptions/user-subscription');
    return response.data; // null の可能性もある
  } catch (error: any) { // エラーハンドリング改善
    if (error.response && error.response.status === 404) {
      // 404 はサブスクリプションがない状態なのでエラーではない
      return null;
    }
    console.error("Error fetching user subscription:", error);
    // その他のエラーは再スローするか、null を返すかなど検討
    throw new Error("サブスクリプション情報の取得に失敗しました"); 
  }
};

export default function ApplicationPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingApplication, setEditingApplication] = useState<Application | null>(null);
  const [showDocumentForm, setShowDocumentForm] = useState(false);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [editingDocument, setEditingDocument] = useState<Application['documents'][0] | null>(null);
  const [editingSchedule, setEditingSchedule] = useState<Application['schedules'][0] | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoadingSubscription, setIsLoadingSubscription] = useState(true);
  const [subscriptionError, setSubscriptionError] = useState<string | null>(null);

  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true);
      setIsLoadingSubscription(true);
      setError(null);
      setSubscriptionError(null);

      try {
        const [appsResponse, subResponse] = await Promise.allSettled([
          fetchApplications(),
          fetchUserSubscription()
        ]);

        if (appsResponse.status === 'rejected') {
          console.error("Failed to fetch applications:", appsResponse.reason);
        }

        if (subResponse.status === 'fulfilled') {
          setSubscription(subResponse.value);
        } else {
          console.error("Failed to fetch subscription:", subResponse.reason);
          setSubscriptionError(subResponse.reason instanceof Error ? subResponse.reason.message : "サブスクリプション情報の取得に失敗しました");
        }

      } catch (err) {
        console.error("Error loading initial data:", err);
        setError("データの初期読み込みに失敗しました。");
      } finally {
        setIsLoadingSubscription(false);
      }
    };

    loadInitialData();
  }, []);

  const fetchApplications = async () => {
    try {
      const token = getToken();
      const response = await apiClient.get<Application[]>('/applications/');
      setApplications(response.data);
    } catch (error: any) {
      setError('志望校情報の取得に失敗しました');
      console.error('Error fetching applications:', error);
      throw error;
    }
  };

  const handleCreateApplication = async (formData: any) => {
    try {
      const token = getToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/applications/`, {
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
      const response = await fetch(`${API_BASE_URL}/api/v1/applications/${id}`, {
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
      const response = await fetch(`${API_BASE_URL}/api/v1/applications/${id}`, {
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

  const handleAddDocument = async (applicationId: string, documentData: DocumentFormData) => {
    try {
      const token = getToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/applications/${applicationId}/documents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify(documentData)
      });

      if (!response.ok) {
        throw new Error('Failed to add document');
      }

      await fetchApplications();
      setShowDocumentForm(false);
    } catch (error) {
      setError('書類の追加に失敗しました');
      console.error('Error adding document:', error);
    }
  };

  const handleAddSchedule = async (applicationId: string, scheduleData: ScheduleFormData) => {
    try {
      const token = getToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/applications/${applicationId}/schedules`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify(scheduleData)
      });

      if (!response.ok) {
        throw new Error('Failed to add schedule');
      }

      await fetchApplications();
      setShowScheduleForm(false);
    } catch (error) {
      setError('スケジュールの追加に失敗しました');
      console.error('Error adding schedule:', error);
    }
  };

  const handleUpdateDocument = async (applicationId: string, documentId: string, documentData: DocumentFormData) => {
    try {
      const token = getToken();
      const response = await fetch(
        `${API_BASE_URL}/api/v1/applications/${applicationId}/documents/${documentId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          credentials: 'include',
          body: JSON.stringify(documentData)
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update document');
      }

      await fetchApplications();
      setEditingDocument(null);
      setShowDocumentForm(false);
    } catch (error) {
      setError('書類の更新に失敗しました');
      console.error('Error updating document:', error);
    }
  };

  const handleUpdateSchedule = async (applicationId: string, scheduleId: string, scheduleData: ScheduleFormData) => {
    try {
      const token = getToken();
      const response = await fetch(
        `${API_BASE_URL}/api/v1/applications/${applicationId}/schedules/${scheduleId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          credentials: 'include',
          body: JSON.stringify(scheduleData)
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update schedule');
      }

      await fetchApplications();
      setEditingSchedule(null);
      setShowScheduleForm(false);
    } catch (error) {
      setError('スケジュールの更新に失敗しました');
      console.error('Error updating schedule:', error);
    }
  };

  const handleDeleteDocument = async (applicationId: string, documentId: string) => {
    try {
      const token = getToken();
      const response = await fetch(
        `${API_BASE_URL}/api/v1/applications/${applicationId}/documents/${documentId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete document');
      }

      await fetchApplications();
      setShowDocumentForm(false);
      setEditingDocument(null);
    } catch (error) {
      setError('書類の削除に失敗しました');
      console.error('Error deleting document:', error);
    }
  };

  const handleDeleteSchedule = async (applicationId: string, scheduleId: string) => {
    try {
      const token = getToken();
      const response = await fetch(
        `${API_BASE_URL}/api/v1/applications/${applicationId}/schedules/${scheduleId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete schedule');
      }

      await fetchApplications();
      setShowScheduleForm(false);
      setEditingSchedule(null);
    } catch (error) {
      setError('スケジュールの削除に失敗しました');
      console.error('Error deleting schedule:', error);
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

  // サマリー情報を計算する関数
  const getSummary = () => {
    const totalApplications = applications.length;
    
    // 提出期限が近い書類（1週間以内）
    const upcomingDocuments = applications.flatMap(app => 
      app.documents.filter(doc => 
        isUpcoming(doc.deadline) && doc.status !== 'SUBMITTED'
      )
    );

    // 今週の予定
    const upcomingSchedules = applications.flatMap(app =>
      app.schedules.filter(schedule => isUpcoming(schedule.date))
    );

    // 出願済み数
    const submittedApplications = applications.filter(app =>
      app.documents.some(doc => doc.status === 'SUBMITTED')
    ).length;

    return {
      totalApplications,
      upcomingDocuments: upcomingDocuments.length,
      upcomingSchedules: upcomingSchedules.length,
      submittedApplications
    };
  };

  if (isLoading || isLoadingSubscription) {
    return <div className="container mx-auto p-4 text-center">データを読み込み中...</div>;
  }

  if (subscriptionError && !subscription) {
    return (
      <div className="container mx-auto p-4">
        <AlertCircle className="h-5 w-5 mr-2 inline" />
        {subscriptionError}
      </div>
    );
  }

  if (!subscription || !subscription.is_active) {
    return <PlanSelection />;
  }

  return (
    <div className="container mx-auto p-4">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">エラー: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">志望校管理</h1>
        <button 
          onClick={() => setShowForm(true)}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded flex items-center"
        >
          <Plus className="mr-2 h-4 w-4" /> 志望校を追加
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">志望校数</p>
              <p className="text-2xl font-bold">{getSummary().totalApplications}</p>
            </div>
            <School className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">提出期限が近い書類</p>
              <p className="text-2xl font-bold">{getSummary().upcomingDocuments}</p>
            </div>
            <FileCheck className="h-8 w-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">今週の予定</p>
              <p className="text-2xl font-bold">{getSummary().upcomingSchedules}</p>
            </div>
            <Calendar className="h-8 w-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">出願済み</p>
              <p className="text-2xl font-bold">{getSummary().submittedApplications}</p>
            </div>
            <Clock className="h-8 w-8 text-green-500" />
          </div>
        </div>
      </div>

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

              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-sm font-medium text-gray-700">提出書類</h4>
                  <button
                    onClick={() => {
                      setSelectedApplication(app);
                      setShowDocumentForm(true);
                    }}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    書類を追加
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {app.documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                        <p className="text-xs text-gray-500">
                          提出期限: {formatDateTime(doc.deadline)}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDocumentStatusColor(doc.status)}`}>
                          {doc.status}
                        </span>
                        <button
                          onClick={() => {
                            setSelectedApplication(app);
                            setEditingDocument(doc);
                            setShowDocumentForm(true);
                          }}
                          className="p-1 text-gray-400 hover:text-blue-600"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-sm font-medium text-gray-700">スケジュール</h4>
                  <button
                    onClick={() => {
                      setSelectedApplication(app);
                      setShowScheduleForm(true);
                    }}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    スケジュールを追加
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {app.schedules.map((event) => (
                    <div key={event.id} className="flex items-center bg-gray-50 p-3 rounded-md">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{event.event_name}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(event.date).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        {isUpcoming(event.date) && (
                          <AlertCircle className="h-5 w-5 text-yellow-500" />
                        )}
                        <button
                          onClick={() => {
                            setSelectedApplication(app);
                            setEditingSchedule(event);
                            setShowScheduleForm(true);
                          }}
                          className="p-1 text-gray-400 hover:text-blue-600"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <Dialog open={showForm} onOpenChange={setShowForm}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>志望校を新規登録</DialogTitle>
              <DialogDescription>新しい志望校情報を入力してください。</DialogDescription>
            </DialogHeader>
            <DesiredSchoolForm onSubmit={handleCreateApplication} onCancel={() => setShowForm(false)} />
          </DialogContent>
        </Dialog>
      )}

      <Dialog open={!!editingApplication} onOpenChange={(open: boolean) => !open && setEditingApplication(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>志望校情報を編集</DialogTitle>
            <DialogDescription>{editingApplication?.university_name} の情報を編集します。</DialogDescription>
          </DialogHeader>
          {editingApplication && (
            <DesiredSchoolForm
              initialData={editingApplication}
              onSubmit={(formData) => handleEditApplication(editingApplication.id, formData)}
              onCancel={() => setEditingApplication(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      <Dialog
        open={showDocumentForm}
        onOpenChange={(open) => {
          if (!open) {
            setShowDocumentForm(false);
            setEditingDocument(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingDocument ? '書類情報を編集' : '提出書類を追加'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            const date = formData.get('deadline_date') as string;
            const time = formData.get('deadline_time') as string;
            
            const jstDate = new Date(`${date}T${time}:00+09:00`);
            const utcDeadline = jstDate.toISOString();
            
            const documentData = {
              name: formData.get('name') as string,
              deadline: utcDeadline,
              status: formData.get('status') as 'DRAFT' | 'SUBMITTED' | 'REVIEWED' | 'APPROVED',
              notes: formData.get('notes') as string
            };
            
            if (selectedApplication) {
              if (editingDocument) {
                handleUpdateDocument(selectedApplication.id, editingDocument.id, documentData);
              } else {
                handleAddDocument(selectedApplication.id, documentData);
              }
            }
          }}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">書類名</label>
                <input
                  type="text"
                  name="name"
                  defaultValue={editingDocument?.name}
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">提出期限</label>
                <div className="flex space-x-2">
                  <input
                    type="date"
                    name="deadline_date"
                    defaultValue={editingDocument ? formatDateForInput(editingDocument.deadline).dateValue : ''}
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  />
                  <input
                    type="time"
                    name="deadline_time"
                    defaultValue={editingDocument ? formatDateForInput(editingDocument.deadline).timeValue : ''}
                    required
                    className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">ステータス</label>
                <select
                  name="status"
                  defaultValue={editingDocument?.status}
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                >
                  <option value="DRAFT">下書き</option>
                  <option value="SUBMITTED">提出済み</option>
                  <option value="REVIEWED">確認済み</option>
                  <option value="APPROVED">承認済み</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">メモ</label>
                <textarea
                  name="notes"
                  defaultValue={editingDocument?.notes}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <Button type="button" variant="outline" onClick={() => setShowDocumentForm(false)}>キャンセル</Button>
                <Button type="submit">{editingDocument ? '更新' : '追加'}</Button>
              </div>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={showScheduleForm}
        onOpenChange={(open) => {
          if (!open) {
            setShowScheduleForm(false);
            setEditingSchedule(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingSchedule ? 'スケジュールを編集' : 'スケジュールを追加'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            const scheduleData = {
              event_name: formData.get('event_name') as string,
              date: formData.get('date') as string,
              type: formData.get('type') as string,
            };
            if (selectedApplication) {
              if (editingSchedule) {
                handleUpdateSchedule(selectedApplication.id, editingSchedule.id, scheduleData);
              } else {
                handleAddSchedule(selectedApplication.id, scheduleData);
              }
            }
          }}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">イベント名</label>
                <input
                  type="text"
                  name="event_name"
                  defaultValue={editingSchedule?.event_name}
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">日付</label>
                <input
                  type="date"
                  name="date"
                  defaultValue={editingSchedule ? formatDateForInput(editingSchedule.date).dateValue : ''}
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">イベントタイプ</label>
                <select
                  name="type"
                  defaultValue={editingSchedule?.type}
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                >
                  <option value="EXAM">試験</option>
                  <option value="INTERVIEW">面接</option>
                  <option value="SUBMISSION">書類提出</option>
                  <option value="OTHER">その他</option>
                </select>
              </div>
              <div className="flex justify-end space-x-2">
                <Button type="button" variant="outline" onClick={() => setShowScheduleForm(false)}>キャンセル</Button>
                <Button type="submit">{editingSchedule ? '更新' : '追加'}</Button>
              </div>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
"use client";

import React, { useState, useEffect } from 'react';
import { GraduationCap, Plus, Edit, Trash2, Calendar, FileText, ArrowUp, ArrowDown, ChevronDown, AlertCircle, ChevronUp } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { applicationApi } from '@/lib/api-client';
import { Button } from '@/components/ui/button';

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

export interface ScheduleResponse {
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

export interface ApplicationDetailResponse {
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

export const ApplicationList = () => {
  const [applications, setApplications] = useState<ApplicationDetailResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});
  const router = useRouter();
  
  useEffect(() => {
    const fetchApplications = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await applicationApi.getApplications();
        
        if (response.data && Array.isArray(response.data)) {
          setApplications(response.data);
        } else {
          console.error('予期しないAPIレスポンス形式:', response);
          throw new Error('データの取得中に問題が発生しました');
        }
      } catch (error) {
        console.error('志望校データの取得に失敗しました:', error);
        setError('志望校データの取得に失敗しました。');
        setApplications([]);
      } finally {
        setLoading(false);
      }
    };

    fetchApplications();
  }, []);

  const toggleExpand = (id: string) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handlePriorityChange = async (id: string, direction: 'up' | 'down') => {
    const currentApplications = [...applications];
    const index = currentApplications.findIndex(app => app.id === id);
    
    if (direction === 'up' && index > 0) {
      [currentApplications[index - 1], currentApplications[index]] = [currentApplications[index], currentApplications[index - 1]];
    } else if (direction === 'down' && index < currentApplications.length - 1) {
      [currentApplications[index], currentApplications[index + 1]] = [currentApplications[index + 1], currentApplications[index]];
    } else {
      return;
    }

    const reorderedApplications = currentApplications.map((app, idx) => ({
      ...app,
      priority: idx + 1
    }));

    setApplications(reorderedApplications);

    const applicationOrder: Record<string, number> = {};
    reorderedApplications.forEach(app => {
      applicationOrder[app.id] = app.priority;
    });

    try {
      await applicationApi.reorderApplications({ application_order: applicationOrder });
    } catch (error) {
      console.error('志望校の優先順位の更新に失敗しました:', error);
      setError('優先順位の更新に失敗しました。ページをリロードしてください。');
      setApplications(applications);
    }
  };

  const handleCreateApplication = async () => {
    router.push('/application/new');
  };

  const handleEditApplication = async (e: React.MouseEvent, applicationId: string) => {
    e.stopPropagation();
    router.push(`/dashboard/applications/edit/${applicationId}`);
  };

  const handleDeleteApplication = async (e: React.MouseEvent, applicationId: string) => {
    e.stopPropagation();
    if (confirm('この志望校情報を削除してもよろしいですか？')) {
      try {
        await applicationApi.deleteApplication(applicationId);
        setApplications(prev => prev.filter(app => app.id !== applicationId));
      } catch (error) {
        console.error('志望校の削除に失敗しました:', error);
        setError('志望校の削除に失敗しました。');
      }
    }
  };

  const handleAddDocument = async (e: React.MouseEvent, applicationId: string) => {
    e.stopPropagation();
    router.push(`/dashboard/applications/${applicationId}/documents/new`);
  };

  const handleAddSchedule = async (e: React.MouseEvent, applicationId: string) => {
    e.stopPropagation();
    router.push(`/dashboard/applications/${applicationId}/schedules/new`);
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'submitted':
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'draft':
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'submitted': return '提出済';
      case 'approved': return '承認済';
      case 'draft': return '下書き';
      case 'pending': return '未提出';
      case 'reviewed': return 'レビュー中';
      default: return '不明';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('ja-JP');
    } catch {
      return '日付不明';
    }
  };

  const calculateDocumentProgress = (documents: DocumentResponse[]) => {
    if (!documents || documents.length === 0) return 0;
    const completed = documents.filter(doc => doc.status?.toLowerCase() === 'submitted' || doc.status?.toLowerCase() === 'approved').length;
    return (completed / documents.length) * 100;
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading...</div>;
  }

  if (error && applications.length === 0) {
     return (
      <div className="text-red-600 p-4 border border-red-300 rounded bg-red-50">
        <AlertCircle className="inline-block mr-2" size={20} />
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold">志望校リスト</h2>
        <Button onClick={handleCreateApplication}>
          <Plus className="mr-2 h-4 w-4" /> 新規追加
        </Button>
      </div>

      {applications.length === 0 && !loading && !error && (
        <div className="text-center text-gray-500 py-8">志望校が登録されていません。</div>
      )}

      {applications.map((application, index) => (
        <div key={application.id} className="border rounded-lg shadow overflow-hidden">
          <div
            className="flex flex-row items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100"
            onClick={() => toggleExpand(application.id)}
          >
            <div className="flex items-center space-x-4">
              <GraduationCap className="h-8 w-8 text-blue-600" />
              <div>
                <h3 className="text-xl font-medium">{application.university_name}</h3>
                <div className="text-sm text-gray-600">
                   {application.department_name}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700 mr-2">優先度: {application.priority}</span>
              <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handlePriorityChange(application.id, 'up'); }} disabled={index === 0}>
                <ArrowUp className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handlePriorityChange(application.id, 'down'); }} disabled={index === applications.length - 1}>
                <ArrowDown className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={(e) => handleEditApplication(e, application.id)} title="編集">
                <Edit className="h-4 w-4" />
              </Button>
              <Button variant="destructive" size="sm" onClick={(e) => handleDeleteApplication(e, application.id)} title="削除">
                <Trash2 className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                 {expandedItems[application.id] ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
              </Button>
            </div>
          </div>

          {expandedItems[application.id] && (
            <div className="p-4 space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                   <h4 className="text-lg font-medium flex items-center"><FileText className="mr-2 h-5 w-5 text-purple-600"/>提出書類</h4>
                   <Button variant="outline" size="sm" onClick={(e) => handleAddDocument(e, application.id)}>
                     <Plus className="mr-1 h-4 w-4" /> 書類追加
                   </Button>
                </div>
                <div>進捗: {calculateDocumentProgress(application.documents).toFixed(0)}%</div>
                {application.documents.length > 0 ? (
                  <ul className="space-y-2">
                    {application.documents.map(doc => (
                      <li key={doc.id} className="flex justify-between items-center p-2 border rounded hover:bg-gray-50">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{doc.name}</span>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(doc.status)}`}>
                             {getStatusText(doc.status)}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600">
                           期限: {formatDate(doc.deadline)}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                   <p className="text-sm text-gray-500">登録されている書類はありません。</p>
                )}
              </div>

              <div className="space-y-3">
                 <div className="flex justify-between items-center">
                   <h4 className="text-lg font-medium flex items-center"><Calendar className="mr-2 h-5 w-5 text-indigo-600"/>関連スケジュール</h4>
                   <Button variant="outline" size="sm" onClick={(e) => handleAddSchedule(e, application.id)}>
                     <Plus className="mr-1 h-4 w-4" /> スケジュール追加
                   </Button>
                 </div>
                {application.schedules.length > 0 ? (
                  <ul className="space-y-2">
                    {application.schedules.map(schedule => (
                      <li key={schedule.id} className="flex justify-between items-center p-2 border rounded hover:bg-gray-50">
                         <div className="flex items-center space-x-2">
                           <span className="font-medium">{schedule.event_name}</span>
                           <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              {schedule.type}
                           </span>
                        </div>
                        <div className="text-sm text-gray-600">
                          日程: {formatDate(schedule.date)} {schedule.location && `(${schedule.location})`}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">登録されているスケジュールはありません。</p>
                )}
              </div>

            </div>
          )}
        </div>
      ))}
    </div>
  );
}; 
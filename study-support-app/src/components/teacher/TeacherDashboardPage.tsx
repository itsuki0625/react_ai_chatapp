"use client";

import React, { useState } from 'react';
import { 
  Users, 
  FileText, 
  MessageSquare, 
  Activity,
  Eye,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react';

interface Student {
  id: string;
  name: string;
  grade: string;
  lastActive: Date;
  progress: number;
  status: 'active' | 'inactive';
}

interface ReviewRequest {
  id: string;
  studentName: string;
  documentType: string;
  submittedAt: Date;
  status: 'pending' | 'in_review' | 'completed';
  priority: 'high' | 'medium' | 'low';
}

const TeacherDashboard = () => {
  const [students] = useState<Student[]>([
    {
      id: '1',
      name: '山田 太郎',
      grade: '3年',
      lastActive: new Date('2024-12-21'),
      progress: 75,
      status: 'active'
    },
    {
      id: '2',
      name: '佐藤 花子',
      grade: '3年',
      lastActive: new Date('2024-12-20'),
      progress: 45,
      status: 'active'
    }
  ]);

  const [reviewRequests] = useState<ReviewRequest[]>([
    {
      id: '1',
      studentName: '山田 太郎',
      documentType: '志望理由書',
      submittedAt: new Date('2024-12-21'),
      status: 'pending',
      priority: 'high'
    },
    {
      id: '2',
      studentName: '佐藤 花子',
      documentType: '活動記録',
      submittedAt: new Date('2024-12-20'),
      status: 'in_review',
      priority: 'medium'
    }
  ]);

  const getStatusColor = (status: ReviewRequest['status']) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'in_review': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
    }
  };

  return (
    <div className="p-6">
      {/* ヘッダー */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">講師ダッシュボード</h1>
        <p className="mt-1 text-sm text-gray-500">
          生徒の進捗状況と添削リクエストを管理できます
        </p>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">担当生徒数</p>
              <p className="text-2xl font-bold">24</p>
            </div>
            <Users className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">未対応の添削</p>
              <p className="text-2xl font-bold">5</p>
            </div>
            <FileText className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">本日のメッセージ</p>
              <p className="text-2xl font-bold">12</p>
            </div>
            <MessageSquare className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">平均進捗率</p>
              <p className="text-2xl font-bold">68%</p>
            </div>
            <Activity className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 生徒リスト */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">担当生徒</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {students.map((student) => (
              <div key={student.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                        <Users className="h-6 w-6 text-gray-500" />
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{student.name}</p>
                      <p className="text-sm text-gray-500">{student.grade}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${student.progress}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-500">{student.progress}%</span>
                    <button className="text-gray-400 hover:text-blue-600">
                      <Eye className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 添削リクエスト */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">添削リクエスト</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {reviewRequests.map((request) => (
              <div key={request.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-900">
                        {request.studentName}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        getStatusColor(request.status)
                      }`}>
                        {request.status === 'pending' ? '未対応' : 
                         request.status === 'in_review' ? '添削中' : '完了'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500">{request.documentType}</p>
                    <div className="flex items-center mt-1 text-xs text-gray-500">
                      <Clock className="h-4 w-4 mr-1" />
                      {request.submittedAt.toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {request.priority === 'high' && (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    )}
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm">
                      添削する
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;
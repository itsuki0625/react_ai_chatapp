"use client";

import React, { useState } from 'react';
import { Calendar, FileCheck, School, Clock, Plus, ChevronDown, Edit2, Trash2, AlertCircle } from 'lucide-react';

interface School {
  id: string;
  name: string;
  faculty: string;
  department: string;
  examType: '総合型' | '学校推薦型' | '一般';
  status: '準備中' | '出願済み' | '合格' | '不合格';
  priority: number;
  documents: {
    id: string;
    name: string;
    status: '未着手' | '作成中' | '完了';
    deadline: Date;
  }[];
  schedule: {
    id: string;
    eventName: string;
    date: Date;
    type: '出願期間' | '試験日' | '面接' | '結果発表';
    completed: boolean;
  }[];
}

const ApplicationPage = () => {
  const [schools, setSchools] = useState<School[]>([
    {
      id: '1',
      name: '慶應義塾大学',
      faculty: '環境情報学部',
      department: '環境情報学科',
      examType: '総合型',
      status: '準備中',
      priority: 1,
      documents: [
        {
          id: 'd1',
          name: '志望理由書',
          status: '完了',
          deadline: new Date('2024-12-31'),
        },
        {
          id: 'd2',
          name: '自由記述',
          status: '作成中',
          deadline: new Date('2024-12-31'),
        },
        {
            id: 'd3',
            name: '志願者評価',
            status: '未着手',
            deadline: new Date('2024-12-31'),
        },
        {
            id: 'd4',
            name: '任意提出資料',
            status: '未着手',
            deadline: new Date('2024-12-31'),
        },
      ],
      schedule: [
        {
          id: 's1',
          eventName: '出願期間',
          date: new Date('2024-12-01'),
          type: '出願期間',
          completed: false,
        },
        {
          id: 's2',
          eventName: '面接試験',
          date: new Date('2025-01-15'),
          type: '面接',
          completed: false,
        }
      ]
    },
    {
        id: '2',
        name: '筑波大学',
        faculty: '情報学群',
        department: '情報科学類',
        examType: '総合型',
        status: '準備中',
        priority: 2,
        documents: [
          {
            id: 'd1',
            name: '志望理由書',
            status: '完了',
            deadline: new Date('2024-12-31'),
          },
          {
            id: 'd2',
            name: '自己推薦書',
            status: '作成中',
            deadline: new Date('2024-12-31'),
          },
          {
              id: 'd3',
              name: '調査書',
              status: '未着手',
              deadline: new Date('2024-12-31'),
          },
          {
              id: 'd4',
              name: '入学志願書',
              status: '未着手',
              deadline: new Date('2024-12-31'),
          },
        ],
        schedule: [
          {
            id: 's1',
            eventName: '出願期間',
            date: new Date('2024-12-01'),
            type: '出願期間',
            completed: false,
          },
          {
            id: 's2',
            eventName: '面接・口述試験',
            date: new Date('2025-01-15'),
            type: '面接',
            completed: false,
          }
        ]
      },
    // 他の大学のデータ...
  ]);

  const getStatusColor = (status: School['status']) => {
    switch (status) {
      case '準備中': return 'bg-yellow-100 text-yellow-800';
      case '出願済み': return 'bg-blue-100 text-blue-800';
      case '合格': return 'bg-green-100 text-green-800';
      case '不合格': return 'bg-red-100 text-red-800';
    }
  };

  const getDocumentStatusColor = (status: string) => {
    switch (status) {
      case '未着手': return 'bg-gray-100 text-gray-800';
      case '作成中': return 'bg-yellow-100 text-yellow-800';
      case '完了': return 'bg-green-100 text-green-800';
    }
  };

  const isUpcoming = (date: Date) => {
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    return diff > 0 && diff < 7 * 24 * 60 * 60 * 1000; // 1週間以内
  };

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
        <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
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
              <p className="text-2xl font-bold">{schools.length}</p>
            </div>
            <School className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">提出期限が近い書類</p>
              <p className="text-2xl font-bold">3</p>
            </div>
            <FileCheck className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">今週の予定</p>
              <p className="text-2xl font-bold">2</p>
            </div>
            <Calendar className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">出願済み</p>
              <p className="text-2xl font-bold">1</p>
            </div>
            <Clock className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* 志望校リスト */}
      <div className="bg-white rounded-lg shadow mb-6">
        {schools.map((school) => (
          <div key={school.id} className="border-b border-gray-200 last:border-b-0">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <span className="text-lg font-semibold text-gray-900">
                    {school.priority}志望
                  </span>
                  <h3 className="text-lg font-medium text-gray-900">
                    {school.name} {school.faculty} {school.department}
                  </h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(school.status)}`}>
                    {school.status}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="p-2 text-gray-400 hover:text-blue-600">
                    <Edit2 className="h-5 w-5" />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-red-600">
                    <Trash2 className="h-5 w-5" />
                  </button>
                  <button className="p-2 text-gray-400">
                    <ChevronDown className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* 提出書類 */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">提出書類</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {school.documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                        <p className="text-xs text-gray-500">
                          提出期限: {doc.deadline.toLocaleDateString()}
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
                  {school.schedule.map((event) => (
                    <div key={event.id} className="flex items-center bg-gray-50 p-3 rounded-md">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{event.eventName}</p>
                        <p className="text-xs text-gray-500">
                          {event.date.toLocaleDateString()}
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
    </div>
  );
};

export default ApplicationPage;
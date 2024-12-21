import React from 'react';
import { FileText, Plus, Clock, Edit2, Trash2 } from 'lucide-react';

interface Statement {
  id: string;
  title: string;
  university: string;
  faculty: string;
  status: 'draft' | 'reviewing' | 'completed';
  lastModified: Date;
}

const StatementListPage = () => {
  const statements: Statement[] = [
    {
      id: '1',
      title: '第一志望大学志望理由書',
      university: '東京大学',
      faculty: '理学部',
      status: 'draft',
      lastModified: new Date('2024-12-20')
    },
    {
      id: '2',
      title: '第二志望大学志望理由書',
      university: '京都大学',
      faculty: '工学部',
      status: 'reviewing',
      lastModified: new Date('2024-12-19')
    }
  ];

  const getStatusBadge = (status: Statement['status']) => {
    const styles = {
      draft: 'bg-yellow-100 text-yellow-800',
      reviewing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800'
    };

    const labels = {
      draft: '下書き',
      reviewing: '添削中',
      completed: '完了'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">志望理由書</h1>
          <p className="mt-1 text-sm text-gray-500">
            志望理由書の作成・編集・添削ができます
          </p>
        </div>
        <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          <Plus className="h-5 w-5 mr-2" />
          新規作成
        </button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="divide-y divide-gray-200">
          {statements.map((statement) => (
            <div key={statement.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <FileText className="h-6 w-6 text-gray-400" />
                  <div>
                    <h2 className="text-lg font-medium text-gray-900">
                      {statement.title}
                    </h2>
                    <div className="mt-1 flex items-center space-x-2 text-sm text-gray-500">
                      <span>{statement.university}</span>
                      <span>•</span>
                      <span>{statement.faculty}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  {getStatusBadge(statement.status)}
                  <div className="flex items-center text-sm text-gray-500">
                    <Clock className="h-4 w-4 mr-1" />
                    <span>
                      {statement.lastModified.toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="p-2 text-gray-400 hover:text-blue-600">
                      <Edit2 className="h-5 w-5" />
                    </button>
                    <button className="p-2 text-gray-400 hover:text-red-600">
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StatementListPage;
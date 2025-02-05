"use client";

import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { API_BASE_URL } from '@/lib/config';

interface ChecklistItem {
  status: boolean;
  feedback: string;
}

interface ChecklistData {
  checklist: {
    [key: string]: ChecklistItem;
  };
  overall_status: boolean;
  general_feedback: string;
}

interface Props {
  chatId: string;
  sessionType?: string;
}

const getToken = () => {
    return localStorage.getItem('token');
  };

export const ChecklistEvaluation = ({ chatId, sessionType = 'CONSULTATION' }: Props) => {
  const [checklistData, setChecklistData] = useState<ChecklistData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChecklist = async () => {
      if (!chatId) return;

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/chat/${chatId}/checklist?session_type=${sessionType}`,
          {
            headers: {
              'Authorization': `Bearer ${getToken()}`
            },
            credentials: 'include',
          }
        );
        
        if (!response.ok) {
          if (response.status === 404) {
            setError('チェックリストがまだ作成されていません');
            return;
          }
          throw new Error('Failed to fetch checklist');
        }
        
        const data = await response.json();
        setChecklistData(data);
      } catch (error) {
        setError('チェックリストの取得に失敗しました');
        console.error('Checklist fetch error:', error);
      }
    };

    fetchChecklist();
  }, [chatId, sessionType]);

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!chatId) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <p className="text-gray-500">チャットを選択してください</p>
      </div>
    );
  }

  if (!checklistData) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-4 bg-gray-200 rounded w-full"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-medium mb-4">チェックリスト評価</h3>
      
      <div className="space-y-4 mb-6">
        {checklistData?.checklist && Object.entries(checklistData.checklist).map(([key, item]) => (
          <div key={key} className="flex items-start gap-3">
            {item.status ? (
              <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <p className="font-medium">
                {key.replace('item', '項目')}
              </p>
              <p className="text-sm text-gray-600">
                {item.feedback}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="border-t pt-4">
        <div className="flex items-center gap-2 mb-2">
          <p className="font-medium">総合評価:</p>
          {checklistData.overall_status ? (
            <span className="text-green-600">完了</span>
          ) : (
            <span className="text-red-600">未完了</span>
          )}
        </div>
        <p className="text-sm text-gray-700">
          {checklistData.general_feedback}
        </p>
      </div>
    </div>
  );
}; 
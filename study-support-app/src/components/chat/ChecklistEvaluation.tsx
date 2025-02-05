"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { API_BASE_URL } from '@/lib/config';

interface ChecklistItem {
  item: string;
  status: string;
  feedback?: string;
}

interface ChecklistData {
  checklist_items: ChecklistItem[];
  completion_status: string;
  general_feedback?: string;
}

interface Props {
  chatId: string;
  sessionType?: string;
}

const getToken = () => {
  return localStorage.getItem('token');
};

export const ChecklistEvaluation = forwardRef<{ triggerUpdate: () => void }, Props>(
  ({ chatId, sessionType = 'CONSULTATION' }, ref) => {
    const [checklistData, setChecklistData] = useState<ChecklistData | null>(null);
    const [error, setError] = useState<string | null>(null);

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

    useImperativeHandle(ref, () => ({
      triggerUpdate: () => {
        setTimeout(fetchChecklist, 5000);
      }
    }));

    // 初回マウント時のみfetchを実行
    useEffect(() => {
      if (chatId) {
        fetchChecklist();
      }
    }, []); // 依存配列を空にする

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
          {checklistData?.checklist_items.map((item, index) => (
            <div key={index} className="border rounded-lg p-4">
              <div className="flex items-start gap-3">
                {item.status === "完了" ? (
                  <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                ) : item.status === "進行中" ? (
                  <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                )}
                <div className="w-full">
                  <div className="flex justify-between items-start">
                    <p className="font-medium">{item.item}</p>
                    <span className={`px-2 py-1 rounded-full text-sm ${
                      item.status === "完了" ? "bg-green-100 text-green-800" :
                      item.status === "進行中" ? "bg-yellow-100 text-yellow-800" :
                      "bg-red-100 text-red-800"
                    }`}>
                      {item.status}
                    </span>
                  </div>
                  
                  {item.feedback && (
                    <p className="mt-2 text-sm text-gray-600">
                      {item.feedback}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="border-t pt-4">
          <div className="flex items-center gap-2 mb-2">
            <p className="font-medium">総合評価:</p>
            <span className={`px-2 py-1 rounded-full text-sm ${
              checklistData.completion_status === "完了" 
                ? "bg-green-100 text-green-800"
                : "bg-yellow-100 text-yellow-800"
            }`}>
              {checklistData.completion_status}
            </span>
          </div>
          {checklistData.general_feedback && (
            <p className="text-sm text-gray-700">
              {checklistData.general_feedback}
            </p>
          )}
        </div>
      </div>
    );
  }
);

ChecklistEvaluation.displayName = 'ChecklistEvaluation'; 
"use client";

import { forwardRef, useEffect, useImperativeHandle, useState, useCallback } from 'react';
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { API_BASE_URL } from '@/lib/config';
import { useChat } from '@/store/chat/ChatContext';

interface ChecklistItem {
  item: string;
  status: string;
  feedback?: string;
  summary?: string;
  next_question?: string;
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

export const ChecklistEvaluation = forwardRef<{ triggerUpdate: () => void }, Props>(
  ({ chatId, sessionType = 'SELF_ANALYSIS' }, ref) => {
    const [checklistItems, setChecklistItems] = useState<ChecklistItem[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const { authToken } = useChat();

    const fetchChecklist = useCallback(async () => {
      if (!chatId || !authToken) {
        if (!authToken) {
            console.warn("Checklist: Auth token not available.");
            setError("認証されていません。チェックリストを取得できません。");
        }
        if (!chatId) {
            console.warn("Checklist: ChatId not available.");
            setChecklistItems(null);
        }
        return;
      }
      setError(null);
      setChecklistItems(null);
      console.log(`Checklist: Fetching for chatId: ${chatId}, sessionType: ${sessionType}, token: ${authToken ? 'present' : 'absent'}`);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/chat/${chatId}/checklist?session_type=${sessionType}`,
          {
            headers: {
              'Authorization': `Bearer ${authToken}`,
            },
          }
        );
        
        if (!response.ok) {
          let errorDetail = 'Failed to fetch checklist';
          try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorDetail;
          } catch (e) {
            errorDetail = await response.text() || errorDetail;
          }

          if (response.status === 401) {
            setError('チェックリストの取得権限がありません。再ログインしてください。');
          } else if (response.status === 404) {
            setChecklistItems([]);
          } else {
            setError(`チェックリストの取得に失敗しました: ${errorDetail}`);
          }
          console.error('Checklist fetch error:', response.status, errorDetail);
          return;
        }
        
        const data: any[] = await response.json();
        const formattedData: ChecklistItem[] = data.map(apiItem => ({
            item: apiItem.checklist_item,
            status: apiItem.is_completed ? "完了" : "未完了",
        }));
        setChecklistItems(formattedData);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'チェックリストの取得中に予期せぬエラーが発生しました';
        setError(errorMessage);
        console.error('Checklist fetch processing error:', error);
      }
    }, [chatId, sessionType, authToken]);

    useImperativeHandle(ref, () => ({
      triggerUpdate: () => {
        console.log("Checklist: triggerUpdate called, will fetch in 5s if still mounted and conditions met.");
        setTimeout(fetchChecklist, 5000);
      }
    }));

    useEffect(() => {
      if (chatId && authToken) {
        console.log("Checklist: Initial fetch due to chatId or authToken change.");
        fetchChecklist();
      } else {
        setChecklistItems(null);
        if (!authToken) setError("認証情報がありません。");
      }
    }, [chatId, authToken, fetchChecklist]);

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

    if (!checklistItems) {
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
          {checklistItems.map((item, index) => (
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
            {checklistItems && checklistItems.every(item => item.status === "完了") ? (
              <span className="px-2 py-1 rounded-full text-sm bg-green-100 text-green-800">完了</span>
            ) : checklistItems && checklistItems.length > 0 ? (
              <span className="px-2 py-1 rounded-full text-sm bg-yellow-100 text-yellow-800">進行中</span>
            ) : (
              <span className="px-2 py-1 rounded-full text-sm bg-gray-100 text-gray-800">N/A</span>
            )}
          </div>
        </div>
      </div>
    );
  }
);

ChecklistEvaluation.displayName = 'ChecklistEvaluation'; 
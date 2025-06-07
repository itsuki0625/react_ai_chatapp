'use client';

import React, { useEffect, useCallback } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { useSession } from 'next-auth/react';
import TopBar from './TopBar';
import MainGrid from './MainGrid';
import { PersonalStatementResponse, PersonalStatementUpdate } from '@/types/personal_statement';
import { API_BASE_URL } from '@/lib/config';
import { useStatementEditorStore } from '@/store/statementEditorStore';

interface AppShellProps {
  draftIdFromParams?: string;
}

const AppShell: React.FC<AppShellProps> = ({ draftIdFromParams }) => {
  const { data: session, status: sessionStatus } = useSession();
  
  const {
    draftId,
    draftContent,
    setDraftId,
    setDraftContent,
    resetStore,
  } = useStatementEditorStore();

  const [isLoading, setIsLoading] = React.useState(true);
  const [isSaving, setIsSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  console.log('[AppShell] Render. draftIdFromParams:', draftIdFromParams, 'sessionStatus:', sessionStatus, 'isLoading:', isLoading);
  console.log('[AppShell] Session object:', session);

  const loadStatement = useCallback(async (idToLoad: string) => {
    console.log('[AppShell] loadStatement called with idToLoad:', idToLoad);
    if (!session?.user?.accessToken) {
      toast.error('認証情報が見つからないため、データ取得をスキップしました。');
      console.log('[AppShell] loadStatement skipped: No access token.');
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const token = session.user.accessToken;
      console.log('[AppShell] Fetching statement with token:', token ? 'Token vorhanden' : 'Token fehlt'); // トークンの存在確認ログ
      const response = await fetch(`${API_BASE_URL}/api/v1/statements/${idToLoad}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      console.log('[AppShell] API Response Status:', response.status); // APIレスポンスステータスログ
      if (!response.ok) {
        const errorData = await response.text();
        console.error('[AppShell] API Error Data:', errorData); // APIエラーデータログ
        throw new Error(`志望理由書の取得に失敗 (${response.status}): ${errorData}`);
      }
      const responseData: PersonalStatementResponse[] | PersonalStatementResponse = await response.json();
      console.log('[AppShell] API Response Data:', responseData); // APIレスポンスデータログ
      
      let dataToSet: PersonalStatementResponse | null = null;
      if (Array.isArray(responseData) && responseData.length > 0) {
        dataToSet = responseData[0];
      } else if (!Array.isArray(responseData)) {
        dataToSet = responseData;
      }

      if (dataToSet) {
        console.log('[AppShell] Setting store with data:', dataToSet); // ストアにセットするデータログ
        setDraftId(dataToSet.id);
        setDraftContent(dataToSet.content || '');
      } else {
        console.warn('[AppShell] No data to set from API response.'); // データなし警告ログ
        throw new Error('取得したデータ形式が正しくありません、またはデータが空です。');
      }
    } catch (err) {
      console.error('[AppShell] Error in loadStatement:', err); // loadStatement内エラーログ
      const errorMessage = err instanceof Error ? err.message : 'データの取得中にエラーが発生しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [session, setDraftId, setDraftContent, setIsLoading, setError]);

  useEffect(() => {
    console.log('[AppShell] useEffect triggered. draftIdFromParams:', draftIdFromParams, 'sessionStatus:', sessionStatus);
    const cleanup = () => {
      console.log('[AppShell] useEffect cleanup. Resetting store.');
      resetStore();
    };

    if (draftIdFromParams) {
      console.log('[AppShell] useEffect: draftIdFromParams exists.');
      if (sessionStatus === 'authenticated' && session?.user?.accessToken) {
        console.log('[AppShell] useEffect: Session authenticated. Calling setDraftId and loadStatement.');
        setDraftId(draftIdFromParams);
        loadStatement(draftIdFromParams);
      } else if (sessionStatus === 'loading') {
        console.log('[AppShell] useEffect: Session loading. Setting isLoading to true.');
        setIsLoading(true);
      } else if (sessionStatus === 'unauthenticated') {
        console.log('[AppShell] useEffect: Session unauthenticated.');
        setError('認証が必要です。ログインしてください。');
        setIsLoading(false);
        resetStore();
      }
    } else {
      console.log('[AppShell] useEffect: No draftIdFromParams. Resetting store.');
      resetStore();
      setIsLoading(false);
    }
    return cleanup;
  }, [draftIdFromParams, sessionStatus, session, resetStore, setDraftId, loadStatement, setError, setIsLoading]);

  const handleSave = async () => {
    if (!draftId) {
      toast.error('保存対象のIDがありません。');
      return;
    }
    if (sessionStatus !== 'authenticated' || !session?.user?.accessToken) {
      toast.error('認証エラー。保存できませんでした。');
      return;
    }
    setIsSaving(true);
    setError(null);
    try {
      const token = session.user.accessToken;
      const contentToSave = useStatementEditorStore.getState().draftContent;
      const requestBody: PersonalStatementUpdate = { content: contentToSave }; 
      const response = await fetch(`${API_BASE_URL}/api/v1/statements/${draftId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`保存に失敗 (${response.status}): ${errorData.detail || JSON.stringify(errorData)}`);
      }
      const updatedStatement: PersonalStatementResponse = await response.json();
      setDraftContent(updatedStatement.content || '');
      toast.success('志望理由書を保存しました。');
    } catch (err) {
      console.error('Error saving statement:', err);
      const errorMessage = err instanceof Error ? err.message : '保存中にエラーが発生しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleContentChangeInStore = (newContent: string) => {
    setDraftContent(newContent);
  };

  if (isLoading && draftIdFromParams) {
    return (
      <div className="flex flex-col h-screen items-center justify-center">
        <p>志望理由書を読み込み中...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      <Toaster position="top-center" reverseOrder={false} />
      <TopBar 
        draftId={draftId ?? undefined}
        onSave={handleSave} 
        isSaving={isSaving} 
      />
      <MainGrid 
        draftId={draftId ?? undefined}
        initialContent={draftContent}
        onContentChange={handleContentChangeInStore}
        isLoading={isLoading && !!draftIdFromParams} 
        error={error}
      />
    </div>
  );
};

export default AppShell; 
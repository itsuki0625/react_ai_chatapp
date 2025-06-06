'use client';

import React, { useEffect, useState } from 'react';

interface DraftPaneProps {
  draftId?: string;
  initialContent: string;
  onContentChange: (newContent: string) => void;
  isLoading: boolean;
  error: string | null;
}

const DraftPane: React.FC<DraftPaneProps> = ({ 
  draftId, 
  initialContent, 
  onContentChange, 
  isLoading, 
  error 
}) => {
  const [localContent, setLocalContent] = useState(initialContent);

  useEffect(() => {
    setLocalContent(initialContent);
  }, [initialContent]);

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setLocalContent(event.target.value);
    onContentChange(event.target.value);
  };

  if (isLoading) {
    return (
      <div className="bg-slate-50 h-full overflow-y-auto p-4 border-r border-slate-300 flex items-center justify-center">
        <p>内容を読み込み中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-50 h-full overflow-y-auto p-4 border-r border-slate-300">
        <h2 className="text-lg font-semibold mb-2 text-red-600">エラー</h2>
        <p className="text-red-500">{error}</p>
        <p className="text-sm mt-2">データの読み込みに失敗しました。再試行するか、管理者にお問い合わせください。</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-50 h-full overflow-y-auto p-4 border-r border-slate-300 flex flex-col">
      <h2 className="text-lg font-semibold mb-2">Draft Pane</h2>
      <textarea
        className="w-full h-full flex-grow p-2 border border-slate-300 rounded resize-none prose max-w-none"
        value={localContent}
        onChange={handleChange}
        placeholder="ここに志望理由書の内容を入力してください..."
      />
    </div>
  );
};

export default DraftPane; 
'use client';

import React from 'react';
import DraftPane from './DraftPane';
import ChatPane from './ChatPane';

interface MainGridProps {
  draftId?: string;
  initialContent: string;
  onContentChange: (newContent: string) => void;
  isLoading: boolean;
  error: string | null;
  // 他に必要なpropsがあれば追加
}

const MainGrid: React.FC<MainGridProps> = ({ 
  draftId, 
  initialContent, 
  onContentChange, 
  isLoading, 
  error 
}) => {
  return (
    <main className="grid grid-cols-[minmax(640px,1fr)_minmax(360px,0.5fr)] flex-grow overflow-hidden">
      <DraftPane 
        draftId={draftId} 
        initialContent={initialContent} 
        onContentChange={onContentChange}
        isLoading={isLoading}
        error={error}
      />
      <ChatPane draftId={draftId} />
    </main>
  );
};

export default MainGrid; 
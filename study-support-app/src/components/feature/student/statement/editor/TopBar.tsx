'use client';

import React from 'react';
import { Button } from '@/components/ui/button'; // 既存のButtonコンポーネントのパスを想定

interface TopBarProps {
  draftId?: string;
  onSave?: () => void; // 保存ボタンのクリックイベントハンドラをpropsとして追加
  isSaving?: boolean; // 保存中かどうかを示すフラグ
  // 他に必要なpropsがあれば追加 (例: draftTitle, userTokens)
}

const TopBar: React.FC<TopBarProps> = ({ draftId, onSave, isSaving }) => {
  return (
    <header className="bg-slate-800 text-white p-3 flex justify-between items-center shadow-md z-10">
      <div>
        <h1 className="text-xl font-semibold">
          {draftId ? `志望理由書 - ${draftId.substring(0, 8)}...` : '新しい志望理由書'}
        </h1>
        {/* 将来的にはここに実際のドラフトタイトルを表示 */}
      </div>
      <div className="flex items-center space-x-3">
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-slate-700 hover:bg-slate-600 text-white"
          onClick={onSave}
          disabled={isSaving}
        >
          {isSaving ? '保存中...' : '保存'}
        </Button>
        {/* <div className="bg-slate-700 px-3 py-1 rounded-md text-sm">
          <span>料金: ¥0.00</span> 
        </div> */}
        {/* 将来的にはここにユーザーアイコンやメニューなどを配置 */}
      </div>
    </header>
  );
};

export default TopBar; 
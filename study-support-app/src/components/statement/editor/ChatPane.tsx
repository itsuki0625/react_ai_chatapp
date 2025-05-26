'use client';

import React from 'react';

interface ChatPaneProps {
  draftId?: string;
  // 他に必要なpropsがあれば追加 (例: messages, onSendMessage)
}

const ChatPane: React.FC<ChatPaneProps> = ({ draftId }) => {
  return (
    <div className="bg-slate-100 h-full overflow-y-auto p-4 flex flex-col">
      <h2 className="text-lg font-semibold mb-2">Chat Pane</h2>
      <div className="flex-grow border border-slate-300 rounded p-2 mb-2">
        {/* 将来的にはここにメッセージリストを表示 */}
        <p>ここにチャットメッセージが表示されます。</p>
        <p>現在はプレースホルダーです。</p>
      </div>
      <div className="mt-auto">
        {/* 将来的にはここにメッセージ入力欄を配置 */}
        <textarea 
          className="w-full p-2 border border-slate-300 rounded"
          rows={3}
          placeholder="メッセージを入力 (または / でコマンド入力)..."
        />
        <button className="mt-2 w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded">
          送信
        </button>
      </div>
    </div>
  );
};

export default ChatPane; 
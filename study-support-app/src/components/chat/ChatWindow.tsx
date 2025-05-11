'use client'; // このコンポーネントはクライアントサイドで動作

import React, { useEffect, useRef } from 'react';
import MessageList from './MessageList';
import { useChat } from '@/store/chat/ChatContext';
import { useSession } from 'next-auth/react';
import { ChatTypeEnum } from '@/types/chat'; // ChatTypeEnumをインポート

// ChatWindowProps はほぼ不要になるか、表示に関するオプションのみになる
// interface ChatWindowProps {
//   // chatType?: ChatTypeValue; // Contextから取得
//   // sessionId?: string;    // Contextから取得
// }

const ChatWindow: React.FC<{/* ChatWindowProps */}> = (/*props*/) => {
  const {
    messages,
    isLoading, 
    error,
    sessionId,
    currentChatType,
    fetchMessages, // fetchMessages を useChat から取得
  } = useChat();

  const { data: authSession, status: authStatus } = useSession();
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    // MessageListコンポーネントの末尾にスクロール要素を配置する想定
    const scrollTarget = document.getElementById('messages-end-sentinel');
    if (scrollTarget) {
        scrollTarget.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 履歴読み込みロジック (セッションIDが設定され、メッセージがまだない場合)
  // ChatProvider側でセッションID変更時に履歴を読み込むのが理想だが、
  // ここで明示的にトリガーすることも一時的な手段としてあり得る。
  // ただし、無限ループを避けるための条件やフラグ管理が重要。
  useEffect(() => {
    if (sessionId && messages.length === 0 && authStatus === 'authenticated' && !isLoading) {
      console.log(`ChatWindow: sessionId ${sessionId} detected with no messages. Attempting to load history via fetchMessages.`);
      fetchMessages(sessionId); // ★★★ fetchMessages を呼び出す ★★★
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, messages.length, authStatus, isLoading, fetchMessages]); // fetchMessages を依存配列に追加


  if (authStatus === 'loading') {
    return (
      <div className="flex flex-col flex-1 items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="mt-2 text-muted-foreground">認証情報を確認中...</p>
      </div>
    );
  }
  if (authStatus === 'unauthenticated') {
    return (
      <div className="flex flex-col flex-1 items-center justify-center p-4">
        <p className="text-muted-foreground">チャットを利用するにはログインしてください。</p>
      </div>
    );
  }

  if (isLoading && messages.length === 0 && sessionId) {
    return (
      <div className="flex flex-col flex-1 items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="mt-2 text-muted-foreground">会話履歴を読み込み中...</p>
      </div>
    );
  }
  
  // セッションが開始されていない、またはメッセージが空の場合の表示
  if (!sessionId && messages.length === 0) {
    let welcomeMessage = "チャットへようこそ！";
    switch(currentChatType) {
        case ChatTypeEnum.SELF_ANALYSIS:
            welcomeMessage = "自己分析チャットへようこそ！あなたのことについて教えてください。";
            break;
        case ChatTypeEnum.ADMISSION:
            welcomeMessage = "入試相談チャットへようこそ！入試に関する質問にお答えします。";
            break;
        // 他のチャットタイプのウェルカムメッセージ
    }
    return (
      <div className="flex flex-col flex-1 items-center justify-center p-6 text-center">
        <h2 className="text-xl font-semibold mb-3">{welcomeMessage}</h2>
        <p className="text-muted-foreground">
          サイドバーから過去のセッションを選択するか、下の入力欄から新しいメッセージを送信してチャットを開始してください。
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden h-full"> 
      {error && (
        <div className="p-3 bg-red-100 text-red-700 text-sm text-center sticky top-0 z-10 shadow-sm">
          エラー: {typeof error === 'string' ? error : error.message} 
        </div>
      )}
      <MessageList />
      {/* messagesEndRefはMessageListコンポーネントの最後に配置する想定 */} 
    </div>
  );
};

export default ChatWindow; 
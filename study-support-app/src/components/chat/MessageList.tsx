import React, { useRef, useEffect } from 'react';
import ChatMessageItemDisplay from './ChatMessage';
import { useChat } from '@/store/chat/ChatContext'; // useChat をインポート
// import { ChatMessage as FrontendChatMessage } from '@/types/chat'; // 不要になるのでコメントアウトまたは削除

// interface MessageListProps {
//   messages: FrontendChatMessage[]; // useChatから取得するため不要
//   // isLoading?: boolean; // グローバルなisLoadingはChatWindowで制御
// }

const MessageList: React.FC = () => { // Props を削除
  const { messages, isLoading, error } = useChat(); // useChat フックから状態を取得
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // エラー表示 (必要に応じて)
  if (error) {
    // errorオブジェクトが文字列の場合とオブジェクトの場合があるため、表示を調整
    const errorMessage = typeof error === 'string' ? error : (error as Error)?.message || '不明なエラーが発生しました';
    return <div className="p-4 text-red-500">エラー: {errorMessage}</div>;
  }
  
  // AIが現在ストリーミング中かどうかを判定 (主にデバッグ用、UIはChatMessageItemが行う)
  // const isAiStreaming = messages.some(msg => msg.sender === 'AI' && msg.isStreaming);
  // console.log("Is AI Streaming (in MessageList)?", isAiStreaming);

  return (
    <div className="flex-1 overflow-y-auto p-4 pt-2 pb-6 space-y-3 bg-gray-50 scrollbar-thin scrollbar-thumb-blue-500 scrollbar-track-blue-100">
      {messages.map((message) => (
        <ChatMessageItemDisplay key={message.id} message={message} />
      ))}
      {/* 
        ローディングインジケータは、ChatMessageItemDisplay が個々のメッセージの 
        isLoading (ユーザーメッセージ送信中) や isStreaming (AI応答中) を見て表示する。
        または、ChatWindow で messages 配列が空で isLoading が true の場合に表示する。
      */}
      <div ref={messagesEndRef} style={{ height: '1px' }} /> {/* 自動スクロールのためのアンカー */}
    </div>
  );
};

export default MessageList; 
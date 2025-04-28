import React, { useRef, useEffect } from 'react';
import ChatMessage, { Message } from './ChatMessage'; // ChatMessageコンポーネントと型をインポート

interface MessageListProps {
  messages: Message[]; // 表示するメッセージの配列
  isLoading: boolean; // AI応答待ちなどのローディング状態
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null); // スクロール用のref

  // messages配列が更新されるたびに最下部にスクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-background">
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
      {/* ローディング中にインジケーターなどを表示 */}
      {isLoading && (
        <div className="flex justify-center items-center p-4">
          {/* AIアバターとローディングテキスト */}
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            {/* AIアバターアイコンはChatMessageから流用 */}
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-pulse"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
            <span>AIが応答を生成中...</span>
          </div>
        </div>
      )}
      {/* スクロール制御用の空div */}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList; 
import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"; // Shadcn/uiのAvatarを使用
import { cn } from "@/lib/utils"; // Shadcn/uiのユーティリティ関数

// メッセージオブジェクトの型定義 (APIスキーマに合わせて調整)
// backend/app/schemas/chat.py の ChatMessage スキーマに対応させる
export interface Message {
  id: number;
  session_id: string; // UUIDを使用するためstringに変更
  sender: 'user' | 'ai';
  content: string;
  created_at: string; // または Date 型
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={cn(
      "flex items-start space-x-3 mb-4",
      isUser ? "justify-end" : "justify-start"
    )}>
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          {/* TODO: AIアバター画像を適切に設定 */}
          <AvatarImage src="/icons/bot.svg" alt="AI" /> 
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      )}
      <div className={cn(
        "p-3 rounded-lg max-w-xs lg:max-w-md xl:max-w-lg break-words", // break-words を追加
        isUser ? "bg-primary text-primary-foreground" : "bg-muted"
      )}>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {/* 必要に応じてタイムスタンプなどを表示 */}
        {/* <p className="text-xs text-muted-foreground mt-1 text-right">{new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p> */}
      </div>
      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
           {/* TODO: ユーザーアバター。認証情報から取得するか、デフォルト表示 */}
          <AvatarImage src="/icons/user.svg" alt="User" />
          <AvatarFallback>You</AvatarFallback>
        </Avatar>
      )}
    </div>
  );
};

export default ChatMessage; 
import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"; // Shadcn/uiのAvatarを使用
import { cn } from "@/lib/utils"; // Shadcn/uiのユーティリティ関数
import { type ChatMessage as Message } from '@/types/chat'; // types/chat.ts からインポート
import { Loader2, AlertTriangle, User, Bot } from 'lucide-react'; // アイコンを追加

// ローカルのMessage型定義は削除

interface ChatMessageItemDisplayProps { // Props名を変更
  message: Message;
}

const ChatMessageItemDisplay: React.FC<ChatMessageItemDisplayProps> = ({ message }) => {
  const isUser = message.sender === 'USER';
  const isAI = message.sender === 'AI';

  return (
    <div className={cn(
      "flex items-start space-x-3 mb-4",
      isUser ? "justify-end" : "justify-start"
    )}>
      {isAI && ( // AIの場合のアバター
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarImage src="/icons/bot.svg" alt="AI" />
          <AvatarFallback><Bot size={18} /></AvatarFallback>
        </Avatar>
      )}
      <div className={cn(
        "p-3 rounded-lg max-w-xs lg:max-w-md xl:max-w-lg break-words shadow-sm",
        isUser ? "bg-primary text-primary-foreground" : "bg-card border",
        message.isError ? "bg-destructive/20 border-destructive text-destructive-foreground" : ""
      )}>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        
        {/* ユーザーメッセージの送信中 */}
        {isUser && message.isLoading && (
          <div className="flex items-center text-xs text-muted-foreground mt-1">
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            送信中...
          </div>
        )}

        {/* AIメッセージのストリーミング中 */}
        {isAI && message.isStreaming && (
          // ストリーミング中のテキスト色は、isUserでない場合の通常テキスト色に合わせるか、特定のアクセントカラーにする
          <div className="flex items-center text-xs text-muted-foreground mt-1"> 
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            応答生成中...
          </div>
        )}
        
        {/* エラー表示 (ユーザーメッセージ送信失敗 or AIエラー) */}
        {message.isError && (
          <div className="flex items-center text-xs text-destructive-foreground mt-1 opacity-90">
            <AlertTriangle className="mr-1 h-3 w-3" />
            エラーが発生しました。
          </div>
        )}

        {/* タイムスタンプ (必要に応じて表示) */}
        {/* <p className={cn("text-xs mt-1 text-right", isUser ? "text-primary-foreground/80" : "text-muted-foreground")}>{new Date(message.timestamp).toLocaleTimeString()}</p> */}
      </div>
      {isUser && ( // ユーザーの場合のアバター
        <Avatar className="h-8 w-8 flex-shrink-0">
          {/* <AvatarImage src="/icons/user.svg" alt="User" /> */} {/* ユーザーアバター画像があれば */} 
          <AvatarFallback><User size={18}/></AvatarFallback>
        </Avatar>
      )}
    </div>
  );
};

export default ChatMessageItemDisplay; // エクスポート名を変更 
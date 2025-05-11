import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"; // Shadcn/uiのAvatarを使用
import { cn } from "@/lib/utils"; // Shadcn/uiのユーティリティ関数
import { type ChatMessage as Message } from '@/types/chat'; // types/chat.ts からインポート
import { Loader2, AlertTriangle, User, Bot, Sparkles } from 'lucide-react'; // アイコンを追加

// ローカルのMessage型定義は削除

interface ChatMessageItemDisplayProps { // Props名を変更
  message: Message;
}

const ChatMessageItemDisplay: React.FC<ChatMessageItemDisplayProps> = ({ message }) => {
  const isUser = message.sender === 'USER';
  const isAI = message.sender === 'AI';

  return (
    <div className={cn(
      "flex items-start space-x-4 mb-6 animate-fadeIn",
      isUser ? "justify-end" : "justify-start"
    )}>
      {isAI && ( // AIの場合のアバター
        <Avatar className="h-10 w-10 flex-shrink-0 ring-2 ring-blue-100 bg-blue-50">
          <AvatarImage src="/icons/bot.svg" alt="AI" />
          <AvatarFallback>
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center w-full h-full rounded-full">
              <Sparkles size={20} className="text-white" />
            </div>
          </AvatarFallback>
        </Avatar>
      )}
      <div 
        className={cn(
          "p-4 rounded-2xl max-w-xs lg:max-w-md xl:max-w-lg break-words",
          "transition-all duration-200 ease-in-out",
          isUser 
            ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-md shadow-blue-500/10" 
            : "bg-white border border-slate-200 shadow-md shadow-slate-200/40",
          message.isError 
            ? "bg-red-50 border-red-200 text-red-800 shadow-red-500/10" 
            : ""
        )}
      >
        <p className={cn(
          "text-sm md:text-base whitespace-pre-wrap leading-relaxed",
          !isUser && "text-slate-800"
        )}>
          {message.content}
        </p>
        
        {/* ユーザーメッセージの送信中 */}
        {isUser && message.isLoading && (
          <div className="flex items-center text-xs text-blue-100 mt-2">
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            <span className="animate-pulse">送信中...</span>
          </div>
        )}

        {/* AIメッセージのストリーミング中 */}
        {isAI && message.isStreaming && (
          <div className="flex items-center text-xs text-blue-500 mt-2"> 
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            <span className="animate-pulse">回答を生成中...</span>
          </div>
        )}
        
        {/* エラー表示 (ユーザーメッセージ送信失敗 or AIエラー) */}
        {message.isError && (
          <div className="flex items-center text-xs text-red-600 mt-2 font-medium">
            <AlertTriangle className="mr-1 h-3 w-3" />
            エラーが発生しました
          </div>
        )}

        {/* タイムスタンプ (必要に応じて表示) */}
        <p className={cn(
          "text-xs mt-1 text-right opacity-80", 
          isUser ? "text-blue-100" : "text-slate-500"
        )}>
          {new Date(message.timestamp).toLocaleTimeString('ja-JP', {hour: '2-digit', minute:'2-digit'})}
        </p>
      </div>
      {isUser && ( // ユーザーの場合のアバター
        <Avatar className="h-10 w-10 flex-shrink-0 ring-2 ring-blue-200 bg-blue-50">
          <AvatarFallback>
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center w-full h-full rounded-full">
              <User size={20} className="text-white" />
            </div>
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
};

export default ChatMessageItemDisplay; // エクスポート名を変更 
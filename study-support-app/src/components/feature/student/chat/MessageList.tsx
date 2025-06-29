import React, { useRef, useEffect } from 'react';
import ChatMessageItemDisplay from './ChatMessage';
import { useChat } from '@/store/chat/ChatContext'; // useChat をインポート
// import { ChatMessage as FrontendChatMessage } from '@/types/chat'; // 不要になるのでコメントアウトまたは削除
import { AlertCircle, Loader2 } from 'lucide-react';

// interface MessageListProps {
//   messages: FrontendChatMessage[]; // useChatから取得するため不要
//   // isLoading?: boolean; // グローバルなisLoadingはChatWindowで制御
// }

const MessageList: React.FC = () => { // Props を削除
  const { messages, isLoading, error, traceLogs } = useChat(); // useChat フックから状態を取得
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // エラー表示
  if (error) {
    const errorMessage = typeof error === 'string' ? error : (error as Error)?.message || '不明なエラーが発生しました';
    return (
      <div className="flex items-center justify-center w-full h-full p-6 bg-red-50">
        <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-4 rounded-lg border border-red-200 shadow-sm max-w-md">
          <AlertCircle className="h-5 w-5" />
          <p className="text-sm font-medium">エラー: {errorMessage}</p>
        </div>
      </div>
    );
  }
  
  // AIが現在ストリーミング中かどうかを判定 (主にデバッグ用、UIはChatMessageItemが行う)
  // const isAiStreaming = messages.some(msg => msg.sender === 'AI' && msg.isStreaming);
  // console.log("Is AI Streaming (in MessageList)?", isAiStreaming);

  return (
    <div className="flex-1 overflow-y-auto h-full space-y-6 bg-white pb-40 p-4 pt-6 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-slate-100 scroll-smooth">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center pb-40">
          <div className="w-16 h-16 mb-4 rounded-full bg-blue-50 flex items-center justify-center">
            <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-2">会話を始めましょう</h3>
          <p className="text-slate-500 max-w-sm">下のフォームからメッセージを送信して、AIとの会話を開始できます。</p>
        </div>
      ) : (
        <>
          {/* AI思考中のTraceログ */}
          {traceLogs.length > 0 && (
            <div className="space-y-1">
              {traceLogs.map((log: string, i: number) => (
                <div key={`trace-${i}`} className="text-xs text-gray-500 whitespace-pre-wrap">
                  {log}
                </div>
              ))}
            </div>
          )}
          {messages.map((message) => (
            <ChatMessageItemDisplay key={message.id} message={message} />
          ))}

          {isLoading && messages.some(m => m.isStreaming) && (
            <div className="flex justify-center py-2">
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-blue-600 text-xs">
                <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                応答を生成中...
              </div>
            </div>
          )}
        </>
      )}
      <div ref={messagesEndRef} id="messages-end-sentinel" className="h-1" />
    </div>
  );
};

export default MessageList;
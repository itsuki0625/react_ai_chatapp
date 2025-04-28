// import React from 'react'; // Reactをインポート - 元のコードにはなかったので削除
import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChatType } from '@/types/chat';
import { Metadata } from 'next'; // Metadataをインポート

// ★ generateMetadata のコメントアウトを解除
interface ChatSessionPageProps { params: { sessionId: string; }; }
export async function generateMetadata({ params }: ChatSessionPageProps): Promise<Metadata> {
    // TODO: セッション情報を取得してタイトルなどを設定 (API呼び出しが必要)
    return { title: `自己分析チャット - ${params.sessionId.substring(0, 8)}...`, };
}

// ★ コンポーネントの中身を元に戻す
export default function ChatSessionPage({ params }: ChatSessionPageProps) { // 型を元に戻す
  const chatType = ChatType.SELF_ANALYSIS; // 元のコードを復元
  const { sessionId } = params; // 元のコードを復元

  return (
    // <div className="flex h-full w-full">
    //   <h1>Chat Session Page</h1>
    //   <p>Session ID: {params.sessionId}</p>
    //   <p>(Simplified Test)</p>
    // </div>
    <div className="flex h-full w-full"> {/* 元のコードを復元 */} 
      <ChatSidebar chatType={chatType} currentSessionId={sessionId} />
      <div className="flex-1 flex flex-col">
        {/* sessionId を渡して既存チャットモードにする */}
        <ChatWindow chatType={chatType} sessionId={sessionId} />
      </div>
    </div>
  );
} 
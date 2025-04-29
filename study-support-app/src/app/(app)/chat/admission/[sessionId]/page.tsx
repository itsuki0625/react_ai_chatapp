// 最小限の構成でテスト

// import ChatSidebar from '@/components/chat/ChatSidebar';
// import ChatWindow from '@/components/chat/ChatWindow';
// import { ChatType } from '@/types/chat';
// import { Metadata } from 'next';

// export async function generateMetadata({ params }: { params: { sessionId: string } }): Promise<Metadata> {
//     return {
//         title: `総合型選抜チャット - ${params.sessionId.substring(0, 8)}...`,
//     };
// }

export default function ChatSessionPage({ params }: { params: { sessionId: string } }) {
  // const chatType = ChatType.ADMISSION;
  const { sessionId } = params;

  return (
    <div>
      <h1>Chat Session (Admission)</h1>
      <p>Session ID: {sessionId}</p>
      {/* <div className="flex h-full w-full">
        <ChatSidebar chatType={chatType} currentSessionId={sessionId} />
        <div className="flex-1 flex flex-col">
          <ChatWindow chatType={chatType} sessionId={sessionId} />
        </div>
      </div> */}
    </div>
  );
} 
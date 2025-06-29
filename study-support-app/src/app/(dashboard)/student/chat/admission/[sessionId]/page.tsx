import ChatSidebar from '@/components/feature/student/chat/ChatSidebar';
import ChatWindow from '@/components/feature/student/chat/ChatWindow';
import { ChatTypeEnum, type ChatSession, type ChatTypeValue } from '@/types/chat';
import { Metadata } from 'next';
// import { getServerSession } from "next-auth/next"; // または "next-auth"
import { auth } from "@/auth"; 
import ChatPage from '@/components/feature/student/chat/ChatPage';

// APIからチャットセッション情報を取得する関数
async function getChatSession(sessionId: string, accessToken: string | undefined): Promise<ChatSession | null> {
  if (!accessToken) {
    console.error('Access token not available for fetching chat session.');
    return null;
  }

  try {
    // NEXT_PUBLIC_API_BASE_URL がブラウザ用なので、サーバーサイドでは INTERNAL_API_BASE_URL を優先的に使用する
    const baseUrl = process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!baseUrl) {
      console.error('API base URL is not defined.');
      return null;
    }
    const response = await fetch(
      `${baseUrl}/api/v1/chat/sessions/${sessionId}`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`, 
          'Content-Type': 'application/json',
        },
        // サーバーサイドフェッチでは cache オプションを指定することが推奨される
        cache: 'no-store', // または 'force-cache', 'default' など、適切なキャッシュ戦略を選択
      }
    );

    if (!response.ok) {
      console.error(`Failed to fetch chat session ${sessionId}: ${response.status}, ${await response.text()}`);
      return null;
    }
    const data: ChatSession = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching chat session ${sessionId}:`, error);
    return null;
  }
}

interface ChatSessionPageProps {
  params: {
    sessionId: string;
  };
}

export async function generateMetadata(
  { params }: ChatSessionPageProps
): Promise<Metadata> {
  return {
    title: `総合型選抜チャットセッション - ${params.sessionId.substring(0, 8)}...`,
  };
}

export default function AdmissionChatSessionPage({ params }: ChatSessionPageProps) {
  return (
    <ChatPage
      initialChatType={ChatTypeEnum.ADMISSION}
      initialSessionId={params.sessionId}
    />
  );
} 
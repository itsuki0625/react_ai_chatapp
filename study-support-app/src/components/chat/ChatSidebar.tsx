'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
// import { usePathname } from 'next/navigation'; // 未使用
import { useSession } from 'next-auth/react';
import { apiClient } from '@/lib/api-client';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
// import { PlusCircle, Archive } from 'lucide-react'; // Archive は未使用
import { PlusCircle, ChevronLeft, ChevronRight } from 'lucide-react';
// import { cn } from "@/lib/utils"; // 未使用
import { ChatType } from '@/types/chat';

// APIから取得するセッションリストの型 (要調整)
interface ChatSessionSummary {
  id: string; // UUID は文字列として扱う
  title: string | null;
  chat_type: ChatType;
  updated_at: string; // または Date
}

interface ChatSidebarProps {
  chatType: ChatType;
  currentSessionId?: string; // 現在表示中のセッションID (パスから取得)
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({ chatType, currentSessionId }) => {
  const { data: session, status } = useSession();
  // const pathname = usePathname(); // 未使用
  const [activeSessions, setActiveSessions] = useState<ChatSessionSummary[]>([]);
  // const [archivedSessions, setArchivedSessions] = useState<ChatSessionSummary[]>([]); // 必要ならアーカイブも取得
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(true);

  // 画面サイズに応じてサイドバーの初期状態を設定
  useEffect(() => {
    const checkScreenSize = () => {
      setIsOpen(window.innerWidth >= 768); // 768px以上で開いた状態
    };

    // 初期表示時に実行
    checkScreenSize();

    // リサイズ時に実行
    window.addEventListener('resize', checkScreenSize);

    // クリーンアップ
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  const token = session?.accessToken;

  useEffect(() => {
    const fetchSessions = async () => {
      if (status !== 'authenticated' || !token) return;
      setIsLoading(true);
      setError(null);
      try {
        // アクティブなセッションを取得 (APIエンドポイントとパラメータは要確認)
        const response = await apiClient.get<ChatSessionSummary[]>(`/api/v1/chat/sessions`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { chat_type: chatType, status: 'ACTIVE' }
        });
        // chatTypeでフィルタリング (APIが対応していない場合)
        const filteredSessions = response.data.filter(s => s.chat_type === chatType);
        setActiveSessions(filteredSessions.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())); // 更新日時で降順ソート

        // アーカイブ済みセッションも取得する場合
        // const archivedResponse = await apiClient.get<ChatSessionSummary[]>(`/api/v1/chat/sessions/archived`, { ... });
        // setArchivedSessions(archivedResponse.data.filter(s => s.chat_type === chatType));

      } catch (err: unknown) {
        console.error("Error fetching sessions:", err);
        setError("会話履歴の取得に失敗しました。");
        setActiveSessions([]);
        // setArchivedSessions([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
  }, [status, token, chatType]); // chatTypeが変わっても再取得

  const getChatTypeName = (type: ChatType): string => {
    switch (type) {
      case ChatType.SELF_ANALYSIS: return "自己分析";
      case ChatType.ADMISSION: return "総合型選抜";
      case ChatType.STUDY_SUPPORT: return "学習支援";
      default: return "チャット";
    }
  };

  return (
    <div className={`relative flex flex-col h-full transition-all duration-300 ${isOpen ? 'w-64' : 'w-12'}`}>
      <div className={`border-r bg-card text-card-foreground flex flex-col h-full transition-all duration-300 ${isOpen ? 'w-64' : 'w-12'}`}>
        <div className="p-4 border-b flex items-center">
          {isOpen && <h2 className="text-lg font-semibold flex-1">{getChatTypeName(chatType)}</h2>}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 hover:bg-accent rounded-md transition-colors"
            style={{ marginLeft: isOpen ? '0.5rem' : '0' }}
          >
            {isOpen ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        </div>
        {isOpen && (
          <>
            <div className="p-2">
              <Button asChild variant="outline" className="w-full justify-start">
                <Link href={`/chat/${chatType}`}>
                  <PlusCircle className="mr-2 h-4 w-4" />
                  新しいチャット
                </Link>
              </Button>
            </div>
            <ScrollArea className="flex-1 px-2">
              <div className="space-y-1 py-2">
                <h3 className="text-xs font-semibold text-muted-foreground px-2 mb-1">最近のチャット</h3>
                {isLoading && <p className="text-xs text-muted-foreground px-2">読み込み中...</p>}
                {error && <p className="text-xs text-destructive px-2">{error}</p>}
                {!isLoading && activeSessions.length === 0 && !error && (
                  <p className="text-xs text-muted-foreground px-2">履歴はありません</p>
                )}
                {activeSessions.map((sess) => (
                  <Button
                    key={sess.id}
                    asChild
                    variant={currentSessionId === sess.id ? "secondary" : "ghost"}
                    className="w-full justify-start h-auto py-2 px-2 text-sm truncate"
                  >
                    <Link href={`/chat/${chatType}/${sess.id}`} title={sess.title || '無題のチャット'}>
                      {sess.title || '無題のチャット'}
                    </Link>
                  </Button>
                ))}
              </div>
            </ScrollArea>
          </>
        )}
      </div>
    </div>
  );
};

export default ChatSidebar;

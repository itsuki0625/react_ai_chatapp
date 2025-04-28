'use client'; // このコンポーネントはクライアントサイドで動作

import React, { useState, useEffect, useCallback } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { Message } from './ChatMessage'; // Message型をインポート
import { useSession } from 'next-auth/react'; // useSession をインポート
import { apiClient } from '@/lib/api-client'; // APIクライアント (ファイル名に合わせて修正)
import { ChatType } from '@/types/chat'; // ChatType をインポート (import type ではない)
import { useRouter } from 'next/navigation'; // ★ router をインポート

interface ChatWindowProps {
  chatType: ChatType;
  sessionId?: string; // ★ sessionId を string 型 (UUID) で受け取る (パスパラメータから)
}

// UUIDから数値IDを生成する関数 (不要になったため削除)
// const generateNumericIdFromUUID = (uuid: string): number => { ... };

const ChatWindow: React.FC<ChatWindowProps> = ({ chatType, sessionId: propSessionId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(propSessionId || null);
  // const [numericSessionId, setNumericSessionId] = useState<number | null>(...); // numericSessionId 関連を削除
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingHistory, setIsFetchingHistory] = useState(false); // 履歴取得中フラグ
  const [error, setError] = useState<string | null>(null);
  const { data: session, status } = useSession(); // useSession を使用
  const router = useRouter(); // ★ router インスタンスを取得

  const token = session?.accessToken; // セッションからトークンを取得
  const user = session?.user; // セッションからユーザー情報を取得

  useEffect(() => {
    setCurrentSessionId(propSessionId || null);
    // setNumericSessionId(...) を削除
    if (!propSessionId) {
      setMessages([]);
    }
  }, [propSessionId]);

  const fetchMessages = useCallback(async (sid: string) => {
    if (!sid || !token) return;
    setIsFetchingHistory(true); // 履歴取得開始
    setError(null);
    try {
      // API呼び出しでUUIDをそのまま使用
      const response = await apiClient.get<Message[]>(`/api/v1/chat/sessions/${sid}/messages/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages(response.data);
    } catch (err: any) {
      console.error("Error fetching messages:", err);
      setError(`メッセージの読み込みに失敗しました: ${err.response?.data?.detail || err.message}`);
      setMessages([]); // エラー時はメッセージをクリア
    } finally {
      setIsFetchingHistory(false); // 履歴取得完了
    }
  }, [token]);

  // セッションIDが確定したらメッセージを読み込む
  useEffect(() => {
    if (currentSessionId) {
      fetchMessages(currentSessionId);
    } else {
      // 初回アクセス時など、セッションIDがない場合はメッセージを空にする
      setMessages([]);
    }
  }, [currentSessionId, fetchMessages]);

  // メッセージ送信処理
  const handleSendMessage = async (content: string) => {
    if (status !== 'authenticated' || !token) {
      setError("メッセージを送信するにはログインが必要です。");
      return;
    }
    setIsLoading(true); // AI応答待ち開始
    setError(null);

    let targetSessionId = currentSessionId;
    // let targetNumericId = numericSessionId; // numericId 関連を削除
    let userMessage: Message | null = null; // Optimistic update 用

    try {
      // 1. セッションがない場合は、まず新しいセッションを作成
      if (!targetSessionId) {
        console.log(`Creating new session with type: ${chatType}...`); // ★ chatType をログに出力
        const sessionResponse = await apiClient.post<{ id: string }>(`/api/v1/chat/sessions/`, 
            { chat_type: chatType }, // ★ chatType を使用
            {
                headers: { Authorization: `Bearer ${token}` },
            });
        targetSessionId = sessionResponse.data.id;
        // targetNumericId = generateNumericIdFromUUID(targetSessionId); // numericId 関連を削除
        setCurrentSessionId(targetSessionId); // 新しいセッションIDをstateに保存
        // setNumericSessionId(targetNumericId); // numericId 関連を削除
        setMessages([]); // 新しいセッションなのでメッセージリストをクリア
        console.log("New session created with ID:", targetSessionId);
        // ★ 新規作成後、URLを更新
        router.push(`/chat/${chatType}/${targetSessionId}`);
      }

      if (!targetSessionId) { // numericId のチェックを削除
          throw new Error("セッションの作成または取得に失敗しました。画面をリロードしてください。");
      }

      // 2. ユーザーメッセージを optimistic update で追加
      userMessage = {
        id: Math.random(), // 仮の数値ID (より安全な方法を検討)
        session_id: targetSessionId, // UUIDをそのまま文字列として保存
        sender: 'user',
        content: content,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage!]);

      // 3. APIにメッセージを送信し、AIの応答を取得
      console.log(`Sending message to session ${targetSessionId}:`, content); // numericId のログを削除
      const response = await apiClient.post<Message>(`/api/v1/chat/sessions/${targetSessionId}/messages/`, // API呼び出しでUUIDをそのまま使用
        { content: content }, // 送信するデータ (ChatMessageCreate)
        { headers: { Authorization: `Bearer ${token}` } }
      );

      console.log("Received AI response:", response.data);

      // 4. APIからのAI応答メッセージでリストを更新
      setMessages((prev) => {
        // 仮のユーザーメッセージを削除し、実際のAI応答を追加
        const optimisticFiltered = prev.filter(msg => msg.id !== userMessage!.id);
        // バックエンドがAI応答のみを返す場合
        return [...optimisticFiltered, response.data]; 
        // もしバックエンドがユーザーメッセージとAI応答を含むリストを返すなら↓
        // return response.data; // または適切な処理
      });

    } catch (err: any) {
      console.error("Error sending message:", err);
      setError(`メッセージの送信に失敗しました: ${err.response?.data?.detail || err.message}`);
      // エラーが起きた場合、optimistic update したメッセージを削除
      if (userMessage) {
         setMessages((prev) => prev.filter(msg => msg.id !== userMessage!.id));
      }
    } finally {
      setIsLoading(false); // AI応答待ち終了
    }
  };

  // NextAuth の認証状態を確認する
  if (status === 'loading') {
    return (
      <div className="flex flex-col h-[calc(100vh-var(--header-height,60px))] border rounded-lg overflow-hidden bg-card shadow-sm items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="mt-2 text-muted-foreground">認証情報を確認中...</p>
      </div>
    );
  }

  // 認証されていない場合（または initialSessionId がなく、履歴取得中より前の場合）
  if (status === 'unauthenticated') {
      return (
          <div className="flex flex-col h-[calc(100vh-var(--header-height,60px))] border rounded-lg overflow-hidden bg-card shadow-sm items-center justify-center">
              <p className="text-muted-foreground">チャットを開始するにはログインしてください。</p>
              {/* 必要に応じてログインボタンなどを表示 */}
          </div>
      );
  }

  // 初期ロード中または履歴取得中の表示
  if (isFetchingHistory && messages.length === 0 && currentSessionId /* sessionIdがある場合のみ履歴表示 */) {
     return (
      <div className="flex flex-col h-[calc(100vh-var(--header-height,60px))] border rounded-lg overflow-hidden bg-card shadow-sm items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="mt-2 text-muted-foreground">会話履歴を読み込み中...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-var(--header-height,60px))] border rounded-lg overflow-hidden bg-card shadow-sm">
      {error && (
        <div className="p-2 bg-destructive text-destructive-foreground text-xs sm:text-sm text-center">
          エラー: {error}
        </div>
      )}

      {/* メッセージリスト */} 
      <MessageList messages={messages} isLoading={isLoading && !!currentSessionId /* 既存セッションの応答待ちのみisLoading */} /> {/* ローディングは入力欄側で制御するのでMessageListからはisLoadingを渡さない変更も検討 */} 

      {/* メッセージ入力 */} 
      <MessageInput onSendMessage={handleSendMessage} isLoading={isLoading} /> 
    </div>
  );
};

export default ChatWindow; 
"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, SendHorizontal } from 'lucide-react';
import ChatSidebar from '@/components/chat/ChatSidebar';
import ChatWindow from '@/components/chat/ChatWindow';
import { ChecklistEvaluation } from './ChecklistEvaluation';
import {
    sendMessageStream,
} from '@/services/chatService';
import { ChatMessage, ChatType } from '@/types/chat';
import { useAuthHelpers } from '@/lib/authUtils';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useRouter } from 'next/navigation';

const ChatPage: React.FC = () => {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [newMessage, setNewMessage] = useState('');
  const checklistRef = useRef<{ triggerUpdate: () => void }>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>(undefined);
  const { hasPermission, isLoading: isAuthLoading } = useAuthHelpers();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatType = ChatType.STUDY_SUPPORT; // このチャットページのタイプを指定

  const canSendMessage = hasPermission('chat_message_send');

  // ChatWindow でセッションが作成されたときに呼び出されるコールバック
  const handleSessionCreated = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    // 新しいセッションIDがURLに反映されるよう更新
    if (sessionId) {
      router.push(`/chat/${chatType}/${sessionId}`);
    }
  };

  // サイドバーでセッションを選択したときのハンドラ
  useEffect(() => {
    // 初期ロード時やURLからセッションIDを取得する処理などを実装できる
    // 現在は主にChatWindowとChatSidebarのために定義
  }, []);

  // メッセージ送信 Mutation は ChatWindow 内部に移動する可能性が高いが、一旦残す
  const sendMessageMutation = useMutation<void, Error, { sessionId: string; message: string }>({
    mutationFn: async ({ sessionId, message }) => {
      // Optimistic update: Add user message immediately
      const optimisticMessage: ChatMessage = {
        id: `temp-user-${Date.now()}`,
        session_id: sessionId,
        content: message,
        sender_type: 'USER',
        created_at: new Date().toISOString(),
      };
      queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
        old ? [...old, optimisticMessage] : [optimisticMessage]
      );

      // Optimistic update: Add AI placeholder message
      const aiPlaceholder: ChatMessage = {
        id: `temp-ai-${Date.now()}`,
        session_id: sessionId,
        content: '', // Initially empty
        sender_type: 'AI',
        created_at: new Date().toISOString(),
        isLoading: true, // Indicate loading
      };
      queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
        old ? [...old, aiPlaceholder] : [aiPlaceholder]
      );

      let streamedContent = '';
      try {
        // Call the streaming API function
        await sendMessageStream(sessionId, message, (chunk: string) => {
          streamedContent += chunk;
          // Update the placeholder message with the streamed content
          queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
            old?.map(msg =>
              msg.id === aiPlaceholder.id ? { ...msg, content: streamedContent } : msg
            )
          );
        });
        // Update the placeholder message once streaming is complete
        queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
          old?.map(msg =>
            msg.id === aiPlaceholder.id ? { ...msg, isLoading: false } : msg
          )
        );
        // Trigger checklist update if necessary
        checklistRef.current?.triggerUpdate();
      } catch (error) {
        console.error("Streaming failed:", error);
        // Update placeholder message to show error
        queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
          old?.map(msg =>
            msg.id === aiPlaceholder.id ? { ...msg, content: "AI応答の取得中にエラーが発生しました。", isLoading: false, isError: true } : msg
          )
        );
        throw error; // Re-throw error to be caught by mutation's onError
      }
    },
    onError: (error, variables) => {
      console.error("Send message error:", error);
      alert(`メッセージ送信エラー: ${error.message}`);
      // Remove optimistic messages on error
      queryClient.setQueryData<ChatMessage[]>(['chatMessages', variables.sessionId], (old) =>
        old?.filter(msg => !msg.id?.startsWith('temp-'))
      );
    },
    // onSettledでは未使用の引数を削除
    onSettled: () => {
      // Invalidate session list to potentially update titles or order
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
    }
  });

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || sendMessageMutation.isPending || isAuthLoading || !canSendMessage) return;

    if (selectedSessionId) {
      sendMessageMutation.mutate({ sessionId: selectedSessionId, message: newMessage });
      setNewMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'; // Reset textarea height
      }
    } else {
       // セッション未選択時の処理 - 新規作成は ChatWindow に任せる想定
       console.log("No session selected, sending message to ChatWindow for new session creation potentially.");
       // ここで直接アラートを出すか、ChatWindowに処理を委譲するかは設計次第
       // alert('チャットセッションを選択してください。');
    }
  };

  const isLoadingMessages = false; // 仮置き (ChatWindowから取得する)

  return (
    <div className="flex h-full">
      {/* ChatSidebar にセッション選択ハンドラを渡す */}
      <ChatSidebar
        chatType={chatType}
        currentSessionId={selectedSessionId}
      />
      <div className="flex-1 flex flex-col border-l">
        {/* ChatWindow は sessionId を受け取り、内部でメッセージ取得と表示を行う */}
        <ChatWindow
            chatType={chatType}
            sessionId={selectedSessionId} // Pass selectedSessionId
            key={selectedSessionId} // Session ID 変更時にコンポーネントを再マウントして内部状態をリセット
            onNewSessionCreated={handleSessionCreated} // handleSessionCreatedを使用
        />

        {/* メッセージ入力欄は selectedSessionId がある場合のみ表示する、または ChatWindow内に移動する */}
        {/* selectedSessionId && ( */}
          <footer className="flex-none bg-white border-t border-gray-200 px-4 py-4">
            <form onSubmit={handleSendMessage} className="flex space-x-4 items-start">
              <Textarea
                ref={textareaRef}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder={canSendMessage ? "メッセージを入力... (Shift+Enterで改行)" : "メッセージを送信する権限がありません"}
                rows={1}
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[40px] max-h-[200px] overflow-y-auto disabled:cursor-not-allowed disabled:opacity-50"
                disabled={isLoadingMessages || sendMessageMutation.isPending || isAuthLoading || !canSendMessage || !selectedSessionId /* セッション未選択時も無効化 */}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
              />
              <Button
                type="submit"
                disabled={!newMessage.trim() || isLoadingMessages || sendMessageMutation.isPending || isAuthLoading || !canSendMessage || !selectedSessionId /* セッション未選択時も無効化 */}
                className="h-[40px] w-[40px] flex-shrink-0 flex items-center justify-center bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:bg-blue-400"
                size="icon"
              >
                {sendMessageMutation.isPending ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <SendHorizontal className="h-5 w-5" />
                )}
              </Button>
            </form>
          </footer>
        {/* ) */}
      </div>
      {/* Checklist Evaluation Panel */}
      {selectedSessionId && (
        <div className="w-80 border-l bg-gray-50 p-4 overflow-y-auto">
          <ChecklistEvaluation
            ref={checklistRef}
            chatId={selectedSessionId} // Use selectedSessionId
            sessionType={ChatType.GENERAL} // Update to use GENERAL from the ChatType enum
          />
        </div>
      )}
    </div>
  );
};

export default ChatPage;
"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, User, Bot, MoreVertical, Archive, RotateCcw, Loader2, SendHorizontal } from 'lucide-react';
import { Menu } from '@headlessui/react';
import { ChecklistEvaluation } from './ChecklistEvaluation';
import { ChatSidebar } from './ChatSidebar';
import { ChatMessages } from './ChatMessages';
import {
    getChatSessions,
    getArchivedChatSessions,
    getChatMessages,
    archiveChatSession,
    sendMessageStream,
} from '@/services/chatService';
import { ChatSession, ChatMessage } from '@/types/chat';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthHelpers } from '@/lib/authUtils';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

const ChatPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const checklistRef = useRef<{ triggerUpdate: () => void }>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [isArchivedView, setIsArchivedView] = useState(false);
  const { hasPermission, isLoading: isAuthLoading } = useAuthHelpers();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSendMessage = hasPermission('chat_message_send');

  const sessionsQuery = useQuery<ChatSession[], Error>({
    queryKey: ['chatSessions', 'active', isArchivedView],
    queryFn: () => getChatSessions("CONSULTATION"),
    enabled: !isArchivedView,
  });

  const archivedSessionsQuery = useQuery<ChatSession[], Error>({
    queryKey: ['chatSessions', 'archived', isArchivedView],
    queryFn: () => getArchivedChatSessions("CONSULTATION"),
    enabled: isArchivedView,
  });

  const messagesQuery = useQuery<ChatMessage[], Error>({
    queryKey: ['chatMessages', selectedSessionId],
    queryFn: () => getChatMessages(selectedSessionId!),
    enabled: !!selectedSessionId,
  });

  const archiveMutation = useMutation<ChatSession, Error, string>({
    mutationFn: archiveChatSession,
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions', 'active'] });
      queryClient.invalidateQueries({ queryKey: ['chatSessions', 'archived'] });
      if (selectedSessionId === variables) {
        setSelectedSessionId(null);
      }
      alert('セッションをアーカイブしました。');
    },
    onError: (error) => {
      console.error('Error archiving session:', error);
      alert(`アーカイブに失敗しました: ${error.message}`);
    },
  });

  const sendMessageMutation = useMutation<void, Error, { sessionId: string; message: string }>({
    mutationFn: async ({ sessionId, message }) => {
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

      const aiPlaceholder: ChatMessage = {
        id: `temp-ai-${Date.now()}`,
        session_id: sessionId,
        content: '',
        sender_type: 'AI',
        created_at: new Date().toISOString(),
        isLoading: true,
      };
      queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
        old ? [...old, aiPlaceholder] : [aiPlaceholder]
      );

      let streamedContent = '';
      try {
        await sendMessageStream(sessionId, message, (chunk: string) => {
          streamedContent += chunk;
          queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
            old?.map(msg =>
              msg.id === aiPlaceholder.id ? { ...msg, content: streamedContent } : msg
            )
          );
        });
        queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
          old?.map(msg =>
            msg.id === aiPlaceholder.id ? { ...msg, isLoading: false } : msg
          )
        );
        checklistRef.current?.triggerUpdate();
      } catch (error) {
        console.error("Streaming failed:", error);
        queryClient.setQueryData<ChatMessage[]>(['chatMessages', sessionId], (old) =>
          old?.map(msg =>
            msg.id === aiPlaceholder.id ? { ...msg, content: "エラー応答", isLoading: false, isError: true } : msg
          )
        );
        throw error;
      }
    },
    onError: (error, variables) => {
      console.error("Send message error:", error);
      alert(`メッセージ送信エラー: ${error.message}`);
      queryClient.setQueryData<ChatMessage[]>(['chatMessages', variables.sessionId], (old) =>
        old?.filter(msg => !msg.id?.startsWith('temp-'))
      );
    },
    onSettled: (data, error, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
    }
  });

  const handleSelectSession = (sessionId: string) => {
    setSelectedSessionId(sessionId);
  };

  const handleToggleArchiveView = (archived: boolean) => {
    setIsArchivedView(archived);
    setSelectedSessionId(null);
  };

  const handleArchiveSession = (sessionId: string) => {
    if (confirm('このセッションをアーカイブしますか？')) {
      archiveMutation.mutate(sessionId);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || sendMessageMutation.isPending || isAuthLoading || !canSendMessage) return;

    if (selectedSessionId) {
      sendMessageMutation.mutate({ sessionId: selectedSessionId, message: newMessage });
      setNewMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } else {
      alert('チャットセッションを選択してください。');
    }
  };

  useEffect(() => {
    if (messagesQuery.data && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messagesQuery.data]);

  const currentSessions = isArchivedView ? archivedSessionsQuery.data : sessionsQuery.data;
  const isLoadingSessions = isArchivedView ? archivedSessionsQuery.isLoading : sessionsQuery.isLoading;
  const currentMessages = messagesQuery.data;
  const isLoadingMessages = messagesQuery.isLoading;

  return (
    <div className="flex h-full">
      <ChatSidebar
        sessions={currentSessions ?? []}
        selectedSessionId={selectedSessionId}
        onSelectSession={handleSelectSession}
        isArchivedView={isArchivedView}
        onToggleArchiveView={handleToggleArchiveView}
        onArchiveSession={handleArchiveSession}
        isLoading={isLoadingSessions}
      />
      <div className="flex-1 flex flex-col border-l">
        {selectedSessionId ? (
          <>
            <ChatMessages
              messages={currentMessages ?? []}
              isLoading={isLoadingMessages}
              error={messagesQuery.error}
              messagesEndRef={messagesEndRef as React.RefObject<HTMLDivElement>}
            />
            <footer className="flex-none bg-white border-t border-gray-200 px-4 py-4">
              <form onSubmit={handleSendMessage} className="flex space-x-4 items-start">
                <Textarea
                  ref={textareaRef}
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder={canSendMessage ? "メッセージを入力... (Shift+Enterで改行)" : "メッセージを送信する権限がありません"}
                  rows={1}
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[40px] max-h-[200px] overflow-y-auto disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={isLoadingMessages || sendMessageMutation.isPending || isAuthLoading || !canSendMessage}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                />
                <Button
                  type="submit"
                  disabled={!newMessage.trim() || isLoadingMessages || sendMessageMutation.isPending || isAuthLoading || !canSendMessage}
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
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-muted-foreground">チャットセッションを選択してください。</p>
          </div>
        )}
      </div>
      {selectedSessionId && (
        <div className="w-80 border-l bg-gray-50 p-4 overflow-y-auto">
          <ChecklistEvaluation
            ref={checklistRef}
            chatId={selectedSessionId}
            sessionType="CONSULTATION"
          />
        </div>
      )}
    </div>
  );
};

export default ChatPage;
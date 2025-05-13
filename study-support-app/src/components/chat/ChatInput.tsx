'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SendHorizontal, Loader2 } from 'lucide-react';
import { useAuthHelpers } from '@/lib/authUtils';
import { useChat } from '@/store/chat/ChatContext';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean; // 外部から渡されるローディング状態
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading = false }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { hasPermission, isLoading: isAuthLoading } = useAuthHelpers();
  const { isConnected, viewingSessionStatus } = useChat();

  // Check for message sending permission
  const canSendMessage = hasPermission('chat_message_send');
  const isDisabled = !isConnected || isLoading || isAuthLoading || !canSendMessage || viewingSessionStatus === 'ARCHIVED';
  
  const getPlaceholder = () => {
    if (!isConnected) return "接続していません...";
    if (!canSendMessage) return "メッセージを送信する権限がありません";
    if (viewingSessionStatus === 'ARCHIVED') return "アーカイブされたチャットです (読み取り専用)";
    return "メッセージを入力... (Shift+Enterで改行)";
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(event.target.value);
    // Auto-resize textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleSend = useCallback(() => {
    // Send only if not disabled and message is not empty
    if (message.trim() && !isDisabled) {
      onSendMessage(message.trim());
      setMessage(''); // Clear input
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'; // Reset height
      }
    }
  }, [message, isDisabled, onSendMessage]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (but not Shift+Enter)
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="flex items-end space-x-2">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={getPlaceholder()}
          rows={1}
          className="flex-1 resize-none max-h-40 overflow-y-auto rounded-full border border-slate-200 bg-white px-3 py-3 text-sm ring-offset-background placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 shadow-sm min-h-[48px]"
          disabled={isDisabled}
        />
        <Button 
          type="button" 
          onClick={handleSend} 
          disabled={isDisabled || !message.trim()}
          size="icon"
          className="flex-shrink-0 bg-blue-600 hover:bg-blue-700 text-white shadow-sm h-10 w-10 rounded-full"
          aria-label="メッセージを送信"
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <SendHorizontal className="h-5 w-5" />
          )}
        </Button>
      </div>
    </div>
  );
}; 
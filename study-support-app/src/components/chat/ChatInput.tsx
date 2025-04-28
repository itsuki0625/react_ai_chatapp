'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SendHorizontal, Loader2 } from 'lucide-react';
import { useAuthHelpers } from '@/lib/authUtils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean; // Parent component can indicate loading state (e.g., during message submission)
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading = false }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { hasPermission, isLoading: isAuthLoading } = useAuthHelpers();

  // Check for message sending permission
  const canSendMessage = hasPermission('chat_message_send');

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(event.target.value);
    // Auto-resize textarea height (optional)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleSend = useCallback(() => {
    // Send only if not loading, has permission, and message is not empty
    if (message.trim() && !isLoading && canSendMessage) {
      onSendMessage(message.trim());
      setMessage(''); // Clear input
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'; // Reset height
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [message, isLoading, onSendMessage, canSendMessage]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (but not Shift+Enter)
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex items-end space-x-2 p-4 border-t bg-background">
      <Textarea
        ref={textareaRef}
        value={message}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder={canSendMessage ? "メッセージを入力... (Shift+Enterで改行)" : "メッセージを送信する権限がありません"} // Placeholder reflects permission
        rows={1}
        className="flex-1 resize-none max-h-40 overflow-y-auto rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={isLoading || isAuthLoading || !canSendMessage} // Disable if loading, auth loading, or no permission
      />
      <Button 
        type="button" 
        onClick={handleSend} 
        disabled={isLoading || isAuthLoading || !canSendMessage || !message.trim()} // Disable button based on same conditions + empty message
        size="icon"
        className="flex-shrink-0"
        aria-label="メッセージを送信"
      >
        {isLoading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <SendHorizontal className="h-5 w-5" />
        )}
      </Button>
    </div>
  );
}; 
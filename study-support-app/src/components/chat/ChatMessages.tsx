'use client';

import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"; // Assuming Avatar components exist
import { Bot, User, Loader2, AlertTriangle } from 'lucide-react';
import { ChatMessage } from '@/types/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; // For GitHub Flavored Markdown
import { cn } from '@/lib/utils';

interface ChatMessagesProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: Error | null;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, isLoading, error, messagesEndRef }) => {

  // Helper to format date/time (consider moving to utils)
  const formatTimestamp = (timestamp: string | undefined): string => {
      if (!timestamp) return '';
      try {
          return new Date(timestamp).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
      } catch {
          return '-';
      }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 bg-muted/20">
      {messages.map((message, index) => {
        const isUserMessage = message.sender_type === 'USER';
        const isAiMessage = message.sender_type === 'AI';
        const isSystemMessage = message.sender_type === 'SYSTEM'; // Handle system messages if needed
        
        // Add temporary fields check for optimistic/error states
        const isOptimisticLoading = message.isLoading; 
        const isOptimisticError = message.isError; 

        return (
          <div
            key={message.id || `msg-${index}`} // Use message ID if available
            className={cn(
              "flex items-start gap-3",
              isUserMessage ? "justify-end" : "justify-start"
            )}
          >
            {/* Avatar for AI/System */} 
            {!isUserMessage && (
                <Avatar className="h-8 w-8 border flex-shrink-0">
                    {/* Add actual image source if available */}
                    {/* <AvatarImage src="/placeholder-user.jpg" /> */} 
                    <AvatarFallback className="bg-primary/10 text-primary">
                       {isAiMessage ? <Bot size={18} /> : <AlertTriangle size={18} />} {/* Or other icon for SYSTEM */} 
                    </AvatarFallback>
                </Avatar>
            )}

            {/* Message Bubble */} 
            <div
              className={cn(
                "rounded-lg px-3.5 py-2 max-w-[75%]",
                isUserMessage
                  ? "bg-primary text-primary-foreground"
                  : "bg-background text-foreground border",
                 isOptimisticError ? "border-destructive bg-destructive/10 text-destructive" : "", // Error styling
                 isOptimisticLoading ? "opacity-70" : "" // Loading styling
              )}
            >
              {/* Markdown Rendering for content */} 
               <div className="text-sm prose prose-sm dark:prose-invert max-w-none break-words">
                 <ReactMarkdown remarkPlugins={[remarkGfm]}>
                     {message.content}
                 </ReactMarkdown>
               </div>
               
              {/* Loading/Error Indicator */} 
               {isOptimisticLoading && <Loader2 className="h-4 w-4 animate-spin ml-2 inline-block text-muted-foreground" />} 
               {isOptimisticError && <AlertTriangle className="h-4 w-4 ml-2 inline-block text-destructive" />} 
               
              {/* Timestamp */} 
               <p className="text-xs mt-1 text-right opacity-70">
                 {formatTimestamp(message.created_at)}
               </p>
            </div>

            {/* Avatar for User */} 
            {isUserMessage && (
                <Avatar className="h-8 w-8 border flex-shrink-0">
                    {/* Add actual image source if available */}
                    {/* <AvatarImage src="/placeholder-user.jpg" /> */} 
                    <AvatarFallback className="bg-secondary/50">
                        <User size={18} />
                    </AvatarFallback>
                </Avatar>
            )}
          </div>
        );
      })}
      {/* Loading indicator for initial fetch */} 
       {isLoading && messages.length === 0 && (
          <div className="flex justify-center items-center p-4">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
       )}
       {/* Error indicator for initial fetch */} 
        {error && messages.length === 0 && (
           <div className="flex flex-col items-center justify-center p-4 text-destructive">
               <AlertTriangle className="h-8 w-8 mb-2" />
               <p>メッセージの読み込みに失敗しました。</p>
               <p className="text-xs mt-1">{error.message}</p>
           </div>
        )}
      {/* Empty div to scroll to */} 
      <div ref={messagesEndRef} />
    </div>
  );
}; 
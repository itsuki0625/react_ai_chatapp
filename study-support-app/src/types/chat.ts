// study-support-app/src/types/chat.ts

// Basic structure for a chat session
export interface ChatSession {
    id: string;
    title?: string | null;
    created_at: string; // ISO 8601 string
    updated_at?: string; // ISO 8601 string
    // Add other relevant fields from your backend model if needed
    // e.g., user_id, session_type, status
  }
  
  // Basic structure for a chat message
  export interface ChatMessage {
    id: string;
    session_id: string;
    sender_id?: string | null; // ID of the user or null/system for AI
    sender_type: 'USER' | 'AI' | 'SYSTEM'; // Type of the sender
    content: string;
    created_at: string; // ISO 8601 string
    // Optional fields based on usage in ChatPage.tsx
    isLoading?: boolean; 
    isError?: boolean; 
    // Add other relevant fields from your backend model if needed
    // e.g., read_status, message_type (text, image, etc.)
  }

// バックエンドの app/enums.py に対応する型定義

export enum ChatType {
  SELF_ANALYSIS = "self_analysis",
  ADMISSION = "admission",
  STUDY_SUPPORT = "study_support",
  GENERAL = "general",
}

// 必要に応じて他の型もここに追加できます
// 例: MessageSender, ChatSessionStatus など

// Add other necessary type definitions here

// ... (rest of the file remains unchanged)

// ... (rest of the file remains unchanged) 
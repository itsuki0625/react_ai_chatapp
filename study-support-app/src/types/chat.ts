// study-support-app/src/types/chat.ts

// セッション一覧などで使用する個々のチャットセッション情報
export interface ChatSession {
  id: string;
  title?: string | null;
  created_at: string; // ISO 8601 string
  updated_at?: string; // ISO 8601 string
  chat_type: ChatTypeValue; // chat_type を追加 (APIレスポンスに含まれる想定)
  last_message_summary?: string; // 追加
  status?: SessionStatusValue; // ★追加: セッションのステータス
  // user_id, status など、バックエンドの ChatSessionResponse に合わせて追加検討
}

// バックエンドの MessageSender Enum に対応
export type MessageSender = 'USER' | 'AI';

// フロントエンドで扱うチャットメッセージの型
export interface ChatMessage {
id: string; // サーバーDBのID or フロントエンドで生成するユニークID
session_id?: string; // どのセッションに属するか (履歴読み込み時など)
sender_id?: string | null; // バックエンドの sender_id に対応 (主に履歴用)
sender: MessageSender;
content: string;
timestamp: string; // ISO 8601 string (created_at から名称変更)
isStreaming?: boolean; // AIのメッセージがストリーミング中か
isLoading?: boolean; // ユーザーメッセージ送信中など
isError?: boolean; // このメッセージがエラーを表すか (例: 送信失敗、AI応答エラー)
}

// バックエンドの app/models/enums.py の ChatType に対応
export enum ChatTypeEnum {
  GENERAL = "general",
  SELF_ANALYSIS = "self_analysis",
  ADMISSION = "admission",
  STUDY_SUPPORT = "study_support",
  FAQ = "faq",
}
// ChatTypeEnum を文字列リテラル型としても使えるようにする
export type ChatTypeValue = `${ChatTypeEnum}`;

export type SessionStatusValue = "ACTIVE" | "ARCHIVED" | "CLOSED" | null; // ★ null を追加

// フロントエンドがサーバーに送信するリクエストの型 (バックエンドの ChatRequest に対応)
export interface ChatSubmitRequest {
message: string;
session_id?: string | null; // UUID
chat_type: ChatTypeValue; // ChatTypeEnum の値を使用
}

// 現在アクティブな単一チャットウィンドウの状態 (useReducer で管理)
export interface ChatState {
sessionId: string | null | undefined; // ★ undefined を許容
messages: ChatMessage[];
isLoading: boolean; // AIからの応答待ち or ユーザーメッセージ送信中
error: string | Error | null; // Error型も許容するように変更
currentChatType: ChatTypeValue | null; // ★ null を許容
// --- セッションリスト関連のstateを追加 ---
sessions: ChatSession[]; // ChatSessionSummary の代わりに ChatSession を使用
isLoadingSessions: boolean;
errorSessions: string | Error | null;
archivedSessions: ChatSession[];
isLoadingArchivedSessions: boolean;
errorArchivedSessions: string | Error | null;
justStartedNewChat?: boolean; // ★新しいチャット開始直後フラグ
viewingSessionStatus?: SessionStatusValue | null; // ★追加: 表示中セッションのステータス
isWebSocketConnected: boolean; // ★追加
sessionStatus: SessionStatusValue | 'PENDING' | 'INACTIVE'; // ★追加 PENDING と INACTIVE も許容
}

// useReducer のための Action 型
export type ChatAction =
| { type: 'SET_SESSION_ID'; payload: { id: string | null | undefined; status?: SessionStatusValue } } // ★ undefined を許容
| { type: 'SET_CURRENT_CHAT_TYPE'; payload: ChatTypeValue | null } // ★ null を許容
| { type: 'ADD_MESSAGE'; payload: ChatMessage }
| { type: 'FETCH_HISTORY_START' }
| { type: 'FETCH_HISTORY_SUCCESS'; payload: ChatMessage[] }
| { type: 'FETCH_HISTORY_FAILURE'; payload: string | Error }
| { type: 'SEND_MESSAGE_START' }
| { type: 'SEND_MESSAGE_SUCCESS' }
| { type: 'SEND_MESSAGE_FAILURE'; payload: string | Error }
| { type: 'FETCH_SESSIONS_START' }
| { type: 'FETCH_SESSIONS_SUCCESS'; payload: ChatSession[] }
| { type: 'FETCH_SESSIONS_FAILURE'; payload: string | Error }
| { type: 'START_NEW_CHAT_SESSION'; payload: { sessionId: string | null | undefined; chatType: ChatTypeValue | null } } // ★ undefined, null を許容
| { type: 'ARCHIVE_SESSION_SUCCESS'; payload: { sessionId: string } }
| { type: 'FETCH_ARCHIVED_SESSIONS_START' }
| { type: 'FETCH_ARCHIVED_SESSIONS_SUCCESS'; payload: ChatSession[] }
| { type: 'FETCH_ARCHIVED_SESSIONS_FAILURE'; payload: string | Error }
| { type: 'UNARCHIVE_SESSION_SUCCESS'; payload: { sessionId: string } }
| { type: 'SET_VIEWING_SESSION_STATUS'; payload: SessionStatusValue | null }
// ★ 以下、新しいアクションタイプを追加
| { type: 'PREPARE_NEW_CHAT'; payload: { chatType: ChatTypeValue } }
| { type: 'SET_CHAT_TYPE'; payload: ChatTypeValue | null }
| { type: 'CLEAR_CHAT'; payload: { chatType?: ChatTypeValue | null } }
| { type: 'SET_WEBSOCKET_CONNECTED'; payload: boolean };

// ChatContext で提供される値の型 (ChatProvider から渡される)
export interface ChatContextType extends ChatState {
  dispatch: React.Dispatch<ChatAction>;
  sendMessage: (messageContent: string) => void;
  clearChat: (chatType?: ChatTypeValue) => void;
  changeChatType: (chatType: ChatTypeValue) => void;
  authToken: string | null;
  isConnected: boolean;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  startNewChat: (chatType: ChatTypeValue, title?: string) => Promise<string | null>;
  fetchSessions: (chatType: ChatTypeValue) => Promise<void>;
  fetchMessages: (sessionId: string) => Promise<void>;
  archiveSession: (sessionId: string) => Promise<void>;
  fetchArchivedSessions: (chatType: ChatTypeValue) => Promise<void>;
  unarchiveSession: (sessionId: string) => Promise<void>;
}
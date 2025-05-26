import { create } from 'zustand';

// 仮の型定義 (後で実際の型に置き換える)
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system'; // 'draft_agent' | 'style_agent' | 'eval_agent' | 'ref_agent' なども将来的には考慮
  content: string;
  timestamp: Date;
}

interface StatementEditorState {
  draftId: string | null;
  draftContent: string;
  currentVersion: string; // 例: "v1-user", "v2-ai"
  messages: Message[];
  // pendingPatch?: ChangeMap; // ChangeMapの型定義が必要
  tokenTotal: number; // 単位は円を想定
  isChatLoading: boolean; // チャットのレスポンス待ちなど

  // アクション
  setDraftId: (id: string | null) => void;
  setDraftContent: (content: string) => void;
  setCurrentVersion: (version: string) => void;
  addMessage: (message: Message) => void;
  // applyPatch: (patch: ChangeMap) => void;
  incrementTokenTotal: (amount: number) => void;
  setIsChatLoading: (isLoading: boolean) => void;
  resetStore: () => void; // ストアを初期状態にリセットするアクション
}

const initialState = {
  draftId: null,
  draftContent: '',
  currentVersion: 'v1-initial',
  messages: [],
  tokenTotal: 0,
  isChatLoading: false,
};

export const useStatementEditorStore = create<StatementEditorState>((set, get) => ({
  ...initialState,

  setDraftId: (id) => set({ draftId: id }),
  setDraftContent: (content) => set({ draftContent: content }),
  setCurrentVersion: (version) => set({ currentVersion: version }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  incrementTokenTotal: (amount) => set((state) => ({ tokenTotal: state.tokenTotal + amount })),
  setIsChatLoading: (isLoading) => set({ isChatLoading: isLoading }),
  resetStore: () => set(initialState),
})); 
import { create } from 'zustand';
import { User } from '@/types/user'; // User 型をインポート

interface UserState {
  user: User | null;
  setUser: (user: User | null) => void;
  // 必要に応じて他の状態やアクションを追加
}

export const useUserStore = create<UserState>((set) => ({
  user: null, // 初期状態は null
  setUser: (user) => set({ user }),
})); 
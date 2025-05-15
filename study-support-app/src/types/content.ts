// バックエンドの Enum に対応する型
export type BackendContentType = 'video' | 'slide' | 'pdf' | 'audio' | 'article' | 'quiz' | 'external_link';
export type ContentCategory = 'self_analysis' | 'admissions' | 'academic' | 'university_info' | 'career' | 'other';

// フロントエンドのフォーム表示などで使う可能性のある大文字版 (もし必要なら)
export type FormContentType = 'VIDEO' | 'SLIDE' | 'PDF'; // 必要に応じて他のタイプを追加

// API レスポンスに合わせた Content 型
export interface Content {
  id: string;
  title: string;
  description?: string;
  url: string;
  content_type: BackendContentType; // バックエンドの小文字 Enum 型に
  thumbnail_url?: string;
  tags?: string[];              // string[] 型に変更
  created_at: string;
  updated_at: string;
  created_by_id?: string; // APIレスポンスに含まれているか確認が必要
  average_rating?: number;
  review_count?: number;
  view_count?: number;
  category_info?: ContentCategoryInfo; // ★ 追加
  duration?: number;                   // ★ 追加
  is_premium?: boolean;                // ★ 追加
  author?: string;                     // ★ 追加
  difficulty?: number;                 // ★ 追加
  provider?: string;                   // ★ 追加 (バックエンドモデルに合わせて)
  provider_item_id?: string;           // ★ 追加 (バックエンドモデルに合わせて)
}

// 新規作成リクエスト用の型 (前回提案済み、必要であれば再確認)
export interface ContentCreate {
  title: string;
  description?: string;
  url: string;
  content_type: BackendContentType;
  thumbnail_url?: string;
  category_id?: string; // ★ Optional<UUID> に対応する型として string (または null) を許容する形に変更
  tags?: string[];
  created_by_id: string;
  // provider?: 'google' | 'slideshare' | 'speakerdeck'; // これはフォーム用の型。APIリクエストではstringでOK
  presenter_notes?: string[];
  provider?: string; // ★ 追加
  provider_item_id?: string; // ★ 追加
}

// ContentType は FormContentType として名前を変更したので古い定義は削除
// export type ContentType = 'VIDEO' | 'SLIDE' | 'PDF'; 

// ★★★ 新しいカテゴリー情報型を追加 ★★★
export interface ContentCategoryInfo {
  id: string; // UUID
  name: string;
  description?: string; // 日本語名
  display_order?: number; // ★ 追加 (元々コメントアウトされていたのを有効化)
  icon_url?: string; // ★ 追加 (元々コメントアウトされていたのを有効化)
  is_active?: boolean; // ★ 追加 (元々コメントアウトされていたのを有効化)
}

// ★★★ ContentCategoryInfo は既存で、display_order などが追加されているはず ★★★
// export interface ContentCategoryInfo {
//   id: string; 
//   name: string;
//   description?: string; 
//   display_order?: number;
//   icon_url?: string; 
//   is_active?: boolean;
// }

// --- ↓↓↓ カテゴリー管理用の新しい型定義を追加 ↓↓↓ ---
export interface ContentCategoryBase {
  name: string; 
  description?: string | null; 
  display_order?: number;
  icon_url?: string | null; 
  is_active?: boolean;
}

export type ContentCategoryCreate = ContentCategoryBase;

export interface ContentCategoryUpdate {
  name?: string;
  description?: string | null;
  display_order?: number;
  icon_url?: string | null;
  is_active?: boolean;
}
// --- ↑↑↑ カテゴリー管理用の新しい型定義を追加 ↑↑↑ --- 
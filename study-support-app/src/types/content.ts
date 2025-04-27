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
  category?: ContentCategory;     // バックエンドの Enum 型に
  tags?: string[];              // string[] 型に変更
  created_at: string;
  updated_at: string;
  created_by_id?: string; // APIレスポンスに含まれているか確認が必要
  provider?: 'google' | 'slideshare' | 'speakerdeck'; // APIレスポンスに含まれているか確認が必要
  presenter_notes?: string[]; // APIレスポンスに含まれているか確認が必要
}

// 新規作成リクエスト用の型 (前回提案済み、必要であれば再確認)
export interface ContentCreate {
  title: string;
  description?: string;
  url: string;
  content_type: BackendContentType;
  thumbnail_url?: string;
  category?: ContentCategory;
  tags?: string[];
  created_by_id: string;
  provider?: 'google' | 'slideshare' | 'speakerdeck';
  presenter_notes?: string[];
}

// ContentType は FormContentType として名前を変更したので古い定義は削除
// export type ContentType = 'VIDEO' | 'SLIDE' | 'PDF'; 
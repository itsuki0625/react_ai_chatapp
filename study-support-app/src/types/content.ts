export type ContentType = 'VIDEO' | 'SLIDE' | 'PDF';

export interface Content {
  id: string;
  title: string;
  description?: string;
  url: string;
  content_type: ContentType;
  thumbnail_url?: string;
  category?: string;
  tags?: string;
  created_at: string;
  updated_at: string;
  provider?: 'google' | 'slideshare' | 'speakerdeck';
  presenter_notes?: string[];
} 
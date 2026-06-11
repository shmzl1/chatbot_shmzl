export interface DiaryAttachment {
  id: number;
  entry_id: number;
  filename: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  public_url: string;
  created_at: string;
}

export interface DiaryEntryListItem {
  id: number;
  title: string;
  content_excerpt: string;
  entry_date: string;
  mood: string;
  tags: string[];
  image_count: number;
  created_at: string;
  updated_at: string;
}

export interface DiaryEntryDetail {
  id: number;
  title: string;
  content_markdown: string;
  entry_date: string;
  mood: string;
  tags: string[];
  attachments: DiaryAttachment[];
  created_at: string;
  updated_at: string;
}

export interface DiaryEntryPayload {
  title: string;
  content_markdown: string;
  entry_date: string;
  mood: string;
  tags: string[];
}

export interface DiaryEntryListResponse {
  entries: DiaryEntryListItem[];
}

export interface DiaryImageUploadResponse {
  attachment: DiaryAttachment;
}

export interface DiaryFilters {
  keyword?: string;
  date_from?: string;
  date_to?: string;
  mood?: string;
  tag?: string;
}

// ... 既存の型定義

export interface ChecklistItem {
  status: boolean;
  feedback: string;
}

export interface ChecklistEvaluation {
  checklist: {
    [key: string]: ChecklistItem;
  };
  overall_status: boolean;
  general_feedback: string;
}

// Generic interface for API responses that return a list of items with pagination/total count
export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  // You can add more fields if your API provides them, like `pages`, `has_next`, `has_prev`
}
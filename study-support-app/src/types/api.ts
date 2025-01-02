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
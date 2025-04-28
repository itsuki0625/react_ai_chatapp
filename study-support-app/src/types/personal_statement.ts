// Placeholder types for PersonalStatement
// Replace with actual types based on backend schema

export interface PersonalStatementResponse {
    id: string;
    content: string;
    status: 'draft' | 'submitted' | 'reviewed' | 'completed' | string; // Allow string for flexibility
    created_at: string; // ISO 8601 DateTime string
    updated_at: string; // ISO 8601 DateTime string
    user_id: string;
    desired_department_id?: string | null;
    university_name?: string | null; // Added based on usage in page.tsx
    department_name?: string | null; // Added based on usage in page.tsx
    // feedback_count?: number; // Optional, if needed
    // latest_feedback_at?: string | null; // Optional, if needed
  }
  
  export interface PersonalStatementCreate {
    content: string;
    desired_department_id?: string | null;
    // status might be set on backend
  }
  
  export interface PersonalStatementUpdate {
    content?: string;
    status?: 'draft' | 'submitted' | 'reviewed' | 'completed' | string;
    desired_department_id?: string | null;
  }
  
  // Placeholder for Feedback types if needed
  export interface FeedbackResponse { /* ... */ }
  export interface FeedbackCreate { /* ... */ } 
import { 
  StudentChatSession, 
  StudentStatement, 
  StudentDesiredSchool,
  TeacherStudentAssignment 
} from '@/types/tenant';

export const mockChatSessions: StudentChatSession[] = [
  {
    id: "chat-001",
    userId: "user-004", // 田中太郎
    type: "self_analysis",
    title: "自己分析セッション #1",
    status: "completed",
    messageCount: 15,
    lastMessageAt: "2024-01-19T16:45:00Z",
    createdAt: "2024-01-19T14:00:00Z"
  },
  {
    id: "chat-002", 
    userId: "user-004",
    type: "self_analysis",
    title: "自己分析セッション #2",
    status: "completed",
    messageCount: 22,
    lastMessageAt: "2024-01-20T10:30:00Z",
    createdAt: "2024-01-20T09:15:00Z"
  },
  {
    id: "chat-003",
    userId: "user-004",
    type: "statement_support",
    title: "志望理由書作成サポート - 東京大学",
    status: "active",
    messageCount: 8,
    lastMessageAt: "2024-01-20T15:20:00Z",
    createdAt: "2024-01-20T14:30:00Z"
  },
  {
    id: "chat-004",
    userId: "user-005", // 鈴木花子
    type: "self_analysis",
    title: "自己分析セッション #1",
    status: "active",
    messageCount: 7,
    lastMessageAt: "2024-01-20T12:20:00Z",
    createdAt: "2024-01-20T11:30:00Z"
  },
  {
    id: "chat-005",
    userId: "user-005",
    type: "general",
    title: "進路相談",
    status: "completed",
    messageCount: 12,
    lastMessageAt: "2024-01-18T14:45:00Z",
    createdAt: "2024-01-18T13:00:00Z"
  },
  {
    id: "chat-006",
    userId: "user-006", // 渡辺次郎
    type: "self_analysis",
    title: "自己分析セッション #1",
    status: "completed",
    messageCount: 18,
    lastMessageAt: "2024-01-17T16:00:00Z",
    createdAt: "2024-01-17T14:15:00Z"
  },
  {
    id: "chat-007",
    userId: "user-006",
    type: "statement_support",
    title: "志望理由書作成サポート - 早稲田大学",
    status: "completed",
    messageCount: 25,
    lastMessageAt: "2024-01-19T17:30:00Z",
    createdAt: "2024-01-18T10:00:00Z"
  },
  {
    id: "chat-008",
    userId: "user-007", // 高橋雪
    type: "self_analysis",
    title: "自己分析セッション #1",
    status: "active",
    messageCount: 3,
    lastMessageAt: "2024-01-20T12:15:00Z",
    createdAt: "2024-01-20T11:45:00Z"
  }
];

export const mockStatements: StudentStatement[] = [
  {
    id: "statement-001",
    userId: "user-004", // 田中太郎
    title: "東京大学理学部 志望理由書",
    universityName: "東京大学",
    departmentName: "理学部",
    status: "completed",
    wordCount: 850,
    targetWordCount: 800,
    progress: 100,
    createdAt: "2024-01-15T10:00:00Z",
    updatedAt: "2024-01-19T16:45:00Z",
    submissionDeadline: "2024-02-15T23:59:59Z"
  },
  {
    id: "statement-002",
    userId: "user-004",
    title: "早稲田大学理工学部 志望理由書",
    universityName: "早稲田大学",
    departmentName: "理工学部",
    status: "in_review",
    wordCount: 650,
    targetWordCount: 800,
    progress: 81,
    createdAt: "2024-01-18T14:30:00Z",
    updatedAt: "2024-01-20T15:20:00Z",
    submissionDeadline: "2024-02-20T23:59:59Z"
  },
  {
    id: "statement-003",
    userId: "user-005", // 鈴木花子
    title: "慶應義塾大学文学部 志望理由書",
    universityName: "慶應義塾大学",
    departmentName: "文学部",
    status: "draft",
    wordCount: 320,
    targetWordCount: 600,
    progress: 53,
    createdAt: "2024-01-16T09:15:00Z",
    updatedAt: "2024-01-19T20:30:00Z",
    submissionDeadline: "2024-03-01T23:59:59Z"
  },
  {
    id: "statement-004",
    userId: "user-005",
    title: "上智大学外国語学部 志望理由書",
    universityName: "上智大学",
    departmentName: "外国語学部",
    status: "draft",
    wordCount: 180,
    targetWordCount: 800,
    progress: 23,
    createdAt: "2024-01-19T16:00:00Z",
    updatedAt: "2024-01-19T20:30:00Z",
    submissionDeadline: "2024-02-25T23:59:59Z"
  },
  {
    id: "statement-005",
    userId: "user-006", // 渡辺次郎
    title: "早稲田大学政治経済学部 志望理由書",
    universityName: "早稲田大学",
    departmentName: "政治経済学部",
    status: "completed",
    wordCount: 795,
    targetWordCount: 800,
    progress: 100,
    createdAt: "2024-01-10T11:20:00Z",
    updatedAt: "2024-01-17T15:45:00Z",
    submissionDeadline: "2024-02-10T23:59:59Z"
  },
  {
    id: "statement-006",
    userId: "user-006",
    title: "慶應義塾大学経済学部 志望理由書",
    universityName: "慶應義塾大学",
    departmentName: "経済学部",
    status: "in_review",
    wordCount: 720,
    targetWordCount: 800,
    progress: 90,
    createdAt: "2024-01-17T13:30:00Z",
    updatedAt: "2024-01-20T15:45:00Z",
    submissionDeadline: "2024-02-28T23:59:59Z"
  },
  {
    id: "statement-007",
    userId: "user-007", // 高橋雪
    title: "青山学院大学文学部 志望理由書",
    universityName: "青山学院大学",
    departmentName: "文学部",
    status: "draft",
    wordCount: 120,
    targetWordCount: 600,
    progress: 20,
    createdAt: "2024-01-20T10:00:00Z",
    updatedAt: "2024-01-20T12:15:00Z",
    submissionDeadline: "2024-03-15T23:59:59Z"
  }
];

export const mockDesiredSchools: StudentDesiredSchool[] = [
  // 田中太郎の志望校
  {
    id: "desired-001",
    userId: "user-004",
    universityName: "東京大学",
    departmentName: "理学部",
    preferenceOrder: 1,
    admissionType: "推薦入試",
    examDate: "2024-02-25",
    status: "decided",
    createdAt: "2024-01-10T00:00:00Z"
  },
  {
    id: "desired-002",
    userId: "user-004", 
    universityName: "早稲田大学",
    departmentName: "理工学部",
    preferenceOrder: 2,
    admissionType: "一般入試",
    examDate: "2024-02-15",
    status: "decided",
    createdAt: "2024-01-10T00:00:00Z"
  },
  {
    id: "desired-003",
    userId: "user-004",
    universityName: "慶應義塾大学",
    departmentName: "理工学部",
    preferenceOrder: 3,
    admissionType: "一般入試",
    examDate: "2024-02-18",
    status: "considering",
    createdAt: "2024-01-15T00:00:00Z"
  },
  // 鈴木花子の志望校
  {
    id: "desired-004",
    userId: "user-005",
    universityName: "慶應義塾大学",
    departmentName: "文学部",
    preferenceOrder: 1,
    admissionType: "推薦入試",
    examDate: "2024-03-01",
    status: "decided",
    createdAt: "2024-01-12T00:00:00Z"
  },
  {
    id: "desired-005",
    userId: "user-005",
    universityName: "上智大学",
    departmentName: "外国語学部",
    preferenceOrder: 2,
    admissionType: "一般入試",
    examDate: "2024-02-22",
    status: "decided",
    createdAt: "2024-01-12T00:00:00Z"
  },
  {
    id: "desired-006",
    userId: "user-005",
    universityName: "青山学院大学",
    departmentName: "文学部",
    preferenceOrder: 3,
    admissionType: "一般入試",
    examDate: "2024-02-28",
    status: "considering",
    createdAt: "2024-01-18T00:00:00Z"
  },
  // 渡辺次郎の志望校
  {
    id: "desired-007",
    userId: "user-006",
    universityName: "早稲田大学",
    departmentName: "政治経済学部",
    preferenceOrder: 1,
    admissionType: "推薦入試",
    examDate: "2024-02-12",
    status: "applied",
    createdAt: "2024-01-08T00:00:00Z"
  },
  {
    id: "desired-008",
    userId: "user-006",
    universityName: "慶應義塾大学",
    departmentName: "経済学部", 
    preferenceOrder: 2,
    admissionType: "一般入試",
    examDate: "2024-02-20",
    status: "decided",
    createdAt: "2024-01-08T00:00:00Z"
  },
  {
    id: "desired-009",
    userId: "user-006",
    universityName: "明治大学",
    departmentName: "政治経済学部",
    preferenceOrder: 3,
    admissionType: "一般入試",
    examDate: "2024-02-25",
    status: "decided",
    createdAt: "2024-01-08T00:00:00Z"
  },
  // 高橋雪の志望校
  {
    id: "desired-010",
    userId: "user-007",
    universityName: "青山学院大学",
    departmentName: "文学部",
    preferenceOrder: 1,
    admissionType: "推薦入試",
    examDate: "2024-03-10",
    status: "considering",
    createdAt: "2024-01-20T00:00:00Z"
  }
];

export const mockTeacherStudentAssignments: TeacherStudentAssignment[] = [
  {
    id: "assignment-001",
    teacherId: "user-002", // 山田英語
    studentId: "user-004", // 田中太郎
    schoolId: "school-001",
    assignmentType: "primary",
    subject: "英語",
    isActive: true,
    assignedAt: "2024-01-10T00:00:00Z",
    assignedBy: "user-001" // 田中管理
  },
  {
    id: "assignment-002",
    teacherId: "user-002", // 山田英語
    studentId: "user-005", // 鈴木花子
    schoolId: "school-001",
    assignmentType: "primary",
    subject: "英語",
    isActive: true,
    assignedAt: "2024-01-12T00:00:00Z",
    assignedBy: "user-001"
  },
  {
    id: "assignment-003",
    teacherId: "user-003", // 佐藤数学
    studentId: "user-004", // 田中太郎
    schoolId: "school-001", 
    assignmentType: "secondary",
    subject: "数学",
    isActive: true,
    assignedAt: "2024-01-10T00:00:00Z",
    assignedBy: "user-001"
  },
  {
    id: "assignment-004",
    teacherId: "user-003", // 佐藤数学
    studentId: "user-006", // 渡辺次郎
    schoolId: "school-001",
    assignmentType: "primary",
    subject: "数学",
    isActive: true,
    assignedAt: "2024-01-08T00:00:00Z",
    assignedBy: "user-001"
  },
  {
    id: "assignment-005",
    teacherId: "user-002", // 山田英語
    studentId: "user-007", // 高橋雪
    schoolId: "school-001",
    assignmentType: "primary", 
    subject: "英語",
    isActive: true,
    assignedAt: "2024-01-20T00:00:00Z",
    assignedBy: "user-001"
  }
];

// チャット詳細メッセージのMockデータ
export interface ChatMessage {
  id: string;
  sessionId: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
}

export const mockChatMessages: ChatMessage[] = [
  // chat-001 (田中太郎の自己分析セッション #1)
  {
    id: "msg-001",
    sessionId: "chat-001",
    content: "こんにちは！自己分析を始めたいと思います。",
    sender: "user",
    timestamp: "2024-01-19T14:00:00Z"
  },
  {
    id: "msg-002",
    sessionId: "chat-001",
    content: "こんにちは！自己分析のお手伝いをさせていただきます。まず、あなたが大学で学びたいことについて教えてください。",
    sender: "ai",
    timestamp: "2024-01-19T14:00:30Z"
  },
  {
    id: "msg-003",
    sessionId: "chat-001",
    content: "理学部で物理学を学びたいと思っています。特に量子力学に興味があります。",
    sender: "user",
    timestamp: "2024-01-19T14:02:00Z"
  },
  {
    id: "msg-004",
    sessionId: "chat-001",
    content: "量子力学への興味、素晴らしいですね！その興味はどのような経験から生まれたのでしょうか？",
    sender: "ai",
    timestamp: "2024-01-19T14:02:30Z"
  },
  {
    id: "msg-005",
    sessionId: "chat-001",
    content: "高校2年生の時に読んだ科学雑誌の特集記事がきっかけです。量子もつれという現象について知り、とても興味を持ちました。",
    sender: "user",
    timestamp: "2024-01-19T14:05:00Z"
  },
  // chat-003 (田中太郎の志望理由書作成サポート)
  {
    id: "msg-006",
    sessionId: "chat-003",
    content: "東京大学の志望理由書を書いているのですが、アドバイスをお願いします。",
    sender: "user",
    timestamp: "2024-01-20T14:30:00Z"
  },
  {
    id: "msg-007",
    sessionId: "chat-003",
    content: "東京大学の志望理由書作成をお手伝いします。現在どのような内容を書かれていますか？",
    sender: "ai", 
    timestamp: "2024-01-20T14:30:30Z"
  },
  {
    id: "msg-008",
    sessionId: "chat-003",
    content: "量子力学への興味と、将来の研究目標について書きました。でも、なぜ東京大学なのかの理由が弱い気がします。",
    sender: "user",
    timestamp: "2024-01-20T14:32:00Z"
  }
];
import { School, SchoolUser, Activity, AnalyticsData } from '@/types/tenant';

export const mockSchools: School[] = [
  {
    id: "school-001",
    name: "東京都立進学高等学校",
    code: "TOKYO-001",
    address: "東京都渋谷区恵比寿1-2-3",
    prefecture: "東京都",
    city: "渋谷区",
    zipCode: "150-0013",
    principalName: "山田太郎",
    websiteUrl: "https://tokyo-shingaku.ed.jp",
    isActive: true,
    settings: {
      allowStudentChat: true,
      requireStatementApproval: true,
      enableAnalytics: true,
      enableTeacherStudentAssignment: true,
      customBranding: {
        primaryColor: "#3B82F6",
        secondaryColor: "#10B981",
        accentColor: "#F59E0B"
      },
      notifications: {
        emailEnabled: true,
        pushEnabled: true,
        digestFrequency: "weekly"
      }
    },
    stats: {
      totalStudents: 120,
      totalTeachers: 15,
      totalSchoolAdmins: 3,
      activeStudents: 115,
      activeTeachers: 14,
      statementsInProgress: 45,
      completedStatements: 75,
      totalChatSessions: 234,
      monthlyNewUsers: 8,
      averageStatementCompletionDays: 21
    },
    createdAt: "2023-04-01T00:00:00Z",
    updatedAt: "2024-01-15T10:30:00Z"
  },
  {
    id: "school-002", 
    name: "神奈川県立海浜高等学校",
    code: "KANAGAWA-002",
    address: "神奈川県横浜市中区海岸通1-1-1",
    prefecture: "神奈川県",
    city: "横浜市",
    zipCode: "231-0002",
    principalName: "佐藤花子",
    websiteUrl: "https://kaihin-high.ed.jp",
    isActive: true,
    settings: {
      allowStudentChat: true,
      requireStatementApproval: false,
      enableAnalytics: true,
      enableTeacherStudentAssignment: true,
      customBranding: {
        primaryColor: "#059669",
        secondaryColor: "#3B82F6",
        accentColor: "#DC2626"
      },
      notifications: {
        emailEnabled: true,
        pushEnabled: false,
        digestFrequency: "daily"
      }
    },
    stats: {
      totalStudents: 98,
      totalTeachers: 12,
      totalSchoolAdmins: 2,
      activeStudents: 94,
      activeTeachers: 11,
      statementsInProgress: 32,
      completedStatements: 66,
      totalChatSessions: 189,
      monthlyNewUsers: 5,
      averageStatementCompletionDays: 18
    },
    createdAt: "2023-05-15T00:00:00Z",
    updatedAt: "2024-01-10T14:20:00Z"
  },
  {
    id: "school-003",
    name: "埼玉県立科学技術高等学校",
    code: "SAITAMA-003", 
    address: "埼玉県さいたま市浦和区高砂3-15-1",
    prefecture: "埼玉県",
    city: "さいたま市",
    zipCode: "330-0063",
    principalName: "鈴木一郎",
    websiteUrl: "https://kagaku-tech.ed.jp",
    isActive: true,
    settings: {
      allowStudentChat: true,
      requireStatementApproval: true,
      enableAnalytics: false,
      enableTeacherStudentAssignment: false,
      customBranding: {
        primaryColor: "#7C3AED",
        secondaryColor: "#F59E0B",
        accentColor: "#EF4444"
      },
      notifications: {
        emailEnabled: false,
        pushEnabled: true,
        digestFrequency: "monthly"
      }
    },
    stats: {
      totalStudents: 156,
      totalTeachers: 18,
      totalSchoolAdmins: 4,
      activeStudents: 142,
      activeTeachers: 16,
      statementsInProgress: 67,
      completedStatements: 89,
      totalChatSessions: 298,
      monthlyNewUsers: 12,
      averageStatementCompletionDays: 25
    },
    createdAt: "2023-03-20T00:00:00Z",
    updatedAt: "2024-01-20T09:45:00Z"
  }
];

export const mockSchoolUsers: SchoolUser[] = [
  // 東京都立進学高等学校のユーザー
  {
    id: "user-001",
    email: "admin@tokyo-shingaku.ed.jp",
    fullName: "田中管理",
    role: "school_admin",
    schoolId: "school-001",
    isActive: true,
    profileImageUrl: "/images/avatars/admin1.jpg",
    lastLoginAt: "2024-01-20T14:30:00Z",
    createdAt: "2023-04-01T00:00:00Z",
    updatedAt: "2024-01-20T14:30:00Z"
  },
  {
    id: "user-002",
    email: "yamada.teacher@tokyo-shingaku.ed.jp", 
    fullName: "山田英語",
    role: "teacher",
    schoolId: "school-001",
    isActive: true,
    profileImageUrl: "/images/avatars/teacher1.jpg",
    lastLoginAt: "2024-01-20T13:45:00Z",
    createdAt: "2023-04-01T00:00:00Z",
    updatedAt: "2024-01-20T13:45:00Z"
  },
  {
    id: "user-003",
    email: "sato.teacher@tokyo-shingaku.ed.jp",
    fullName: "佐藤数学",
    role: "teacher", 
    schoolId: "school-001",
    isActive: true,
    profileImageUrl: "/images/avatars/teacher2.jpg",
    lastLoginAt: "2024-01-20T10:20:00Z",
    createdAt: "2023-04-01T00:00:00Z",
    updatedAt: "2024-01-20T10:20:00Z"
  },
  {
    id: "user-004",
    email: "tanaka.taro@tokyo-shingaku.ed.jp",
    fullName: "田中太郎",
    role: "student",
    schoolId: "school-001",
    isActive: true,
    grade: "3",
    className: "A",
    studentNumber: "15",
    profileImageUrl: "/images/avatars/student1.jpg",
    lastLoginAt: "2024-01-20T16:10:00Z",
    createdAt: "2023-04-01T00:00:00Z", 
    updatedAt: "2024-01-20T16:10:00Z"
  },
  {
    id: "user-005",
    email: "suzuki.hanako@tokyo-shingaku.ed.jp",
    fullName: "鈴木花子",
    role: "student",
    schoolId: "school-001",
    isActive: true,
    grade: "2",
    className: "B",
    studentNumber: "08",
    profileImageUrl: "/images/avatars/student2.jpg",
    lastLoginAt: "2024-01-19T20:30:00Z",
    createdAt: "2023-04-01T00:00:00Z",
    updatedAt: "2024-01-19T20:30:00Z"
  },
  {
    id: "user-006",
    email: "watanabe.jiro@tokyo-shingaku.ed.jp",
    fullName: "渡辺次郎",
    role: "student",
    schoolId: "school-001",
    isActive: true,
    grade: "3",
    className: "A",
    studentNumber: "22",
    profileImageUrl: "/images/avatars/student3.jpg",
    lastLoginAt: "2024-01-20T15:45:00Z",
    createdAt: "2023-04-01T00:00:00Z",
    updatedAt: "2024-01-20T15:45:00Z"
  },
  {
    id: "user-007",
    email: "takahashi.yuki@tokyo-shingaku.ed.jp",
    fullName: "高橋雪",
    role: "student",
    schoolId: "school-001",
    isActive: true,
    grade: "1",
    className: "C",
    studentNumber: "05",
    profileImageUrl: "/images/avatars/student4.jpg",
    lastLoginAt: "2024-01-20T12:15:00Z",
    createdAt: "2023-04-01T00:00:00Z",
    updatedAt: "2024-01-20T12:15:00Z"
  },
  // 神奈川県立海浜高等学校のユーザー（サンプル）
  {
    id: "user-101",
    email: "admin@kaihin-high.ed.jp",
    fullName: "海浜管理",
    role: "school_admin",
    schoolId: "school-002",
    isActive: true,
    profileImageUrl: "/images/avatars/admin2.jpg",
    lastLoginAt: "2024-01-20T11:20:00Z",
    createdAt: "2023-05-15T00:00:00Z",
    updatedAt: "2024-01-20T11:20:00Z"
  },
  {
    id: "user-102",
    email: "ishii.teacher@kaihin-high.ed.jp",
    fullName: "石井理科",
    role: "teacher",
    schoolId: "school-002",
    isActive: true,
    profileImageUrl: "/images/avatars/teacher3.jpg",
    lastLoginAt: "2024-01-20T14:00:00Z",
    createdAt: "2023-05-15T00:00:00Z",
    updatedAt: "2024-01-20T14:00:00Z"
  }
];

export const mockActivities: Activity[] = [
  {
    id: "activity-001",
    schoolId: "school-001",
    userId: "user-004",
    userName: "田中太郎",
    userRole: "student",
    type: "statement_completed",
    description: "志望理由書「東京大学理学部」を完成させました",
    timestamp: "2024-01-20T15:30:00Z",
    metadata: {
      statementId: "statement-001",
      universityName: "東京大学",
      departmentName: "理学部"
    }
  },
  {
    id: "activity-002", 
    schoolId: "school-001",
    userId: "user-002",
    userName: "山田英語",
    userRole: "teacher",
    type: "login",
    description: "システムにログインしました",
    timestamp: "2024-01-20T13:45:00Z"
  },
  {
    id: "activity-003",
    schoolId: "school-001",
    userId: "user-005",
    userName: "鈴木花子",
    userRole: "student", 
    type: "chat_started",
    description: "自己分析チャットを開始しました",
    timestamp: "2024-01-20T12:20:00Z",
    metadata: {
      chatType: "self_analysis"
    }
  },
  {
    id: "activity-004",
    schoolId: "school-001",
    userId: "user-007",
    userName: "高橋雪",
    userRole: "student",
    type: "user_registered",
    description: "新規ユーザーとして登録されました",
    timestamp: "2024-01-20T10:00:00Z"
  },
  {
    id: "activity-005",
    schoolId: "school-001",
    userId: "user-002",
    userName: "山田英語",
    userRole: "teacher",
    type: "assignment_created",
    description: "田中太郎を担当生徒に割り当てました",
    timestamp: "2024-01-19T16:30:00Z",
    metadata: {
      studentId: "user-004",
      studentName: "田中太郎"
    }
  }
];

export const mockAnalytics: AnalyticsData = {
  monthlyProgress: [
    { month: "2023-09", completedStatements: 12, newUsers: 5, activeSessions: 45 },
    { month: "2023-10", completedStatements: 18, newUsers: 8, activeSessions: 67 },
    { month: "2023-11", completedStatements: 25, newUsers: 12, activeSessions: 89 },
    { month: "2023-12", completedStatements: 20, newUsers: 6, activeSessions: 78 },
    { month: "2024-01", completedStatements: 28, newUsers: 15, activeSessions: 112 }
  ],
  userActivity: [
    { date: "2024-01-15", activeUsers: 45, loginCount: 78, chatSessions: 23 },
    { date: "2024-01-16", activeUsers: 52, loginCount: 85, chatSessions: 31 },
    { date: "2024-01-17", activeUsers: 48, loginCount: 72, chatSessions: 28 },
    { date: "2024-01-18", activeUsers: 58, loginCount: 94, chatSessions: 35 },
    { date: "2024-01-19", activeUsers: 61, loginCount: 101, chatSessions: 42 },
    { date: "2024-01-20", activeUsers: 67, loginCount: 115, chatSessions: 38 }
  ],
  statementProgress: [
    { status: "下書き", count: 32, percentage: 42.7 },
    { status: "作成中", count: 28, percentage: 37.3 },
    { status: "完成", count: 15, percentage: 20.0 }
  ],
  topPerformingStudents: [
    { id: "user-004", name: "田中太郎", completedStatements: 3, averageScore: 4.8 },
    { id: "user-006", name: "渡辺次郎", completedStatements: 2, averageScore: 4.6 },
    { id: "user-005", name: "鈴木花子", completedStatements: 2, averageScore: 4.5 },
    { id: "user-007", name: "高橋雪", completedStatements: 1, averageScore: 4.3 }
  ]
};
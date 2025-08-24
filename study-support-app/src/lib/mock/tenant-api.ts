import { 
  School, 
  SchoolUser, 
  Activity, 
  AnalyticsData,
  StudentChatSession,
  StudentStatement,
  StudentDesiredSchool,
  TeacherStudentAssignment
} from '@/types/tenant';
import { 
  mockSchools, 
  mockSchoolUsers, 
  mockActivities, 
  mockAnalytics 
} from './schools';
import { 
  mockChatSessions,
  mockStatements,
  mockDesiredSchools,
  mockTeacherStudentAssignments,
  mockChatMessages,
  ChatMessage
} from './student-data';

// シミュレーション用の遅延
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export class MockTenantAPI {
  /**
   * 現在のユーザー情報を取得
   */
  static async getCurrentUser(email: string): Promise<SchoolUser> {
    await delay(300);
    
    const user = mockSchoolUsers.find(u => u.email === email);
    if (!user) {
      throw new Error(`User not found: ${email}`);
    }
    
    return user;
  }

  /**
   * ユーザーがアクセス可能な学校一覧を取得
   */
  static async getAvailableSchools(userId: string): Promise<School[]> {
    await delay(200);
    
    const user = mockSchoolUsers.find(u => u.id === userId);
    if (!user) {
      throw new Error(`User not found: ${userId}`);
    }

    // システム管理者は全ての学校にアクセス可能
    if (user.role === 'admin') {
      return mockSchools;
    }

    // その他のユーザーは所属学校のみアクセス可能
    return mockSchools.filter(school => school.id === user.schoolId);
  }

  /**
   * 学校のユーザー一覧を取得
   */
  static async getSchoolUsers(schoolId: string, role?: string): Promise<SchoolUser[]> {
    await delay(400);
    
    let users = mockSchoolUsers.filter(user => user.schoolId === schoolId);
    
    if (role) {
      users = users.filter(user => user.role === role);
    }
    
    return users.sort((a, b) => {
      // ロール順でソート（school_admin > teacher > student）
      const roleOrder = { school_admin: 0, teacher: 1, student: 2 };
      const aOrder = roleOrder[a.role as keyof typeof roleOrder] ?? 3;
      const bOrder = roleOrder[b.role as keyof typeof roleOrder] ?? 3;
      
      if (aOrder !== bOrder) {
        return aOrder - bOrder;
      }
      
      // 同じロールの場合は名前順
      return a.fullName.localeCompare(b.fullName);
    });
  }

  /**
   * 先生の担当生徒一覧を取得
   */
  static async getTeacherStudents(schoolId: string, teacherId: string): Promise<SchoolUser[]> {
    await delay(300);
    
    // 担当関係を取得
    const assignments = mockTeacherStudentAssignments.filter(
      assignment => 
        assignment.teacherId === teacherId && 
        assignment.schoolId === schoolId && 
        assignment.isActive
    );
    
    // 担当生徒の詳細情報を取得
    const studentIds = assignments.map(assignment => assignment.studentId);
    const students = mockSchoolUsers.filter(user => 
      studentIds.includes(user.id) && user.role === 'student'
    );
    
    return students.sort((a, b) => {
      // 学年、クラス、出席番号順でソート
      const gradeA = parseInt(a.grade || '0');
      const gradeB = parseInt(b.grade || '0');
      
      if (gradeA !== gradeB) {
        return gradeB - gradeA; // 学年は降順（3年 > 2年 > 1年）
      }
      
      if (a.className !== b.className) {
        return (a.className || '').localeCompare(b.className || '');
      }
      
      const numA = parseInt(a.studentNumber || '0');
      const numB = parseInt(b.studentNumber || '0');
      return numA - numB;
    });
  }

  /**
   * 生徒の詳細情報を取得
   */
  static async getStudentDetails(studentId: string) {
    await delay(500);
    
    const student = mockSchoolUsers.find(u => u.id === studentId);
    if (!student) {
      throw new Error(`Student not found: ${studentId}`);
    }
    
    const chatSessions = mockChatSessions.filter(s => s.userId === studentId);
    const statements = mockStatements.filter(s => s.userId === studentId);
    const desiredSchools = mockDesiredSchools.filter(s => s.userId === studentId);
    
    // 統計情報を計算
    const stats = {
      totalChatSessions: chatSessions.length,
      activeChatSessions: chatSessions.filter(s => s.status === 'active').length,
      completedChatSessions: chatSessions.filter(s => s.status === 'completed').length,
      totalStatements: statements.length,
      completedStatements: statements.filter(s => s.status === 'completed').length,
      statementsInProgress: statements.filter(s => s.status === 'in_review' || s.status === 'draft').length,
      totalDesiredSchools: desiredSchools.length,
      decidedSchools: desiredSchools.filter(s => s.status === 'decided').length
    };
    
    return {
      student,
      chatSessions: chatSessions.sort((a, b) => 
        new Date(b.lastMessageAt).getTime() - new Date(a.lastMessageAt).getTime()
      ),
      statements: statements.sort((a, b) => 
        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      ),
      desiredSchools: desiredSchools.sort((a, b) => 
        a.preferenceOrder - b.preferenceOrder
      ),
      stats
    };
  }

  /**
   * チャットセッションの詳細メッセージを取得
   */
  static async getChatMessages(sessionId: string): Promise<ChatMessage[]> {
    await delay(300);
    
    const messages = mockChatMessages.filter(msg => msg.sessionId === sessionId);
    return messages.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }

  /**
   * 志望理由書の詳細内容を取得
   */
  static async getStatementDetails(statementId: string) {
    await delay(300);
    
    const statement = mockStatements.find(s => s.id === statementId);
    if (!statement) {
      throw new Error(`Statement not found: ${statementId}`);
    }
    
    // Mock content（実際の内容）
    const content = `私が${statement.universityName}${statement.departmentName}を志望する理由は、${statement.departmentName}における先端的な研究に携わりたいという強い願いがあるからです。

高校時代に参加した科学オリンピックでの経験を通じて、理論と実践の両面からアプローチする重要性を学びました。特に、量子力学の分野に興味を持ち、将来的には量子コンピューティングの研究に携わりたいと考えています。

${statement.universityName}の${statement.departmentName}は、この分野において国内外で高い評価を受けており、最先端の研究設備と優秀な教授陣が揃っています。私は、この環境で学ぶことで、将来の研究者としての基盤を築きたいと思います。

また、大学院進学を視野に入れており、研究活動を通じて社会に貢献できる人材になりたいと考えています。`;

    return {
      ...statement,
      content,
      feedback: [
        {
          id: "feedback-001",
          type: "improvement",
          message: "具体的な研究テーマをもう少し詳しく書くとより良くなります。",
          timestamp: "2024-01-19T15:30:00Z"
        },
        {
          id: "feedback-002", 
          type: "positive",
          message: "体験談を交えた動機の説明が効果的です。",
          timestamp: "2024-01-19T15:32:00Z"
        }
      ]
    };
  }

  /**
   * 学校の分析データを取得
   */
  static async getSchoolAnalytics(schoolId: string): Promise<AnalyticsData> {
    await delay(600);
    
    // 学校ごとに異なる分析データを返す
    if (schoolId === "school-001") {
      return mockAnalytics;
    }
    
    // 他の学校のサンプルデータ
    return {
      monthlyProgress: [
        { month: "2023-09", completedStatements: 8, newUsers: 3, activeSessions: 32 },
        { month: "2023-10", completedStatements: 12, newUsers: 5, activeSessions: 45 },
        { month: "2023-11", completedStatements: 15, newUsers: 7, activeSessions: 58 },
        { month: "2023-12", completedStatements: 18, newUsers: 4, activeSessions: 62 },
        { month: "2024-01", completedStatements: 22, newUsers: 8, activeSessions: 78 }
      ],
      userActivity: [
        { date: "2024-01-15", activeUsers: 32, loginCount: 56, chatSessions: 18 },
        { date: "2024-01-16", activeUsers: 38, loginCount: 67, chatSessions: 22 },
        { date: "2024-01-17", activeUsers: 35, loginCount: 54, chatSessions: 19 },
        { date: "2024-01-18", activeUsers: 42, loginCount: 73, chatSessions: 26 },
        { date: "2024-01-19", activeUsers: 45, loginCount: 81, chatSessions: 29 },
        { date: "2024-01-20", activeUsers: 48, loginCount: 89, chatSessions: 31 }
      ],
      statementProgress: [
        { status: "下書き", count: 22, percentage: 45.8 },
        { status: "作成中", count: 18, percentage: 37.5 },
        { status: "完成", count: 8, percentage: 16.7 }
      ],
      topPerformingStudents: [
        { id: "user-102", name: "海浜太郎", completedStatements: 2, averageScore: 4.7 },
        { id: "user-103", name: "海浜花子", completedStatements: 2, averageScore: 4.5 },
        { id: "user-104", name: "海浜次郎", completedStatements: 1, averageScore: 4.4 }
      ]
    };
  }

  /**
   * 最近の活動履歴を取得
   */
  static async getRecentActivities(schoolId: string, limit: number = 10): Promise<Activity[]> {
    await delay(250);
    
    const activities = mockActivities
      .filter(activity => activity.schoolId === schoolId)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, limit);
    
    return activities;
  }

  /**
   * 先生の担当関係を取得
   */
  static async getTeacherAssignments(teacherId: string): Promise<TeacherStudentAssignment[]> {
    await delay(200);
    
    return mockTeacherStudentAssignments.filter(
      assignment => assignment.teacherId === teacherId && assignment.isActive
    );
  }

  /**
   * 学校統計のサマリーを取得
   */
  static async getSchoolStatsSummary(schoolId: string) {
    await delay(300);
    
    const school = mockSchools.find(s => s.id === schoolId);
    if (!school) {
      throw new Error(`School not found: ${schoolId}`);
    }
    
    const users = mockSchoolUsers.filter(u => u.schoolId === schoolId);
    const recentActivities = await this.getRecentActivities(schoolId, 5);
    
    return {
      school,
      stats: school.stats,
      recentActivities,
      usersByRole: {
        students: users.filter(u => u.role === 'student').length,
        teachers: users.filter(u => u.role === 'teacher').length,
        schoolAdmins: users.filter(u => u.role === 'school_admin').length
      }
    };
  }

  /**
   * ユーザーの権限チェック
   */
  static async checkUserPermission(userId: string, permission: string): Promise<boolean> {
    await delay(100);
    
    const user = mockSchoolUsers.find(u => u.id === userId);
    if (!user) return false;
    
    // 簡単な権限チェック（実装では より詳細な権限管理が必要）
    const permissions = {
      school_admin: [
        'school_manage_users',
        'school_view_all_students', 
        'school_view_all_teachers',
        'school_manage_settings',
        'school_view_analytics'
      ],
      teacher: [
        'teacher_view_assigned_students',
        'teacher_view_student_chat',
        'teacher_view_student_statements',
        'teacher_view_student_schools'
      ],
      student: [
        'student_manage_own_data',
        'student_create_statements',
        'student_use_chat'
      ]
    };
    
    const userPermissions = permissions[user.role as keyof typeof permissions] || [];
    return userPermissions.includes(permission);
  }
}
import { PersonalStatement, StatementStatus, ChatSession, ChatMessage, DesiredUniversity, Feedback } from '@/types/statement';

// 志望校のモックデータ
export const mockDesiredUniversities: DesiredUniversity[] = [
  {
    id: "1",
    universityName: "東京大学",
    departmentName: "法学部",
    priority: 1
  },
  {
    id: "2", 
    universityName: "早稲田大学",
    departmentName: "政治経済学部",
    priority: 2
  },
  {
    id: "3",
    universityName: "慶應義塾大学",
    departmentName: "商学部",
    priority: 3
  },
  {
    id: "4",
    universityName: "上智大学",
    departmentName: "外国語学部",
    priority: 4
  }
];

// 志望理由書のモックデータ
export const mockStatements: PersonalStatement[] = [
  {
    id: "stmt-1",
    title: "東京大学法学部志望理由書",
    content: `私が東京大学法学部を志望する理由は、将来国際法の分野で活躍したいという強い願いからです。

高校時代に模擬国連に参加した経験を通じて、国際社会の複雑な問題を法的な観点から解決することの重要性を実感しました。特に、人権問題や環境問題などのグローバルイシューに対して、法的枠組みを通じてアプローチすることの可能性を感じています。

東京大学法学部は、日本最高峰の法学教育を提供するだけでなく、国際的な視野を持った教授陣と充実した国際交流プログラムを有していることで知られています。特に、○○教授の国際人権法に関する研究に強い関心を持っており、ぜひご指導を受けたいと考えています。

また、貴学部の少人数ゼミナール制度を通じて、深い議論と批判的思考力を養いたいと思います。同級生との切磋琢磨を通じて、自分の考えを論理的に構築し、表現する能力を向上させることが目標です。

卒業後は、国際機関や外務省での勤務を視野に入れており、そのための基盤となる法学的思考と国際的な視野を貴学部で身につけたいと考えています。`,
    status: StatementStatus.DRAFT,
    universityName: "東京大学",
    departmentName: "法学部",
    keywords: ["国際法", "人権", "模擬国連", "外務省"],
    submissionDeadline: "2024-03-15",
    createdAt: "2024-01-15T09:00:00Z",
    updatedAt: "2024-01-20T14:30:00Z",
    wordCount: 487,
    feedbackCount: 2,
    selfAnalysisChatId: "self-analysis-1"
  },
  {
    id: "stmt-2",
    title: "早稲田大学政治経済学部志望理由書",
    content: `私が早稲田大学政治経済学部を志望する理由は、政治と経済の複合的な視点から社会問題にアプローチしたいからです。

現在の日本社会は、少子高齢化、格差拡大、地方創生など多くの課題に直面しています。これらの問題は単一の学問分野だけでは解決できず、政治学と経済学の知識を統合的に活用することが必要だと考えています。

早稲田大学政治経済学部は、この両分野を横断的に学べる日本でも数少ない学部です。特に、社会保障制度や税制に関する研究が充実しており、理論と実践を結びつけた学習ができる環境が整っています。

私は将来、地方自治体の政策立案に携わりたいと考えており、そのために必要な政策分析能力と経済的思考力を貴学部で培いたいと思います。`,
    status: StatementStatus.REVIEW,
    universityName: "早稲田大学", 
    departmentName: "政治経済学部",
    keywords: ["政治学", "経済学", "政策立案", "地方自治"],
    submissionDeadline: "2024-02-28",
    createdAt: "2024-01-10T10:00:00Z",
    updatedAt: "2024-01-25T16:45:00Z",
    wordCount: 324,
    feedbackCount: 1,
    selfAnalysisChatId: "self-analysis-2"
  },
  {
    id: "stmt-3",
    title: "慶應義塾大学商学部志望理由書",
    content: `私が慶應義塾大学商学部を志望する理由は、グローバルビジネスの最前線でリーダーシップを発揮したいという夢があるからです。

高校時代の起業体験を通じて、ビジネスの面白さと同時に、その複雑さと責任の重さを学びました。特に、マーケティングや財務管理の重要性を実感し、より体系的にビジネス学を学びたいと考えるようになりました。

慶應義塾大学商学部は、伝統ある商学教育と最新のビジネス理論を融合させた教育プログラムで知られています。また、多くの卒業生が各界で活躍しており、実践的な学びの場として最適だと考えています。`,
    status: StatementStatus.FINAL,
    universityName: "慶應義塾大学",
    departmentName: "商学部", 
    keywords: ["ビジネス", "起業", "マーケティング", "リーダーシップ"],
    createdAt: "2024-01-05T11:00:00Z",
    updatedAt: "2024-01-30T09:15:00Z",
    wordCount: 267,
    feedbackCount: 0
  }
];

// チャットセッションのモックデータ
export const mockChatSessions: ChatSession[] = [
  {
    id: "chat-1",
    title: "志望理由の論理構成について",
    createdAt: "2024-01-20T14:30:00Z",
    updatedAt: "2024-01-20T15:45:00Z",
    messageCount: 8
  },
  {
    id: "chat-2", 
    title: "表現の改善と文章校正",
    createdAt: "2024-01-18T10:00:00Z",
    updatedAt: "2024-01-18T11:30:00Z",
    messageCount: 12
  },
  {
    id: "chat-3",
    title: "新規チャット",
    createdAt: "2024-01-25T09:00:00Z",
    updatedAt: "2024-01-25T09:00:00Z",
    messageCount: 0
  }
];

// 自己分析チャットのモックデータ
export const mockSelfAnalysisChats: ChatSession[] = [
  {
    id: "self-analysis-1",
    title: "将来の目標と価値観について",
    createdAt: "2024-01-10T09:00:00Z",
    updatedAt: "2024-01-15T16:30:00Z",
    messageCount: 24
  },
  {
    id: "self-analysis-2",
    title: "これまでの経験と学び",
    createdAt: "2024-01-12T14:20:00Z",
    updatedAt: "2024-01-18T11:45:00Z",
    messageCount: 18
  },
  {
    id: "self-analysis-3",
    title: "強みと弱みの分析",
    createdAt: "2024-01-08T10:15:00Z",
    updatedAt: "2024-01-20T09:30:00Z",
    messageCount: 15
  },
  {
    id: "self-analysis-4",
    title: "興味のある分野と理由",
    createdAt: "2024-01-05T13:45:00Z",
    updatedAt: "2024-01-22T14:15:00Z",
    messageCount: 21
  }
];

// チャットメッセージのモックデータ
export const mockChatMessages: ChatMessage[] = [
  {
    id: "msg-1",
    sessionId: "chat-1",
    role: "user",
    content: "この志望理由書の論理構成について、改善点があれば教えてください。特に第2段落から第3段落への繋がりが気になっています。",
    timestamp: "2024-01-20T14:30:00Z"
  },
  {
    id: "msg-2",
    sessionId: "chat-1", 
    role: "assistant",
    content: "志望理由書を拝読しました。全体的に良い構成ですが、ご指摘の通り第2段落から第3段落への接続をもう少し明確にできそうです。\n\n具体的には、第2段落で述べた「国際社会の複雑な問題」が、第3段落の「東京大学法学部の特徴」とどう結びつくのかを明示的に示すと良いでしょう。\n\n例えば、「このような問題意識を持つ中で」や「これらの課題に取り組むために」といった接続表現を加えることをお勧めします。",
    timestamp: "2024-01-20T14:35:00Z"
  },
  {
    id: "msg-3",
    sessionId: "chat-1",
    role: "user", 
    content: "なるほど、接続表現を工夫すれば論理の流れがより明確になりますね。他にも全体的な構成で気をつけるべき点はありますか？",
    timestamp: "2024-01-20T14:40:00Z"
  },
  {
    id: "msg-4",
    sessionId: "chat-1",
    role: "assistant",
    content: "はい、他にも以下の点をご検討ください：\n\n1. **具体性の強化**: 「○○教授の研究」とありますが、具体的な研究内容や論文を挙げるとより説得力が増します。\n\n2. **将来性の明確化**: 「国際機関や外務省での勤務」という目標は素晴らしいですが、具体的にどのような役割で貢献したいかを示すとより良いでしょう。\n\n3. **独自性の強調**: 模擬国連の経験は良いエピソードですが、そこで得た具体的な学びや気づきをもう少し詳しく述べると、あなたらしさが伝わります。",
    timestamp: "2024-01-20T14:45:00Z"
  }
];

// フィードバックのモックデータ
export const mockFeedbacks: Feedback[] = [
  {
    id: "feedback-1",
    statementId: "stmt-1",
    authorName: "田中先生",
    content: "全体的に良い構成ですが、具体的な体験談をもう少し詳しく書いてみてください。模擬国連での具体的なエピソードがあると、より説得力のある志望理由書になります。",
    createdAt: "2024-01-22T10:00:00Z",
    type: "teacher"
  },
  {
    id: "feedback-2", 
    statementId: "stmt-1",
    authorName: "AIアシスタント",
    content: "文章の論理的な流れは良好です。ただし、第4段落の「同級生との切磋琢磨」の部分で、より具体的にどのような活動を通じて成長したいかを示すと良いでしょう。",
    createdAt: "2024-01-21T14:30:00Z",
    type: "ai"
  },
  {
    id: "feedback-3",
    statementId: "stmt-2", 
    authorName: "山田先生",
    content: "政治と経済の関連性について良く理解されていることが伝わります。地方自治体での政策立案という具体的な目標も明確で良いですね。",
    createdAt: "2024-01-26T11:15:00Z",
    type: "teacher"
  }
]; 
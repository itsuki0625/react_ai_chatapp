import React from 'react';
import { 
  MessageSquare, 
  FileText, 
  User, 
  Clock,
  ArrowRight 
} from 'lucide-react';
import DashboardCard from '@/components/dashboad/DashboardCard';
import ActivityCard from '@/components/dashboad/ActivityCard';
import NextStepsCard from '@/components/dashboad/NextStepsCard';

const DashboardPage = () => {
  const menuItems = [
    {
      title: "AIチャット",
      description: "AIと対話して自己理解を深めましょう",
      icon: MessageSquare,
      href: "/app/chat",
      stats: "新規チャット可能"
    },
    {
      title: "自己分析",
      description: "あなたの強みと可能性を発見しましょう",
      icon: User,
      href: "/self-analysis",
      stats: "30%完了"
    },
    {
      title: "志望理由書",
      description: "効果的な志望理由書を作成しましょう",
      icon: FileText,
      href: "/statement",
      stats: "下書き保存済み"
    }
  ];

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
        <div className="flex items-center space-x-2">
          <Clock className="h-5 w-5 text-gray-500" />
          <span className="text-sm text-gray-500">最終ログイン: 2024/12/21 10:30</span>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {menuItems.map((item, index) => (
          <DashboardCard
            key={index}
            title={item.title}
            description={item.description}
            icon={item.icon}
            href={item.href}
            stats={item.stats}
          />
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <ActivityCard />
        <NextStepsCard />
      </div>
    </div>
  );
};

export default DashboardPage;
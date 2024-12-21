const ActivityCard: React.FC = () => {
    const activities = [
      {
        id: 1,
        action: "志望理由書の下書きを保存しました",
        timestamp: "2時間前",
        type: "statement"
      },
      {
        id: 2,
        action: "AIチャットで自己分析を行いました",
        timestamp: "昨日",
        type: "chat"
      },
      {
        id: 3,
        action: "自己分析シートを更新しました",
        timestamp: "2日前",
        type: "analysis"
      }
    ];
  
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900">最近の活動</h3>
        <div className="mt-4 space-y-4">
          {activities.map(activity => (
            <div key={activity.id} className="flex items-start">
              <div className="w-2 h-2 mt-2 rounded-full bg-blue-500 flex-shrink-0" />
              <div className="ml-4">
                <p className="text-sm text-gray-900">{activity.action}</p>
                <p className="text-xs text-gray-500">{activity.timestamp}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
};

export default ActivityCard;
const NextStepsCard: React.FC = () => {
    const steps = [
      {
        id: 1,
        title: "志望理由書の添削を受けましょう",
        status: "未着手",
        priority: "high"
      },
      {
        id: 2,
        title: "自己分析を完了させましょう",
        status: "進行中",
        priority: "medium"
      },
      {
        id: 3,
        title: "面接対策を始めましょう",
        status: "未着手",
        priority: "low"
      }
    ];
  
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900">次のステップ</h3>
        <div className="mt-4 space-y-4">
          {steps.map(step => (
            <div key={step.id} className="flex items-start">
              <div
                className={`w-2 h-2 mt-2 rounded-full flex-shrink-0 
                  ${step.priority === 'high' ? 'bg-red-500' : 
                    step.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'}`}
              />
              <div className="ml-4">
                <p className="text-sm text-gray-900">{step.title}</p>
                <p className="text-xs text-gray-500">{step.status}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
};

export default NextStepsCard;
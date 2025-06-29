import React from 'react';
import { SubscriptionPlan } from '@/types/subscription';
import { Button } from '@/components/ui/button';

interface PlanCardProps {
  plan: SubscriptionPlan;
  currentPlanId?: string | null;
  onSelectPlan: (planId: string) => void;
  isLoading?: boolean;
}

export const PlanCard: React.FC<PlanCardProps> = ({
  plan,
  currentPlanId,
  onSelectPlan,
  isLoading = false
}) => {
  const isCurrentPlan = currentPlanId === plan.id;
  
  // 金額をフォーマット
  const formatAmount = (amount: number, currency: string): string => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: currency.toUpperCase(),
      minimumFractionDigits: 0
    }).format(amount);
  };
  
  // 請求周期を日本語表示
  const getIntervalLabel = (interval: string): string => {
    switch (interval) {
      case 'month':
        return '月額';
      case 'year':
        return '年額';
      default:
        return interval;
    }
  };
  
  return (
    <div className={`border rounded-lg p-6 shadow-sm ${isCurrentPlan ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
      <div className="mb-4">
        {isCurrentPlan && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mb-2">
            現在のプラン
          </span>
        )}
        <h3 className="text-xl font-bold">{plan.name}</h3>
      </div>
      
      <div className="mb-4">
        <span className="text-3xl font-bold">
          {formatAmount(plan.amount, plan.currency)}
        </span>
        <span className="text-gray-500 ml-1">/ {getIntervalLabel(plan.interval)}</span>
      </div>
      
      {plan.description && (
        <div className="text-gray-600 mb-6">
          {plan.description}
        </div>
      )}
      
      <Button
        onClick={() => onSelectPlan(plan.id)}
        disabled={isLoading}
        variant={isCurrentPlan ? "outline" : "default"}
        className="w-full"
      >
        {isCurrentPlan ? '現在のプラン' : '選択する'}
      </Button>
    </div>
  );
}; 
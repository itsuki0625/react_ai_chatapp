import React, { useState } from 'react';
import { VerifyCampaignCodeResponse } from '@/types/subscription';
import { Input } from '@/components/common/Input';
import { Button } from '@/components/common/Button';

interface CampaignCodeFormProps {
  onSubmit: (code: string) => Promise<VerifyCampaignCodeResponse>;
  onApply: (response: VerifyCampaignCodeResponse) => void;
  originalAmount: number;
  currency: string;
}

export const CampaignCodeForm: React.FC<CampaignCodeFormProps> = ({
  onSubmit,
  onApply,
  originalAmount,
  currency
}) => {
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerifyCampaignCodeResponse | null>(null);
  
  // 金額をフォーマット
  const formatAmount = (amount: number, curr: string): string => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: curr.toUpperCase(),
      minimumFractionDigits: 0
    }).format(amount);
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code) return;
    
    setError(null);
    setIsLoading(true);
    
    try {
      const result = await onSubmit(code);
      setVerificationResult(result);
      
      if (result.valid) {
        onApply(result);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError('キャンペーンコードの検証中にエラーが発生しました');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="mt-4 border border-gray-200 rounded-lg p-4">
      <h4 className="font-medium mb-2">キャンペーンコード</h4>
      
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-grow">
          <Input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="コードを入力"
            disabled={isLoading || !!verificationResult?.valid}
          />
        </div>
        <Button
          type="submit"
          variant="secondary"
          disabled={!code || isLoading || !!verificationResult?.valid}
        >
          {isLoading ? '検証中...' : '適用'}
        </Button>
      </form>
      
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      
      {verificationResult?.valid && (
        <div className="mt-4 bg-green-50 p-3 rounded-md">
          <p className="text-green-700 font-medium">
            キャンペーンコード「{code}」が適用されました
          </p>
          {verificationResult.discount_type && verificationResult.discount_value && (
            <p className="text-sm text-green-600">
              {verificationResult.discount_type === 'percentage' 
                ? `${verificationResult.discount_value}%割引` 
                : `${formatAmount(verificationResult.discount_value, currency)}割引`}
            </p>
          )}
          {verificationResult.original_amount && verificationResult.discounted_amount && (
            <div className="mt-2 flex items-center">
              <span className="text-gray-500 line-through mr-2">
                {formatAmount(verificationResult.original_amount, currency)}
              </span>
              <span className="text-green-700 font-bold">
                {formatAmount(verificationResult.discounted_amount, currency)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}; 
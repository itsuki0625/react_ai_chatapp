import React, { useState } from 'react';
import { VerifyCampaignCodeResponse } from '@/types/subscription';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface CampaignCodeFormProps {
  onSubmit: (code: string) => Promise<VerifyCampaignCodeResponse>;
  onApply?: (response: VerifyCampaignCodeResponse) => void;
  currency?: string;
  initialCode?: string;
  onCodeChange?: (code: string) => void;
  isLoading?: boolean;
}

export const CampaignCodeForm: React.FC<CampaignCodeFormProps> = ({
  onSubmit,
  onApply,
  currency = 'jpy',
  initialCode = '',
  onCodeChange,
  isLoading: propIsLoading
}) => {
  const [campaignCode, setCampaignCode] = useState<string>(initialCode);
  const [internalIsLoading, setInternalIsLoading] = useState(false);
  const isLoading = propIsLoading ?? internalIsLoading;
  const [error, setError] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerifyCampaignCodeResponse | null>(null);
  
  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newCode = e.target.value;
    setCampaignCode(newCode);
    setError(null);
    setVerificationResult(null);
    if (onCodeChange) {
      onCodeChange(newCode);
    }
  };
  
  const formatAmount = (amount: number | null | undefined, curr: string): string => {
    if (amount === null || amount === undefined) {
      return '-';
    }
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: curr.toUpperCase(),
      minimumFractionDigits: 0
    }).format(amount);
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!campaignCode || isLoading) return;
    
    setError(null);
    setInternalIsLoading(true);
    
    try {
      const result = await onSubmit(campaignCode);
      setVerificationResult(result);
      
      if (result.valid) {
        if (onApply) {
          onApply(result);
        }
      } else {
        setError(result.message || '入力されたキャンペーンコードは無効です。');
      }
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : typeof error === 'object' && error !== null && 'response' in error && typeof error.response === 'object' && error.response !== null && 'data' in error.response && typeof error.response.data === 'object' && error.response.data !== null && 'detail' in error.response.data && typeof error.response.data.detail === 'string'
            ? error.response.data.detail 
            : 'キャンペーンコードの検証中にエラーが発生しました';
      setError(errorMessage);
      console.error(error);
    } finally {
      setInternalIsLoading(false);
    }
  };
  
  const isResultValid = (result: VerifyCampaignCodeResponse | null): boolean => {
    return result?.valid ?? false;
  };
  
  const getDiscountDisplay = (result: VerifyCampaignCodeResponse) => {
    if (!result.valid) return null;
    
    const discountType = result.discount_type;
    const discountValue = result.discount_value;
    
    if (discountType && discountValue !== null) {
      return discountType === 'percentage'
        ? `${discountValue}%割引`
        : `${formatAmount(discountValue, currency)}割引`;
    }
    return "割引適用";
  };
  
  const getOriginalAmountDisplay = (result: VerifyCampaignCodeResponse) => {
    return result.original_amount;
  };
  
  const getDiscountedAmountDisplay = (result: VerifyCampaignCodeResponse) => {
    return result.discounted_amount;
  };
  
  return (
    <div className="mt-4 border border-gray-200 rounded-lg p-4">
      <h4 className="font-medium mb-2">キャンペーンコード</h4>
      
      {!isResultValid(verificationResult) ? (
        <form onSubmit={handleSubmit} className="flex gap-2 items-start">
          <div className="flex-grow">
            <label htmlFor="campaign-code" className="sr-only">
              キャンペーンコード
            </label>
            <Input
              id="campaign-code"
              name="campaign-code"
              autoComplete="off"
              value={campaignCode}
              onChange={handleCodeChange}
              placeholder="コードを入力"
              disabled={isLoading}
              className="h-10"
            />
          </div>
          <Button
            type="submit"
            variant="secondary"
            disabled={!campaignCode || isLoading}
            className="h-10"
          >
            {isLoading ? '検証中...' : '適用'}
          </Button>
        </form>
      ) : null}
      
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      
      {isResultValid(verificationResult) && verificationResult && (
        <div className="mt-4 bg-green-50 p-3 rounded-md border border-green-200">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-green-700 font-medium">
                コード「{campaignCode}」適用済み
              </p>
              <p className="text-sm text-green-600">
                {getDiscountDisplay(verificationResult)}
              </p>
            </div>
          </div>
          {getOriginalAmountDisplay(verificationResult) !== null && getDiscountedAmountDisplay(verificationResult) !== null && (
            <div className="mt-2 flex items-center">
              <span className="text-gray-500 line-through mr-2">
                {formatAmount(getOriginalAmountDisplay(verificationResult), currency)}
              </span>
              <span className="text-green-700 font-bold">
                {formatAmount(getDiscountedAmountDisplay(verificationResult), currency)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}; 
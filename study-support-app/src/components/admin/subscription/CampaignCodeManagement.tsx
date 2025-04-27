"use client";

import React, { useState, useEffect } from 'react';
import { PlusCircle, Edit, Trash2, AlertCircle, Check, X } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card, CardContent } from '@/components/common/Card';
import { CampaignCode, DiscountTypeResponse } from '@/types/subscription';
import { adminService } from '@/services/adminService';
import { fetchDiscountTypes } from '@/lib/api/admin';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

// モーダルの共通コンポーネント
const Modal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h3 className="text-xl font-semibold">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="px-6 py-4">
          {children}
        </div>
      </div>
    </div>
  );
};

// 入力フィールドのコンポーネント
const FormField: React.FC<{
  label: string;
  children: React.ReactNode;
  error?: string;
}> = ({ label, children, error }) => {
  return (
    <div className="mb-4">
      <label className="block text-gray-700 text-sm font-medium mb-2">
        {label}
      </label>
      {children}
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};

// 入力コンポーネント
const Input: React.FC<{
  type?: string;
  value: string | number;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  required?: boolean;
  min?: number;
  step?: string;
  name?: string;
}> = ({ type = "text", value, onChange, placeholder, required, min, step, name }) => {
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      required={required}
      min={min}
      step={step}
      name={name}
      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
    />
  );
};

// チェックボックスコンポーネント
const Checkbox: React.FC<{
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  label: string;
  name?: string;
}> = ({ checked, onChange, label, name }) => {
  return (
    <label className="inline-flex items-center">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        name={name}
        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
      />
      <span className="ml-2 text-gray-700">{label}</span>
    </label>
  );
};

// セレクトコンポーネント
const Select: React.FC<{
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  options: { value: string; label: string }[];
  required?: boolean;
  name?: string;
}> = ({ value, onChange, options, required, name }) => {
  return (
    <select
      value={value}
      onChange={onChange}
      required={required}
      name={name}
      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
    >
      <option value="">選択してください</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
};

export const CampaignCodeManagement: React.FC = () => {
  const [campaignCodes, setCampaignCodes] = useState<CampaignCode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [currentCode, setCurrentCode] = useState<CampaignCode | null>(null);
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  
  // 割引タイプ取得用の useQuery
  const { data: discountTypes = [], isLoading: isLoadingDiscountTypes, error: discountTypesError } = useQuery<DiscountTypeResponse[]>({
    queryKey: ['adminDiscountTypes'],
    queryFn: fetchDiscountTypes
  });

  // 新規キャンペーンコードのフォーム状態
  const [newCode, setNewCode] = useState({
    code: '',
    description: '',
    discount_type: '',
    discount_value: '',
    max_uses: '',
    valid_from: '',
    valid_until: '',
    is_active: true
  });

  useEffect(() => {
    fetchCampaignCodes();
  }, []);

  const fetchCampaignCodes = async () => {
    try {
      setIsLoading(true);
      const data = await adminService.getCampaignCodes();
      setCampaignCodes(data || []);
    } catch (err) {
      console.error('キャンペーンコードの取得中にエラーが発生しました:', err);
      setError(err instanceof Error ? err.message : 'キャンペーンコードの取得中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setNewCode({
      code: '',
      description: '',
      discount_type: '',
      discount_value: '',
      max_uses: '',
      valid_from: '',
      valid_until: '',
      is_active: true
    });
    setFormErrors({});
  };

  const handleAddCampaignCode = () => {
    resetForm();
    setIsAddModalOpen(true);
  };

  const handleEditCampaignCode = (code: CampaignCode) => {
    setCurrentCode(code);
    
    // 日付フォーマット変換（yyyy-MM-dd形式に変換）
    const formatDateForInput = (dateString: string | null) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toISOString().split('T')[0];
    };
    
    // 編集フォームの初期値を設定
    setNewCode({
      code: code.code,
      description: code.description || '',
      discount_type: code.discount_type,
      discount_value: String(code.discount_value),
      max_uses: code.max_uses ? String(code.max_uses) : '',
      valid_from: formatDateForInput(code.valid_from),
      valid_until: formatDateForInput(code.valid_until),
      is_active: code.is_active
    });
    
    setFormErrors({});
    setIsEditModalOpen(true);
  };

  const handleDeleteCampaignCode = async (codeId: string) => {
    if (!confirm('このキャンペーンコードを削除してもよろしいですか？')) {
      return;
    }

    try {
      await adminService.deleteCampaignCode(codeId);
      // 成功したらキャンペーンコードリストを更新
      fetchCampaignCodes();
    } catch (err) {
      console.error('キャンペーンコードの削除中にエラーが発生しました:', err);
      alert(err instanceof Error ? err.message : 'キャンペーンコードの削除中にエラーが発生しました');
    }
  };

  // フォームの入力値変更ハンドラ
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    setNewCode(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
    
    // エラーをクリア
    if (formErrors[name]) {
      setFormErrors(prev => {
        const errors = { ...prev };
        delete errors[name];
        return errors;
      });
    }
  };

  // キャンペーンコードを作成/更新する
  const handleSubmitCampaignCode = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // フォームのバリデーション
    const errors: { [key: string]: string } = {};
    
    if (!newCode.code.trim()) {
      errors.code = 'コードを入力してください';
    }
    
    if (!newCode.discount_type) {
      errors.discount_type = '割引タイプを選択してください';
    }
    
    if (!newCode.discount_value) {
      errors.discount_value = '割引値を入力してください';
    } else {
      const discountValue = Number(newCode.discount_value);
      if (isNaN(discountValue) || discountValue <= 0) {
        errors.discount_value = '有効な割引値を入力してください';
      } else if (newCode.discount_type === 'percentage' && discountValue > 100) {
        errors.discount_value = 'パーセンテージは100%以下にしてください';
      }
    }
    
    // 日付の検証
    if (newCode.valid_from && newCode.valid_until) {
      const fromDate = new Date(newCode.valid_from);
      const untilDate = new Date(newCode.valid_until);
      if (fromDate > untilDate) {
        errors.valid_until = '終了日は開始日より後にしてください';
      }
    }
    
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    
    try {
      // 日付をISO 8601形式 (UTCの日の始まり) に変換するヘルパー関数
      const toISOStartOfDayUTC = (dateString: string | undefined): string | undefined => {
        if (!dateString) return undefined;
        try {
          const date = new Date(dateString + 'T00:00:00Z'); // UTCとして解釈
          return date.toISOString();
        } catch (e) {
          console.error("Invalid date format:", dateString);
          return undefined; // 無効な場合は undefined を返す
        }
      };

      const campaignCodeData = {
        code: newCode.code.trim(),
        description: newCode.description.trim() || undefined,
        discount_type: newCode.discount_type as 'percentage' | 'fixed',
        discount_value: Number(newCode.discount_value),
        max_uses: newCode.max_uses ? Number(newCode.max_uses) : undefined,
        valid_from: toISOStartOfDayUTC(newCode.valid_from),
        valid_until: toISOStartOfDayUTC(newCode.valid_until),
        is_active: newCode.is_active
      };
      
      console.log("Submitting Campaign Code Data:", campaignCodeData); // 送信データを確認

      if (isEditModalOpen && currentCode) {
        // 現在のAPIでは更新エンドポイントがないため、
        // バックエンドでPUTエンドポイントを実装する必要があります
        // 一時的に新しいコードを作成するようにしています
        // TODO: Implement update logic using PUT /admin/campaign-codes/{codeId}
        console.warn("Campaign code edit currently uses create logic. Implement PUT endpoint.");
        await adminService.createCampaignCode(campaignCodeData); 
        alert("キャンペーンコードが（新規作成として）保存されました。更新処理は未実装です。");
      } else {
        await adminService.createCampaignCode(campaignCodeData);
        alert("キャンペーンコードが作成されました。"); // 成功時のメッセージ変更
      }
      
      // モーダルを閉じてキャンペーンコードリストを更新
      setIsAddModalOpen(false);
      setIsEditModalOpen(false);
      fetchCampaignCodes();
      resetForm();
    } catch (err) {
      console.error('キャンペーンコードの保存中にエラーが発生しました:', err);
      // エラーハンドリング改善 (Axios エラーチェック)
      let errorMessage = 'キャンペーンコードの保存中にエラーが発生しました';
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
          // バックエンドからの詳細エラーメッセージを表示
          errorMessage = `エラー: ${err.response.data.detail}`;
          if (typeof err.response.data.detail === 'string') {
              errorMessage = `エラー: ${err.response.data.detail}`;
          } else if (Array.isArray(err.response.data.detail)) {
              // バリデーションエラーの詳細を整形
              errorMessage = "エラー: 入力内容を確認してください。\n" + 
                  err.response.data.detail.map((d: any) => `${d.loc.join('.')} - ${d.msg}`).join("\n");
          } 
      } else if (err instanceof Error) {
          errorMessage = err.message;
      }
      alert(errorMessage);
    }
  };

  // 割引情報のフォーマット
  const formatDiscount = (code: CampaignCode) => {
    if (code.discount_type === 'percentage') {
      return `${code.discount_value}%割引`;
    } else {
      return `${code.discount_value.toLocaleString()}円割引`;
    }
  };

  // 日付のフォーマット
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '設定なし';
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const renderCampaignCodeForm = () => {
    // 割引タイプロード中の表示
    if (isLoadingDiscountTypes) {
        return <div>割引タイプを読み込み中...</div>;
    }
    // 割引タイプ取得エラー表示
    if (discountTypesError) {
        return <div className="text-red-500">割引タイプの読み込みに失敗しました: {discountTypesError.message}</div>;
    }

    return (
      <form onSubmit={handleSubmitCampaignCode}>
        <FormField label="キャンペーンコード" error={formErrors.code}>
          <Input
            value={newCode.code}
            onChange={handleInputChange}
            name="code"
            placeholder="例: WELCOME2023"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            * ユーザーが入力するコードです（大文字小文字を区別します）
          </p>
        </FormField>
        
        <FormField label="説明">
          <Input
            value={newCode.description}
            onChange={handleInputChange}
            name="description"
            placeholder="例: 新規ユーザー向けキャンペーン"
          />
        </FormField>
        
        <FormField label="割引タイプ" error={formErrors.discount_type}>
          <Select
            value={newCode.discount_type}
            onChange={handleInputChange}
            name="discount_type"
            required
            options={discountTypes.map(dt => ({
                value: dt.name,
                label: `${dt.name}${dt.description ? ` (${dt.description})` : ''}`
            }))}
          />
        </FormField>
        
        <FormField label="割引値" error={formErrors.discount_value}>
          <div className="flex items-center">
            <Input
              type="number"
              value={newCode.discount_value}
              onChange={handleInputChange}
              name="discount_value"
              placeholder={newCode.discount_type === 'percentage' ? '例: 10' : '例: 1000'}
              required
              min={0}
              step={newCode.discount_type === 'percentage' ? '1' : '100'}
            />
            <span className="ml-2">
              {newCode.discount_type === 'percentage' ? '%' : '円'}
            </span>
          </div>
        </FormField>
        
        <FormField label="最大使用回数">
          <Input
            type="number"
            value={newCode.max_uses}
            onChange={handleInputChange}
            name="max_uses"
            placeholder="例: 100 (空白の場合は無制限)"
            min={1}
          />
        </FormField>
        
        <div className="grid grid-cols-2 gap-4">
          <FormField label="有効期間開始日">
            <Input
              type="date"
              value={newCode.valid_from}
              onChange={handleInputChange}
              name="valid_from"
            />
          </FormField>
          
          <FormField label="有効期間終了日" error={formErrors.valid_until}>
            <Input
              type="date"
              value={newCode.valid_until}
              onChange={handleInputChange}
              name="valid_until"
            />
          </FormField>
        </div>
        
        <FormField label="ステータス">
          <Checkbox
            checked={newCode.is_active}
            onChange={handleInputChange}
            name="is_active"
            label="このキャンペーンコードを有効にする"
          />
        </FormField>
        
        <div className="flex justify-end space-x-3 mt-6">
          <Button
            variant="outline"
            onClick={() => {
              setIsAddModalOpen(false);
              setIsEditModalOpen(false);
            }}
          >
            キャンセル
          </Button>
          <Button type="submit" variant="primary">
            {isEditModalOpen ? '更新する' : '作成する'}
          </Button>
        </div>
      </form>
    );
  };

  const renderCampaignCodeList = () => {
    if (isLoading) {
      return <div className="text-center py-8">キャンペーンコードを読み込み中...</div>;
    }

    if (error) {
      return (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 mt-0.5" />
          <span>{error}</span>
        </div>
      );
    }

    if (campaignCodes.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          キャンペーンコードが登録されていません
        </div>
      );
    }

    return (
      <div className="grid gap-4">
        {campaignCodes.map((code) => (
          <Card key={code.id} className="overflow-hidden">
            <CardContent className="p-0">
              <div className="p-4 flex justify-between items-center">
                <div className="flex-grow">
                  <div className="flex items-center">
                    <h3 className="font-medium text-lg">{code.code}</h3>
                    <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      code.is_valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {code.is_valid ? '有効' : '無効'}
                    </span>
                  </div>
                  
                  <p className="text-gray-500 text-sm mt-1">
                    {code.description || 'キャンペーンコードの説明なし'}
                  </p>
                  
                  <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                    <div className="flex items-center">
                      <span className="text-gray-600 mr-1">割引:</span>
                      <span className="font-medium">{formatDiscount(code)}</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-gray-600 mr-1">使用回数:</span>
                      <span className="font-medium">
                        {code.used_count} / {code.max_uses || '無制限'}
                      </span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-gray-600 mr-1">開始日:</span>
                      <span>{formatDate(code.valid_from)}</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-gray-600 mr-1">終了日:</span>
                      <span>{formatDate(code.valid_until)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditCampaignCode(code)}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    編集
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteCampaignCode(code.id)}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    削除
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">キャンペーンコード管理</h2>
        <Button variant="primary" onClick={handleAddCampaignCode}>
          <PlusCircle className="h-4 w-4 mr-2" />
          コードを追加
        </Button>
      </div>

      {renderCampaignCodeList()}

      {/* キャンペーンコード追加モーダル */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="新しいキャンペーンコードを追加"
      >
        {renderCampaignCodeForm()}
      </Modal>

      {/* キャンペーンコード編集モーダル */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="キャンペーンコードを編集"
      >
        {renderCampaignCodeForm()}
      </Modal>
    </div>
  );
};
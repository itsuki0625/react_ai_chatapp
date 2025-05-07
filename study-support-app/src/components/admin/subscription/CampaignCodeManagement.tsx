"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PlusCircle, Edit, Trash2, AlertCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/common/Card';
import { CampaignCode, CampaignCodeCreatePayload, DiscountTypeResponse } from '@/types/subscription';
import { StripeCouponResponse } from '@/types/coupon';
import { adminService } from '@/services/adminService';
import { couponAdminService } from '@/services/couponService';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';

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
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [currentCode, setCurrentCode] = useState<CampaignCode | null>(null);
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [showCreateForm, setShowCreateForm] = useState(false);
  const queryClient = useQueryClient();

  const { data: campaignCodesData, isLoading: isLoadingCampaignCodes, refetch: refetchCampaignCodes } = useQuery<CampaignCode[]>({
    queryKey: ['adminCampaignCodes'],
    queryFn: () => adminService.getCampaignCodes().then(data => data || []),
    initialData: [],
  });

  const { data: coupons, isLoading: isLoadingCoupons, error: couponsError } = useQuery<StripeCouponResponse[], Error>({
    queryKey: ['adminStripeCoupons'],
    queryFn: () => couponAdminService.listAdminDbCoupons(100),
  });

  const [newCode, setNewCode] = useState({
    code: '',
    description: '',
    stripe_coupon_id: '',
    max_uses: '',
    valid_from: '',
    valid_until: '',
    is_active: true
  });

  useEffect(() => {
  }, []);

  const resetForm = () => {
    setNewCode({
      code: '',
      description: '',
      stripe_coupon_id: '',
      max_uses: '',
      valid_from: '',
      valid_until: '',
      is_active: true
    });
    setFormErrors({});
  };

  const handleEditCampaignCode = (code: CampaignCode) => {
    setCurrentCode(code);
    const formatDateForInput = (dateString: string | null | undefined) => {
      if (!dateString) return '';
      try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return '';
        return date.toISOString().split('T')[0];
      } catch (e) {
        console.error("Error formatting date:", dateString, e);
        return '';
      }
    };
    setNewCode({
      code: code.code,
      description: code.description || '',
      stripe_coupon_id: code.coupon_id || '',
      max_uses: code.max_uses ? String(code.max_uses) : '',
      valid_from: formatDateForInput(code.valid_from),
      valid_until: formatDateForInput(code.valid_until),
      is_active: code.is_active
    });
    setFormErrors({});
    setIsEditModalOpen(true);
  };

  const { toast } = useToast();

  const createCampaignCodeMutation = useMutation<
    CampaignCode,
    Error,
    CampaignCodeCreatePayload
  >({
    mutationFn: adminService.createCampaignCode,
    onSuccess: (data) => {
      toast({ title: "成功", description: `キャンペーンコード「${data.code}」が作成されました。` });
      queryClient.invalidateQueries({ queryKey: ['adminCampaignCodes'] });
      setShowCreateForm(false);
      resetForm();
    },
    onError: (error) => {
      console.error("キャンペーンコード作成エラー:", error);
      let detail = "キャンペーンコードの作成に失敗しました。";
      if (axios.isAxiosError(error)) {
        detail = error.response?.data?.detail || error.message;
      } else if (error instanceof Error) {
        detail = error.message;
      }
      toast({ variant: "destructive", title: "作成エラー", description: detail });
    },
  });

  const handleDeleteCampaignCode = async (codeId: string) => {
    if (!confirm('このキャンペーンコードを削除してもよろしいですか？')) {
      return;
    }
    try {
      await adminService.deleteCampaignCode(codeId);
      toast({ title: "成功", description: "キャンペーンコードが削除されました。" });
      queryClient.invalidateQueries({ queryKey: ['adminCampaignCodes'] });
    } catch (err) {
      console.error('キャンペーンコードの削除中にエラーが発生しました:', err);
      const detail = err instanceof Error ? err.message : 'キャンペーンコードの削除中にエラーが発生しました';
      toast({ variant: "destructive", title: "削除エラー", description: detail });
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    setNewCode(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
    if (formErrors[name]) {
      setFormErrors(prev => { const errors = { ...prev }; delete errors[name]; return errors; });
    }
  };

  const handleSubmitNewCampaignCode = async () => {
    setFormErrors({});
    let errors: { [key: string]: string } = {};

    if (!newCode.code) errors.code = "コードは必須です";
    if (!newCode.stripe_coupon_id) errors.stripe_coupon_id = "StripeクーポンIDは必須です";
    if (newCode.max_uses && (isNaN(Number(newCode.max_uses)) || Number(newCode.max_uses) < 0)) {
        errors.max_uses = "最大使用回数は0以上の数値で入力してください";
    }
    if (newCode.valid_from && isNaN(new Date(newCode.valid_from).getTime())) {
        errors.valid_from = "有効開始日が不正な日付形式です";
    }
    if (newCode.valid_until && isNaN(new Date(newCode.valid_until).getTime())) {
        errors.valid_until = "有効終了日が不正な日付形式です";
    }
    if (newCode.valid_from && newCode.valid_until && new Date(newCode.valid_from) > new Date(newCode.valid_until)) {
        errors.valid_until = "有効終了日は有効開始日より後の日付である必要があります";
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    const payload: CampaignCodeCreatePayload = {
      code: newCode.code,
      description: newCode.description || null,
      stripe_coupon_id: newCode.stripe_coupon_id,
      max_uses: newCode.max_uses ? parseInt(newCode.max_uses, 10) : null,
      valid_from: newCode.valid_from ? new Date(newCode.valid_from).toISOString() : null,
      valid_until: newCode.valid_until ? new Date(newCode.valid_until).toISOString() : null,
      is_active: newCode.is_active,
    };

    console.log("Creating campaign code with payload:", payload);

    try {
      await createCampaignCodeMutation.mutateAsync(payload);
    } catch (error) {
      console.error("Caught mutation error in handleSubmit:", error);
    }
  };

  const handleUpdateCampaignCode = async () => {
    toast({ title: "未実装", description: "キャンペーンコードの更新機能は未実装です。" });
    setIsEditModalOpen(false);
  };

  const formatDiscount = (code: CampaignCode) => {
    if (code.discount_type === 'percentage') {
      return `${code.discount_value}%割引`;
    } else {
      return `${code.discount_value.toLocaleString()}円割引`;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '設定なし';
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const renderCreateCampaignCodeForm = () => (
    <Card className="mb-6 border border-blue-200 bg-blue-50">
      <CardContent className="pt-6">
        <h3 className="text-lg font-semibold mb-4 text-blue-800">新規キャンペーンコード作成</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="コード *" error={formErrors.code}>
            <Input name="code" value={newCode.code} onChange={handleInputChange} placeholder="例: WELCOME2024" required />
          </FormField>
          <FormField label="紐付けるStripe Coupon *" error={formErrors.stripe_coupon_id}>
            <Select
              name="stripe_coupon_id"
              value={newCode.stripe_coupon_id}
              onChange={handleInputChange}
              options={coupons?.map(c => ({ 
                value: c.stripe_coupon_id,
                label: `${c.name || c.stripe_coupon_id} (ID: ${c.stripe_coupon_id})`
              })) || []}
              required
            />
            {isLoadingCoupons && <p className="text-sm text-gray-500 mt-1">クーポン読み込み中...</p>}
            {couponsError && <p className="text-sm text-red-600 mt-1">クーポン読み込みエラー: {couponsError.message}</p>}
          </FormField>
          <FormField label="説明" error={formErrors.description}>
            <Input name="description" value={newCode.description} onChange={handleInputChange} placeholder="例: 初回ユーザー向け割引" />
          </FormField>
          <FormField label="最大利用回数" error={formErrors.max_uses}>
            <Input type="number" name="max_uses" value={newCode.max_uses} onChange={handleInputChange} placeholder="未入力の場合は無制限" min={1} />
          </FormField>
          <FormField label="有効期限（開始）" error={formErrors.valid_from}>
            <Input type="date" name="valid_from" value={newCode.valid_from} onChange={handleInputChange} />
          </FormField>
          <FormField label="有効期限（終了）" error={formErrors.valid_until}>
            <Input type="date" name="valid_until" value={newCode.valid_until} onChange={handleInputChange} />
          </FormField>
        </div>
        <div className="mt-4">
          <Checkbox name="is_active" checked={newCode.is_active} onChange={handleInputChange} label="有効" />
        </div>
        <div className="flex justify-end space-x-3 mt-6">
          <Button variant="outline" onClick={() => { setShowCreateForm(false); resetForm(); }}>キャンセル</Button>
          <Button onClick={handleSubmitNewCampaignCode} disabled={createCampaignCodeMutation.isPending}>
            {createCampaignCodeMutation.isPending ? "作成中..." : "作成"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderCampaignCodeList = () => {
    if (isLoadingCampaignCodes) return <p>キャンペーンコードを読み込み中...</p>;
    if (error) return <p className="text-red-600">エラー: {error}</p>;
    if (!campaignCodesData || campaignCodesData.length === 0) return <p>利用可能なキャンペーンコードはありません。</p>;

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">コード</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">説明</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">紐付けCoupon</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最大利用/利用済</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">有効期間</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状態</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {campaignCodesData.map((code) => (
              <tr key={code.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{code.code}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{code.description || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono text-xs">{code.coupon_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {code.max_uses ? `${code.used_count} / ${code.max_uses}` : `${code.used_count} / 無制限`}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {code.valid_from ? formatDate(code.valid_from) : '-'} ~ {code.valid_until ? formatDate(code.valid_until) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${code.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {code.is_active ? '有効' : '無効'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <Button variant="ghost" size="sm" onClick={() => handleEditCampaignCode(code)} className="mr-2">
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDeleteCampaignCode(code.id)} className="text-red-600 hover:text-red-700">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderEditCampaignCodeModal = () => (
    <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="キャンペーンコード編集">
      <p>キャンペーンコード: {currentCode?.code}</p>
      <p className="text-sm text-muted-foreground mt-4">更新機能は現在実装中です。</p>
      <div className="flex justify-end space-x-3 mt-6">
        <Button variant="outline" onClick={() => setIsEditModalOpen(false)}>キャンセル</Button>
        <Button onClick={handleUpdateCampaignCode}>更新</Button>
      </div>
    </Modal>
  );

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">キャンペーンコード管理</h2>
          <Button onClick={() => setShowCreateForm(!showCreateForm)} variant="default">
            <PlusCircle className="mr-2 h-4 w-4" /> {showCreateForm ? 'フォームを閉じる' : '新規作成'}
          </Button>
        </div>

        {showCreateForm && renderCreateCampaignCodeForm()}

        {renderCampaignCodeList()}

        {renderEditCampaignCodeModal()}

      </CardContent>
    </Card>
  );
};
"use client";

import React, { useState, useEffect } from 'react';
import { PlusCircle, Edit, Trash2, AlertCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { adminService } from '@/services/adminService';
import {
  StripePriceResponse,
  StripeProductResponse,
  StripeProductWithPricesResponse
} from '@/types/stripe';
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

export const PriceList: React.FC = () => {
  const [prices, setPrices] = useState<StripePriceResponse[]>([]);
  const [products, setProducts] = useState<StripeProductWithPricesResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [currentPrice, setCurrentPrice] = useState<StripePriceResponse | null>(null);
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [showInactivePrices, setShowInactivePrices] = useState(() => {
    // ローカルストレージから設定を読み込む（デフォルトはtrue）
    if (typeof window !== 'undefined') {
      const savedSetting = localStorage.getItem('showInactivePrices');
      return savedSetting === null ? true : savedSetting === 'true';
    }
    return true;
  });
  
  // 新規価格設定のフォーム状態
  const [newPrice, setNewPrice] = useState({
    product: '',
    unit_amount: '',
    currency: 'jpy',
    type: 'recurring',
    interval: 'month',
    interval_count: '1',
    nickname: ''
  });

  useEffect(() => {
    Promise.all([fetchPrices(), fetchProducts()]);
  }, []);

  // 表示設定が変更されたらローカルストレージに保存
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('showInactivePrices', String(showInactivePrices));
    }
  }, [showInactivePrices]);

  const fetchPrices = async () => {
    try {
      setIsLoading(true);
      const data = await adminService.getPrices();
      
      if (Array.isArray(data)) {
        setPrices(data);
      } else {
        console.error('予期せぬAPIレスポンス形式です:', data);
        setPrices([]);
        setError('価格データの形式が不正です。管理者に連絡してください。');
      }
    } catch (err) {
      console.error('価格の取得中にエラーが発生しました:', err);
      setPrices([]);
      setError(err instanceof Error ? err.message : '価格の取得中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const data = await adminService.getProducts();
      setProducts(data || []);
    } catch (err) {
      console.error('商品の取得中にエラーが発生しました:', err);
    }
  };

  const resetForm = () => {
    setNewPrice({
      product: '',
      unit_amount: '',
      currency: 'jpy',
      type: 'recurring',
      interval: 'month',
      interval_count: '1',
      nickname: ''
    });
    setFormErrors({});
  };

  const handleAddPrice = () => {
    resetForm();
    setIsAddModalOpen(true);
  };

  const handleEditPrice = (price: StripePriceResponse) => {
    setCurrentPrice(price);

    let displayAmount = '0'; // デフォルト値を設定
    if (price.unit_amount !== null && price.unit_amount !== undefined) {
      if (price.currency.toLowerCase() === 'jpy') {
        displayAmount = String(price.unit_amount);
      } else {
        // JPY以外の場合、100で割って小数点以下2桁まで表示する可能性を考慮
        // ただし、StripePriceResponseのunit_amountは整数なので、
        // /100の結果が整数にならない場合はtoFixedなどで調整が必要か検討
        displayAmount = String(price.unit_amount / 100);
      }
    }
    
    setNewPrice({
      product: price.product,
      unit_amount: displayAmount,
      currency: price.currency,
      type: price.type,
      interval: price.recurring?.interval || 'month',
      interval_count: String(price.recurring?.interval_count || 1),
      nickname: price.nickname || ''
    });
    
    setFormErrors({});
    setIsEditModalOpen(true);
  };

  const handleDeletePrice = async (priceId: string) => {
    if (!confirm('この価格設定を非アクティブにしてもよろしいですか？\n\n注意: Stripeでは価格設定を完全に削除することはできないため、非アクティブ化されます。')) {
      return;
    }

    try {
      await adminService.archivePrice(priceId);
      // 成功したら価格リストを更新
      fetchPrices();
      alert('価格設定が非アクティブ化されました');
    } catch (err) {
      console.error('価格設定の削除中にエラーが発生しました:', err);
      alert(err instanceof Error ? err.message : '価格設定の削除中にエラーが発生しました');
    }
  };

  // 非アクティブ価格の表示/非表示を切り替える
  const toggleInactivePrices = () => {
    setShowInactivePrices(prev => !prev);
  };

  // フォームの入力値変更ハンドラ
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    if (name === 'unit_amount') { // 金額フィールドの場合のみログ出力
      console.log('handleInputChange - unit_amount value:', value); 
    }
    setNewPrice(prev => ({ ...prev, [name]: value }));
    
    // エラーをクリア
    if (formErrors[name]) {
      setFormErrors(prev => {
        const errors = { ...prev };
        delete errors[name];
        return errors;
      });
    }
  };

  // 価格を作成/更新する
  const handleSubmitPrice = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('handleSubmitPrice - newPrice.unit_amount at start:', newPrice.unit_amount); // ★ ここに追加
    setFormErrors({}); // エラーをリセット

    // バリデーション
    const errors: { [key: string]: string } = {};
    if (!newPrice.product) errors.product = '商品を選択してください。';
    
    const parsedAmount = parseFloat(newPrice.unit_amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      errors.unit_amount = '有効な価格を入力してください。';
    }

    if (newPrice.type === 'recurring') {
      if (!newPrice.interval) errors.interval = '繰り返し間隔を選択してください。';
      if (!newPrice.interval_count || parseInt(newPrice.interval_count, 10) <= 0) {
        errors.interval_count = '有効な繰り返し回数を入力してください。';
      }
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    let finalUnitAmount: number;
    if (newPrice.currency.toLowerCase() === 'jpy') {
      finalUnitAmount = Math.round(parsedAmount); // JPYの場合はそのまま（整数に丸める）
    } else {
      finalUnitAmount = Math.round(parsedAmount * 100); // JPY以外は100倍してセントに変換
    }

    const pricePayload = {
      product_id: newPrice.product,
      unit_amount: finalUnitAmount, // ★ 修正後の金額を使用
      currency: newPrice.currency,
      active: true,
      nickname: newPrice.nickname || undefined,
      recurring: newPrice.type === 'recurring' ? {
        interval: newPrice.interval as 'day' | 'week' | 'month' | 'year',
        interval_count: parseInt(newPrice.interval_count, 10),
      } : undefined,
    };

    try {
      setIsLoading(true);
      if (isEditModalOpen && currentPrice) {
        // ★ 価格編集APIの呼び出し (adminService.updatePrice を想定)
        // Stripeの価格は一度作成すると金額や通貨、課金タイプなどを変更できないものが多いため、
        // 一般的には「既存の価格をアーカイブして新しい価格を作成する」という流れになります。
        // ここでは一旦、既存の価格編集はサポート外としてアラートを出す現状のロジックを維持します。
        alert('価格の編集は現在サポートされていません。一度非アクティブ化し、新しい価格を作成してください。');
        // もし Stripe Price Update API を使ってメタデータや nickname のみを更新する場合は、
        // 適切なペイロードで adminService.updatePrice(currentPrice.id, updatePayload) のように呼び出します。
      } else {
        await adminService.createPrice(pricePayload);
        alert('新しい価格が作成されました。');
      }
      fetchPrices();
      setIsAddModalOpen(false);
      setIsEditModalOpen(false);
      setCurrentPrice(null);
      resetForm();
    } catch (err: any) {
      console.error('価格の保存中にエラーが発生しました:', err);
      const apiErrorMessage = err.response?.data?.detail || err.message || '価格の保存中にエラーが発生しました';
      alert(apiErrorMessage);
      if (err.response?.data?.errors) {
        setFormErrors(err.response.data.errors);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // 金額を表示用にフォーマット
  const formatAmount = (amount: number | null | undefined, currency: string) => {
    if (amount === null || amount === undefined) {
      return '価格未設定';
    }
    const normalizedAmount = currency.toLowerCase() === 'jpy' 
      ? amount 
      : amount / 100; 
    
    const minimumFractionDigits = currency.toLowerCase() === 'jpy' ? 0 : 2;

    const formatter = new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: currency.toUpperCase(),
      minimumFractionDigits: minimumFractionDigits
    });
    return formatter.format(normalizedAmount);
  };

  // 商品名を取得
  const getProductName = (productId: string) => {
    const product = products.find(p => p.id === productId);
    return product ? product.name : '不明な商品';
  };

  const renderPriceForm = () => {
    return (
      <form onSubmit={handleSubmitPrice}>
        <FormField label="商品" error={formErrors.product}>
          <Select
            value={newPrice.product}
            onChange={handleInputChange}
            name="product"
            required
            options={products
              .filter(p => p.active)
              .map(p => ({ value: p.id, label: p.name }))
            }
          />
        </FormField>
        
        <FormField label="金額" error={formErrors.unit_amount}>
          <div className="flex">
            <Input
              type="number"
              value={newPrice.unit_amount}
              onChange={handleInputChange}
              name="unit_amount"
              placeholder="例: 980"
              required
              min={1}
              step="1"
            />
            <select
              value={newPrice.currency}
              onChange={handleInputChange}
              name="currency"
              className="ml-2 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="jpy">円 (JPY)</option>
              <option value="usd">ドル (USD)</option>
            </select>
          </div>
        </FormField>
        
        <FormField label="課金タイプ">
          <div className="flex space-x-4">
            <label className="inline-flex items-center">
              <input
                type="radio"
                name="type"
                value="recurring"
                checked={newPrice.type === 'recurring'}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2">定期課金</span>
            </label>
            <label className="inline-flex items-center">
              <input
                type="radio"
                name="type"
                value="one_time"
                checked={newPrice.type === 'one_time'}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2">一回限り</span>
            </label>
          </div>
        </FormField>
        
        {newPrice.type === 'recurring' && (
          <>
            <FormField label="請求周期" error={formErrors.interval}>
              <Select
                value={newPrice.interval}
                onChange={handleInputChange}
                name="interval"
                required
                options={[
                  { value: 'day', label: '日ごと' },
                  { value: 'week', label: '週ごと' },
                  { value: 'month', label: '月ごと' },
                  { value: 'year', label: '年ごと' }
                ]}
              />
            </FormField>
            
            <FormField label="周期の回数" error={formErrors.interval_count}>
              <Input
                type="number"
                value={newPrice.interval_count}
                onChange={handleInputChange}
                name="interval_count"
                placeholder="例: 1"
                required
                min={1}
                step="1"
              />
              <p className="text-xs text-gray-500 mt-1">
                （例: 3ヶ月ごとの場合は3を入力）
              </p>
            </FormField>
          </>
        )}
        
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

  const renderPriceList = () => {
    if (isLoading) {
      return <div className="text-center py-8">価格情報を読み込み中...</div>;
    }

    if (error) {
      return (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 mt-0.5" />
          <span>{error}</span>
        </div>
      );
    }

    if (prices.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          価格設定が登録されていません
        </div>
      );
    }

    // アクティブな価格と非アクティブな価格を分ける
    const activePrices = prices.filter(price => price.active);
    const inactivePrices = prices.filter(price => !price.active);

    return (
      <div className="space-y-6">
        {/* アクティブな価格セクション */}
        <div>
          <h3 className="text-lg font-medium mb-3">有効な価格設定 ({activePrices.length}件)</h3>
          {activePrices.length > 0 ? (
            <div className="grid gap-4">
              {activePrices.map((price) => (
                <Card key={price.id} className="overflow-hidden border-l-4 border-l-green-500">
                  <CardContent className="p-0">
                    <div className="p-4 flex justify-between items-center">
                      <div>
                        <h3 className="font-medium text-lg">
                          {formatAmount(price.unit_amount, price.currency)}
                          {price.type === 'recurring' && price.recurring && (
                            <span className="text-sm font-normal text-gray-500 ml-1">
                              / {price.recurring.interval_count > 1 ? `${price.recurring.interval_count} ` : ''}
                              {price.recurring.interval === 'month' ? '月' : 
                               price.recurring.interval === 'year' ? '年' : 
                               price.recurring.interval === 'week' ? '週' : '日'}
                            </span>
                          )}
                        </h3>
                        <p className="text-gray-500 text-sm mt-1">
                          商品: {getProductName(price.product)}
                        </p>
                        <div className="flex items-center mt-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            有効
                          </span>
                          <span className="text-xs text-gray-500 ml-2">
                            ID: {price.id}
                          </span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditPrice(price)}
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          編集
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeletePrice(price.id)}
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          非アクティブ化
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500 bg-gray-50 rounded-md">
              有効な価格設定はありません
            </div>
          )}
        </div>

        {/* 非アクティブな価格の表示/非表示トグルボタン */}
        {inactivePrices.length > 0 && (
          <div className="mt-6 flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-600">非アクティブな価格設定 ({inactivePrices.length}件)</h3>
            <button
              onClick={toggleInactivePrices}
              className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-50 transition-colors flex items-center"
            >
              {showInactivePrices ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                  </svg>
                  非表示にする
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                  表示する
                </>
              )}
            </button>
          </div>
        )}

        {/* 非アクティブな価格セクション */}
        {inactivePrices.length > 0 && showInactivePrices && (
          <div className="mt-2">
            <div className="grid gap-4">
              {inactivePrices.map((price) => (
                <Card key={price.id} className="overflow-hidden border border-gray-200 bg-gray-50 opacity-75">
                  <CardContent className="p-0">
                    <div className="p-4 flex justify-between items-center">
                      <div>
                        <h3 className="font-medium text-lg text-gray-500">
                          {formatAmount(price.unit_amount, price.currency)}
                          {price.type === 'recurring' && price.recurring && (
                            <span className="text-sm font-normal text-gray-400 ml-1">
                              / {price.recurring.interval_count > 1 ? `${price.recurring.interval_count} ` : ''}
                              {price.recurring.interval === 'month' ? '月' : 
                               price.recurring.interval === 'year' ? '年' : 
                               price.recurring.interval === 'week' ? '週' : '日'}
                            </span>
                          )}
                        </h3>
                        <p className="text-gray-400 text-sm mt-1">
                          商品: {getProductName(price.product)}
                        </p>
                        <div className="flex items-center mt-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-700">
                            非アクティブ
                          </span>
                          <span className="text-xs text-gray-400 ml-2">
                            ID: {price.id}
                          </span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditPrice(price)}
                          className="opacity-75"
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          詳細
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      {/* Stripe API設定エラーの通知 */}
      {error && error.includes('Stripe') && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded-lg mb-6">
          <h3 className="text-lg font-medium flex items-center">
            <AlertCircle className="h-5 w-5 mr-2" />
            Stripe API設定に問題があります
          </h3>
          <p className="mt-2 text-sm">
            Stripe APIとの連携に問題が発生しています。この機能を使用するには、バックエンドでStripe APIキーの設定が必要です。
            <br />
            詳細なエラー: {error}
          </p>
          <p className="mt-3 text-sm font-medium">
            管理者向けの他の機能（キャンペーンコード管理など）は引き続き利用可能です。
          </p>
        </div>
      )}

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">価格設定</h2>
        <Button variant="primary" onClick={handleAddPrice} disabled={!!error}>
          <PlusCircle className="h-4 w-4 mr-2" />
          価格を追加
        </Button>
      </div>

      {renderPriceList()}

      {/* 価格追加モーダル */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="新しい価格設定を追加"
      >
        {renderPriceForm()}
      </Modal>

      {/* 価格編集モーダル */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="価格設定を編集"
      >
        {renderPriceForm()}
      </Modal>
    </div>
  );
}; 
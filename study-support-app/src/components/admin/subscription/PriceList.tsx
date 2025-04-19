"use client";

import React, { useState, useEffect } from 'react';
import { PlusCircle, Edit, Trash2, AlertCircle, X } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card, CardContent } from '@/components/common/Card';
import { adminService, StripeProduct, StripePrice } from '@/services/adminService';

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
  const [prices, setPrices] = useState<StripePrice[]>([]);
  const [products, setProducts] = useState<StripeProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [currentPrice, setCurrentPrice] = useState<StripePrice | null>(null);
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  
  // 新規価格設定のフォーム状態
  const [newPrice, setNewPrice] = useState({
    product: '',
    unit_amount: '',
    currency: 'jpy',
    type: 'recurring',
    interval: 'month',
    interval_count: '1'
  });

  useEffect(() => {
    Promise.all([fetchPrices(), fetchProducts()]);
  }, []);

  const fetchPrices = async () => {
    try {
      setIsLoading(true);
      const data = await adminService.getPrices();
      setPrices(data || []);
    } catch (err) {
      console.error('価格の取得中にエラーが発生しました:', err);
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
      interval_count: '1'
    });
    setFormErrors({});
  };

  const handleAddPrice = () => {
    resetForm();
    setIsAddModalOpen(true);
  };

  const handleEditPrice = (price: StripePrice) => {
    setCurrentPrice(price);
    
    // 編集フォームの初期値を設定
    setNewPrice({
      product: price.product,
      unit_amount: String(price.unit_amount / 100), // Stripeは最小単位（円/セント）で保存されているため100で割る
      currency: price.currency,
      type: price.type,
      interval: price.recurring?.interval || 'month',
      interval_count: String(price.recurring?.interval_count || 1)
    });
    
    setFormErrors({});
    setIsEditModalOpen(true);
  };

  const handleDeletePrice = async (priceId: string) => {
    if (!confirm('この価格設定を削除してもよろしいですか？')) {
      return;
    }

    try {
      await adminService.deletePrice(priceId);
      // 成功したら価格リストを更新
      fetchPrices();
    } catch (err) {
      console.error('価格設定の削除中にエラーが発生しました:', err);
      alert(err instanceof Error ? err.message : '価格設定の削除中にエラーが発生しました');
    }
  };

  // フォームの入力値変更ハンドラ
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
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
    
    // フォームのバリデーション
    const errors: { [key: string]: string } = {};
    
    if (!newPrice.product) {
      errors.product = '商品を選択してください';
    }
    
    if (!newPrice.unit_amount) {
      errors.unit_amount = '金額を入力してください';
    } else if (Number(newPrice.unit_amount) <= 0) {
      errors.unit_amount = '金額は0より大きい値を入力してください';
    }
    
    if (newPrice.type === 'recurring') {
      if (!newPrice.interval) {
        errors.interval = '請求周期を選択してください';
      }
      
      if (!newPrice.interval_count || Number(newPrice.interval_count) <= 0) {
        errors.interval_count = '請求周期の回数は0より大きい値を入力してください';
      }
    }
    
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    
    try {
      const priceData = {
        product: newPrice.product,
        unit_amount: Math.round(Number(newPrice.unit_amount) * 100), // 円/セント単位に変換
        currency: newPrice.currency,
        ...(newPrice.type === 'recurring' ? {
          recurring: {
            interval: newPrice.interval as 'day' | 'week' | 'month' | 'year',
            interval_count: Number(newPrice.interval_count)
          }
        } : {})
      };
      
      if (isEditModalOpen && currentPrice) {
        // 価格の更新はStripeでは直接サポートされていないため、
        // 通常は古い価格を非アクティブにして新しい価格を作成する
        await adminService.createPrice(priceData);
        // 古い価格を削除または非アクティブにするロジックが必要な場合はここに追加
      } else {
        await adminService.createPrice(priceData);
      }
      
      // モーダルを閉じて価格リストを更新
      setIsAddModalOpen(false);
      setIsEditModalOpen(false);
      fetchPrices();
      resetForm();
    } catch (err) {
      console.error('価格の保存中にエラーが発生しました:', err);
      alert(err instanceof Error ? err.message : '価格の保存中にエラーが発生しました');
    }
  };

  // 金額を表示用にフォーマット
  const formatAmount = (amount: number, currency: string) => {
    const formatter = new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: currency.toUpperCase(),
      minimumFractionDigits: 0
    });
    return formatter.format(amount / 100); // Stripeは金額を最小単位（円/セント）で保存
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

    return (
      <div className="grid gap-4">
        {prices.map((price) => (
          <Card key={price.id} className="overflow-hidden">
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
                    商品: {price.product_name || getProductName(price.product)}
                  </p>
                  <div className="flex items-center mt-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      price.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {price.active ? '有効' : '無効'}
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
        <h2 className="text-xl font-semibold">価格設定</h2>
        <Button variant="primary" onClick={handleAddPrice}>
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
"use client";

import React, { useState, useEffect } from 'react';
import { PlusCircle, Edit, Trash2, AlertCircle, X } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card, CardContent } from '@/components/common/Card';
import { adminService, StripeProduct } from '@/services/adminService';

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
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  required?: boolean;
  name?: string;
}> = ({ type = "text", value, onChange, placeholder, required, name }) => {
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      required={required}
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

export const ProductList: React.FC = () => {
  const [products, setProducts] = useState<StripeProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [currentProduct, setCurrentProduct] = useState<StripeProduct | null>(null);
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  
  // 新規商品のフォーム状態
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    active: true
  });

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setIsLoading(true);
      const data = await adminService.getProducts();
      setProducts(data || []);
    } catch (err) {
      console.error('商品の取得中にエラーが発生しました:', err);
      setError(err instanceof Error ? err.message : '商品の取得中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setNewProduct({
      name: '',
      description: '',
      active: true
    });
    setFormErrors({});
  };

  const handleAddProduct = () => {
    resetForm();
    setIsAddModalOpen(true);
  };

  const handleEditProduct = (product: StripeProduct) => {
    setCurrentProduct(product);
    
    // 編集フォームの初期値を設定
    setNewProduct({
      name: product.name,
      description: product.description || '',
      active: product.active
    });
    
    setFormErrors({});
    setIsEditModalOpen(true);
  };

  const handleDeleteProduct = async (productId: string) => {
    if (!confirm('この商品を削除してもよろしいですか？関連する価格設定も削除されます。')) {
      return;
    }

    try {
      await adminService.deleteProduct(productId);
      // 成功したら商品リストを更新
      fetchProducts();
    } catch (err) {
      console.error('商品の削除中にエラーが発生しました:', err);
      alert(err instanceof Error ? err.message : '商品の削除中にエラーが発生しました');
    }
  };

  // フォームの入力値変更ハンドラ
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setNewProduct(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
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

  // 商品を作成/更新する
  const handleSubmitProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // フォームのバリデーション
    const errors: { [key: string]: string } = {};
    
    if (!newProduct.name.trim()) {
      errors.name = '商品名を入力してください';
    }
    
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    
    try {
      const productData = {
        name: newProduct.name.trim(),
        description: newProduct.description.trim() || undefined,
        active: newProduct.active
      };
      
      if (isEditModalOpen && currentProduct) {
        // 商品の更新は現在のAPIでは直接サポートしていない
        // 通常は商品を非アクティブにして新しい商品を作成するか、
        // バックエンドでPUTエンドポイントを実装する必要がある
        await adminService.createProduct(productData);
      } else {
        await adminService.createProduct(productData);
      }
      
      // モーダルを閉じて商品リストを更新
      setIsAddModalOpen(false);
      setIsEditModalOpen(false);
      fetchProducts();
      resetForm();
    } catch (err) {
      console.error('商品の保存中にエラーが発生しました:', err);
      alert(err instanceof Error ? err.message : '商品の保存中にエラーが発生しました');
    }
  };

  const renderProductForm = () => {
    return (
      <form onSubmit={handleSubmitProduct}>
        <FormField label="商品名" error={formErrors.name}>
          <Input
            value={newProduct.name}
            onChange={handleInputChange}
            name="name"
            placeholder="例: プレミアムプラン"
            required
          />
        </FormField>
        
        <FormField label="説明">
          <textarea
            value={newProduct.description}
            onChange={(e) => setNewProduct(prev => ({ ...prev, description: e.target.value }))}
            name="description"
            placeholder="例: 全機能が利用できるプレミアムなプラン"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            rows={3}
          />
        </FormField>
        
        <FormField label="ステータス">
          <Checkbox
            checked={newProduct.active}
            onChange={handleInputChange}
            name="active"
            label="この商品を有効にする"
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

  const renderProductList = () => {
    if (isLoading) {
      return <div className="text-center py-8">商品情報を読み込み中...</div>;
    }

    if (error) {
      return (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 mt-0.5" />
          <span>{error}</span>
        </div>
      );
    }

    if (products.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          商品が登録されていません
        </div>
      );
    }

    return (
      <div className="grid gap-4">
        {products.map((product) => (
          <Card key={product.id} className="overflow-hidden">
            <CardContent className="p-0">
              <div className="p-4 flex justify-between items-center">
                <div>
                  <h3 className="font-medium text-lg">{product.name}</h3>
                  {product.description && (
                    <p className="text-gray-500 text-sm mt-1">{product.description}</p>
                  )}
                  <div className="flex items-center mt-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      product.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {product.active ? '有効' : '無効'}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      ID: {product.id}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditProduct(product)}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    編集
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteProduct(product.id)}
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
        <h2 className="text-xl font-semibold">商品一覧</h2>
        <Button variant="primary" onClick={handleAddProduct}>
          <PlusCircle className="h-4 w-4 mr-2" />
          商品を追加
        </Button>
      </div>

      {renderProductList()}

      {/* 商品追加モーダル */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="新しい商品を追加"
      >
        {renderProductForm()}
      </Modal>

      {/* 商品編集モーダル */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="商品を編集"
      >
        {renderProductForm()}
      </Modal>
    </div>
  );
}; 
"use client";

import React from 'react';
import { useQuery } from '@tanstack/react-query';

// API 関数
import { fetchDiscountTypes } from '@/lib/api/admin'; 

// 型定義
import { DiscountTypeResponse } from '@/types/subscription'; 

// 依存コンポーネント
import { DiscountTypeTable } from './DiscountTypeTable';
import { columns } from './discount-type-columns'; 

export function DiscountTypeList() {
  // --- React Query Hooks --- 
  const { data: discountTypes = [], isLoading, error } = useQuery<DiscountTypeResponse[]>(
    { 
      queryKey: ['adminDiscountTypes'], 
      queryFn: fetchDiscountTypes 
    }
  );

  // --- Render Logic --- 
  if (isLoading) return <div>割引タイプを読み込み中...</div>;
  if (error) return <div className="text-red-500">エラーが発生しました: {error.message}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">割引タイプ管理</h2>
      </div>

      <DiscountTypeTable 
        columns={columns()}
        data={discountTypes}
      />
    </div>
  );
} 
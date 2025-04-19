"use client";

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/common/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/common/Card';
import { ProductList } from '@/components/admin/subscription/ProductList';
import { PriceList } from '@/components/admin/subscription/PriceList';
import { CampaignCodeManagement } from '@/components/admin/subscription/CampaignCodeManagement';

export const SubscriptionManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState('products');

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>サブスクリプション管理</CardTitle>
        <CardDescription>
          Stripe商品・価格設定、キャンペーンコード管理
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="products" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="products">商品設定</TabsTrigger>
            <TabsTrigger value="prices">価格設定</TabsTrigger>
            <TabsTrigger value="campaigns">キャンペーンコード</TabsTrigger>
          </TabsList>
          <TabsContent value="products">
            <ProductList />
          </TabsContent>
          <TabsContent value="prices">
            <PriceList />
          </TabsContent>
          <TabsContent value="campaigns">
            <CampaignCodeManagement />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}; 
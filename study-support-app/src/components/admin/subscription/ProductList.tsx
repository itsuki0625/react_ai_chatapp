"use client";

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { PlusCircle } from 'lucide-react';
import { 
  AlertDialog, 
  AlertDialogAction, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle 
} from '@/components/ui/alert-dialog';
import { useToast } from "@/hooks/use-toast";

// API 関数 (./../../lib/api/admin から)
import { fetchProducts, archiveProduct } from '@/lib/api/admin'; 

// 型定義
import { 
  StripeProductWithPricesResponse, 
  StripeProductResponse, 
  StripePriceResponse,
} from '@/types/stripe';

// 依存コンポーネント (後で移動/作成するファイル)
import { ProductTable } from './product-table'; 
import { columns } from './columns';
import { CreateProductDialog } from './create-product-dialog';
import { EditProductDialog } from './edit-product-dialog';
import { EditPriceDialog } from './edit-price-dialog';

// ProductList コンポーネント定義
export function ProductList() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // --- State Management --- 
  // 商品関連
  const [isCreateDialogOpen, setIsCreateDialogOpen] = React.useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = React.useState(false);
  const [editingProduct, setEditingProduct] = React.useState<StripeProductWithPricesResponse | null>(null);
  const [isArchiveDialogOpen, setIsArchiveDialogOpen] = React.useState(false);
  const [archivingProductId, setArchivingProductId] = React.useState<string | null>(null);
  // 価格関連
  const [isEditPriceDialogOpen, setIsEditPriceDialogOpen] = React.useState(false);
  const [editingPrice, setEditingPrice] = React.useState<StripePriceResponse | null>(null);

  // --- React Query Hooks --- 
  // 商品リスト取得
  const { data: products = [], isLoading, error } = useQuery<StripeProductWithPricesResponse[]>(
    { 
      queryKey: ['adminProducts'], 
      queryFn: fetchProducts 
    }
  );

  // 商品アーカイブ
  const archiveProductMutation = useMutation<
    StripeProductResponse,
    Error,
    string
  >({
    mutationFn: archiveProduct,
    onSuccess: (data) => {
      toast({ title: "成功", description: `商品「${data.name}」をアーカイブしました。` });
      queryClient.invalidateQueries({ queryKey: ['adminProducts'] });
      setIsArchiveDialogOpen(false);
      setArchivingProductId(null);
    },
    onError: (error) => {
      toast({ title: "エラー", description: `商品のアーカイブに失敗: ${error.message}`, variant: "destructive" });
      setIsArchiveDialogOpen(false);
      setArchivingProductId(null);
    },
  });

  // --- Handlers --- 
  const handleCreateSuccess = () => {
    setIsCreateDialogOpen(false);
    queryClient.invalidateQueries({ queryKey: ['adminProducts'] });
  };

  const handleEditSuccess = () => {
    setIsEditDialogOpen(false);
    setEditingProduct(null);
    queryClient.invalidateQueries({ queryKey: ['adminProducts'] });
  };

  const handleOpenCreateDialog = () => {
    setIsCreateDialogOpen(true);
  };

  const handleOpenEditDialog = (product: StripeProductWithPricesResponse) => {
    setEditingProduct(product);
    setIsEditDialogOpen(true);
  };

  const handleOpenArchiveDialog = (productId: string) => {
    setArchivingProductId(productId);
    setIsArchiveDialogOpen(true);
  };

  const handleConfirmArchive = () => {
    if (archivingProductId) {
      archiveProductMutation.mutate(archivingProductId);
    }
  };

  const handleOpenEditPriceDialog = (price: StripePriceResponse) => {
    setEditingPrice(price);
    setIsEditPriceDialogOpen(true);
  };

  const handleEditPriceSuccess = () => {
    setIsEditPriceDialogOpen(false);
    setEditingPrice(null);
    queryClient.invalidateQueries({ queryKey: ['adminProducts'] });
  };


  // --- Render Logic --- 
  if (isLoading) return <div>商品を読み込み中...</div>;
  // TODO: エラー表示を改善 (例: Alert コンポーネントを使用)
  if (error) return <div className="text-red-500">エラーが発生しました: {error.message}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <Button onClick={handleOpenCreateDialog}>
          <PlusCircle className="mr-2 h-4 w-4" /> 商品を追加
        </Button>
      </div>

      <ProductTable 
        columns={columns({ 
          onEdit: handleOpenEditDialog, 
          onArchive: handleOpenArchiveDialog, 
        })} 
        data={products} 
        onEditPrice={handleOpenEditPriceDialog}
      />

      <CreateProductDialog 
        isOpen={isCreateDialogOpen} 
        onClose={() => setIsCreateDialogOpen(false)}
        onSuccess={handleCreateSuccess} 
      />
      
      {editingProduct && (
        <EditProductDialog
          isOpen={isEditDialogOpen}
          onClose={() => setIsEditDialogOpen(false)}
          onSuccess={handleEditSuccess}
          product={editingProduct}
        />
      )}

      <AlertDialog open={isArchiveDialogOpen} onOpenChange={setIsArchiveDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>商品のアーカイブ確認</AlertDialogTitle>
            <AlertDialogDescription>
              商品ID: {archivingProductId} をアーカイブ（非アクティブ化）してもよろしいですか？<br />
              関連する価格も利用できなくなります。この操作は元に戻せません（再度有効化は可能です）。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setArchivingProductId(null)}>キャンセル</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmArchive} 
              disabled={archiveProductMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {archiveProductMutation.isPending ? "アーカイブ中..." : "アーカイブ実行"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {editingPrice && (
        <EditPriceDialog
          isOpen={isEditPriceDialogOpen}
          onClose={() => setIsEditPriceDialogOpen(false)}
          onSuccess={handleEditPriceSuccess}
          price={editingPrice}
        />
      )}
    </div>
  );
} 
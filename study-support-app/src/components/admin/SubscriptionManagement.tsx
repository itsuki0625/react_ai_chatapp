"use client";

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/common/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/common/Card';
import { ProductList } from '@/components/admin/subscription/ProductList';
import { PriceList } from '@/components/admin/subscription/PriceList';
import { CampaignCodeManagement } from '@/components/admin/subscription/CampaignCodeManagement';
// import { DiscountTypeList } from '@/components/admin/subscription/DiscountTypeList';
// --- Coupon Imports Start ---
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { couponAdminService } from '@/services/couponService';
import { StripeCouponResponse, StripeCouponCreate, StripeCouponUpdate } from '@/types/coupon';
import { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/data-table";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, PlusCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { format } from 'date-fns';
import { CouponFormModal } from "@/components/admin/CouponFormModal";
// --- Coupon Imports End ---

// --- Coupon Helper Functions Start ---
const formatDiscount = (coupon: StripeCouponResponse): string => {
    if (coupon.percent_off) {
        return `${coupon.percent_off}%`;
    }
    if (coupon.amount_off) {
        // DB側に通貨情報がないため、固定で JPY を使用
        const formatter = new Intl.NumberFormat('ja-JP', {
            style: 'currency',
            currency: 'JPY',
            minimumFractionDigits: 0
        });
        return formatter.format(coupon.amount_off);
    }
    return '0';
};

const formatDuration = (coupon: StripeCouponResponse): string => {
    switch (coupon.duration) {
        case 'forever': return '永続';
        case 'once': return '1回のみ';
        case 'repeating': return `${coupon.duration_in_months}ヶ月間`;
        default: return coupon.duration;
    }
};

const formatTimestamp = (timestamp: number | null | undefined): string => {
    if (!timestamp) return '-';
    return format(new Date(timestamp * 1000), 'yyyy/MM/dd HH:mm');
};

// Helper function to format coupon value display
const formatCouponValue = (coupon: StripeCouponResponse): string => {
    if (coupon.percent_off) {
        return `${coupon.percent_off}% OFF`;
    }
    if (coupon.amount_off) {
        // DB側に通貨情報がないため、固定で JPY を使用
        const formatter = new Intl.NumberFormat('ja-JP', { style: 'currency', currency: 'JPY', minimumFractionDigits: 0 });
        return formatter.format(coupon.amount_off);
    }
    return 'N/A'; // Should not happen if data is valid
};
// --- Coupon Helper Functions End ---

// --- Coupon Table Columns Definition Start ---
const getColumns = (onEdit: (coupon: StripeCouponResponse) => void, onDelete: (coupon: StripeCouponResponse) => void): ColumnDef<StripeCouponResponse>[] => [
    { accessorKey: "id", header: "Coupon ID", cell: ({ row }) => <div className="font-mono text-xs">{row.getValue("id")}</div> },
    { accessorKey: "name", header: "名前", cell: ({ row }) => row.getValue("name") || <span className="text-muted-foreground">N/A</span> },
    { id: "discount", header: "割引", cell: ({ row }) => formatDiscount(row.original) },
    { id: "duration", header: "期間", cell: ({ row }) => formatDuration(row.original) },
    { accessorKey: "valid", header: "有効", cell: ({ row }) => row.getValue("valid") ? <span className="text-green-600">有効</span> : <span className="text-red-600">無効</span> },
    { accessorKey: "created", header: "作成日時", cell: ({ row }) => formatTimestamp(row.getValue("created")) },
    { accessorKey: "times_redeemed", header: "利用回数", cell: ({ row }) => { const max = row.original.max_redemptions; const redeemed = row.getValue("times_redeemed") as number; return max ? `${redeemed} / ${max}` : `${redeemed}`; } },
    { 
        id: "actions", 
        cell: ({ row }) => { 
            const coupon = row.original; 
            return ( 
                <DropdownMenu> 
                    <DropdownMenuTrigger asChild> 
                        <Button variant="ghost" className="h-8 w-8 p-0"> 
                            <span className="sr-only">Open menu</span> 
                            <MoreHorizontal className="h-4 w-4" /> 
                        </Button> 
                    </DropdownMenuTrigger> 
                    <DropdownMenuContent align="end"> 
                        <DropdownMenuLabel>アクション</DropdownMenuLabel> 
                        <DropdownMenuItem onClick={() => onEdit(coupon)}> 
                            編集 
                        </DropdownMenuItem> 
                        <DropdownMenuSeparator /> 
                        <DropdownMenuItem 
                            className="text-red-600 focus:text-red-700 focus:bg-red-50 cursor-pointer" 
                            onSelect={(event) => {
                                event.preventDefault();
                                onDelete(coupon);
                            }}
                        >
                            削除
                        </DropdownMenuItem>
                    </DropdownMenuContent> 
                </DropdownMenu> 
            ); 
        } 
    },
];
// --- Coupon Table Columns Definition End ---

// --- Coupon Management Component Start ---
const CouponManagement = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [showFormModal, setShowFormModal] = useState(false);
  const [editingCoupon, setEditingCoupon] = useState<StripeCouponResponse | null>(null);
  // --- State for Delete Confirmation Dialog ---
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [couponToDelete, setCouponToDelete] = useState<StripeCouponResponse | null>(null);

  const {
    data: couponsResponse,
    isLoading: isLoadingCoupons,
    error: couponsError,
    refetch: refetchCoupons,
  } = useQuery<StripeCouponResponse[], Error>({
    queryKey: ['adminDbCoupons'],
    queryFn: () => couponAdminService.listAdminDbCoupons(100),
  });

  const createCouponMutation = useMutation({
    mutationFn: couponAdminService.createAndImportCoupon,
    onSuccess: () => {
      toast({ title: "クーポン作成成功", description: "StripeとDBにクーポンが作成されました。" });
      queryClient.invalidateQueries({ queryKey: ['adminDbCoupons'] });
      handleCloseModal();
    },
    onError: (error: any) => {
      toast({ title: "クーポン作成失敗", description: error.response?.data?.detail || error.message, variant: "destructive" });
    },
  });

  const updateCouponMutation = useMutation({
    mutationFn: ({ couponDbId, data }: { couponDbId: string, data: StripeCouponUpdate }) =>
      couponAdminService.updateDbCoupon(couponDbId, data),
    onSuccess: () => {
      toast({ title: "クーポン更新成功", description: "StripeとDBのクーポン情報が更新されました。" });
      queryClient.invalidateQueries({ queryKey: ['adminDbCoupons'] });
      handleCloseModal();
    },
    onError: (error: any) => {
      toast({ title: "クーポン更新失敗", description: error.response?.data?.detail || error.message, variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (couponDbId: string) => couponAdminService.deleteDbCoupon(couponDbId),
    onSuccess: () => {
      toast({ title: "クーポン削除成功", description: "StripeとDBからクーポンが削除されました。" });
      queryClient.invalidateQueries({ queryKey: ['adminDbCoupons'] });
      setCouponToDelete(null);
      setIsAlertOpen(false);
    },
    onError: (error: any) => {
      toast({ title: "クーポン削除失敗", description: error.response?.data?.detail || error.message, variant: "destructive" });
      setCouponToDelete(null);
      setIsAlertOpen(false);
    },
  });

  const handleEditCoupon = (coupon: StripeCouponResponse) => {
      setEditingCoupon(coupon);
      setShowFormModal(true);
  };

  // --- Modified: Opens the delete confirmation dialog ---
  const handleDeleteCoupon = (coupon: StripeCouponResponse) => {
      // deleteMutation.mutate(couponId); // Don't delete directly
      setCouponToDelete(coupon); // Store coupon info
      setIsAlertOpen(true);       // Open the alert dialog
  };

  // --- New: Confirms and executes the deletion ---
  const confirmDelete = () => {
      if (couponToDelete) {
          deleteMutation.mutate(couponToDelete.id);
      }
  };

  const handleOpenCreateModal = () => {
      setEditingCoupon(null);
      setShowFormModal(true);
  };

  const handleCloseModal = () => {
      setShowFormModal(false);
      setEditingCoupon(null);
  };

  // Pass the modified handleDeleteCoupon to getColumns
  const couponColumns = getColumns(handleEditCoupon, handleDeleteCoupon);

  const columns: ColumnDef<StripeCouponResponse>[] = [
    ...couponColumns,
    {
      accessorKey: "value", // Custom key for display value
      header: "割引内容",
      cell: ({ row }) => formatCouponValue(row.original), // ★ ここで formatCouponValue が使われる
    },
  ];

  return (
      <div>
          <div className="flex justify-end mb-4">
              <Button onClick={handleOpenCreateModal}>
                  <PlusCircle className="mr-2 h-4 w-4" /> 新規 Coupon 作成
              </Button>
          </div>

          <CouponFormModal
              isOpen={showFormModal}
              onClose={handleCloseModal}
              initialData={editingCoupon}
          />

          {couponsError ? (
              <div className="text-red-500">クーポンデータの読み込みエラー: {couponsError.message}</div>
          ) : (
              <DataTable columns={columns} data={couponsResponse ?? []} isLoading={isLoadingCoupons} />
          )}

          {/* --- Delete Confirmation Dialog --- */}
          <AlertDialog open={isAlertOpen} onOpenChange={setIsAlertOpen}>
              <AlertDialogContent>
                  <AlertDialogHeader>
                      <AlertDialogTitle>DB Coupon「{couponToDelete?.name || couponToDelete?.stripe_coupon_id}」を削除しますか？</AlertDialogTitle>
                      <AlertDialogDescription>
                          この操作は元に戻せません。アプリのデータベースと Stripe から Coupon が削除されます。
                          (プロモーションコードに紐付いている場合は削除できません)
                      </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                      <AlertDialogCancel onClick={() => setCouponToDelete(null)}>キャンセル</AlertDialogCancel>
                      <AlertDialogAction
                          onClick={confirmDelete}
                          disabled={deleteMutation.isPending}
                          className="bg-red-600 hover:bg-red-700"
                      >
                          {deleteMutation.isPending ? "削除中..." : "削除実行 (Stripe+DB)"}
                      </AlertDialogAction>
                  </AlertDialogFooter>
              </AlertDialogContent>
          </AlertDialog>
      </div>
  );
};
// --- Coupon Management Component End ---

export const SubscriptionManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState('products');

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>サブスクリプション・クーポン管理</CardTitle>
        <CardDescription>
          Stripe商品・価格設定、キャンペーンコード、クーポン管理
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="products" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="products">商品設定</TabsTrigger>
            <TabsTrigger value="prices">価格設定</TabsTrigger>
            <TabsTrigger value="campaigns">キャンペーンコード</TabsTrigger>
            <TabsTrigger value="coupons">クーポン</TabsTrigger>
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
          <TabsContent value="coupons">
            <CouponManagement />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}; 
"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { couponAdminService } from '@/services/couponService'; // Adjust path if necessary
import { StripeCouponResponse, StripeCouponCreate, StripeCouponUpdate } from '@/types/coupon';
import { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/data-table"; // Assuming you have a DataTable component
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
import { useToast } from "@/hooks/use-toast"; // Updated import path
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { AdminLayout } from '@/components/layout/AdminLayout'; // Assuming an AdminLayout exists
import { format } from 'date-fns'; // For date formatting
import { CouponFormModal } from "@/components/admin/CouponFormModal"; // Import the modal

// --- Helper Functions ---
const formatDiscount = (coupon: StripeCouponResponse): string => {
    if (coupon.percent_off) {
        return `${coupon.percent_off}%`;
    }
    if (coupon.amount_off) {
        // Basic currency formatting (improve as needed)
        const formatter = new Intl.NumberFormat('ja-JP', { style: 'currency', currency: coupon.currency || 'JPY', minimumFractionDigits: 0 });
        return formatter.format(coupon.amount_off / 100); // Assuming amount_off is in cents
    }
    return 'N/A';
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

// --- Coupon Table Columns Definition ---
const getColumns = (onEdit: (coupon: StripeCouponResponse) => void, onDelete: (couponId: string) => void): ColumnDef<StripeCouponResponse>[] => [
    {
        accessorKey: "id",
        header: "Coupon ID",
        cell: ({ row }) => <div className="font-mono text-xs">{row.getValue("id")}</div>,
    },
    {
        accessorKey: "name",
        header: "名前",
        cell: ({ row }) => row.getValue("name") || <span className="text-muted-foreground">N/A</span>,
    },
    {
        id: "discount",
        header: "割引",
        cell: ({ row }) => formatDiscount(row.original),
    },
    {
        id: "duration",
        header: "期間",
        cell: ({ row }) => formatDuration(row.original),
    },
    {
        accessorKey: "valid",
        header: "有効",
        cell: ({ row }) => row.getValue("valid") ? <span className="text-green-600">有効</span> : <span className="text-red-600">無効</span>,
    },
    {
        accessorKey: "stripe_created_timestamp",
        header: "作成日時 (Stripe)",
        cell: ({ row }) => formatTimestamp(row.getValue("stripe_created_timestamp")),
    },
    {
        accessorKey: "times_redeemed",
        header: "利用回数",
        cell: ({ row }) => {
            const max = row.original.max_redemptions;
            const redeemed = row.getValue("times_redeemed") as number;
            return max ? `${redeemed} / ${max}` : `${redeemed}`;
        },
    },
    {
        id: "actions",
        cell: ({ row }) => {
            const coupon = row.original;
            return (
                <AlertDialog>
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
                            <AlertDialogTrigger asChild>
                                <DropdownMenuItem className="text-red-600 focus:text-red-700 focus:bg-red-50">
                                    削除
                                </DropdownMenuItem>
                            </AlertDialogTrigger>
                        </DropdownMenuContent>
                    </DropdownMenu>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Coupon「{coupon.name || coupon.id}」を削除しますか？</AlertDialogTitle>
                            <AlertDialogDescription>
                                この操作は元に戻せません。Stripe上のCouponが削除されます。
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>キャンセル</AlertDialogCancel>
                            <AlertDialogAction 
                                onClick={() => onDelete(coupon.id)}
                                className="bg-red-600 hover:bg-red-700"
                            >
                                削除実行
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            );
        },
    },
];

// --- Main Page Component ---
const AdminCouponsPage = () => {
    const queryClient = useQueryClient();
    const { toast } = useToast();
    const [showFormModal, setShowFormModal] = useState(false); // Renamed state variable
    const [editingCoupon, setEditingCoupon] = useState<StripeCouponResponse | null>(null);

    // Fetch coupons query
    const { data: couponsResponse, isLoading, error } = useQuery({
        queryKey: ['adminStripeCoupons'],
        queryFn: () => couponAdminService.listAdminDbCoupons(100),
    });

    // ★ ここにログを追加
    console.log("AdminCouponsPage - isLoading:", isLoading);
    console.log("AdminCouponsPage - error:", error);
    console.log("AdminCouponsPage - couponsResponse:", couponsResponse);

    // Delete coupon mutation
    const deleteMutation = useMutation({
        mutationFn: couponAdminService.deleteDbCoupon,
        onSuccess: () => {
            toast({ title: "成功", description: "Couponが削除されました。" });
            queryClient.invalidateQueries({ queryKey: ['adminStripeCoupons'] });
        },
        onError: (err: Error) => {
            toast({ variant: "destructive", title: "エラー", description: `Couponの削除に失敗しました: ${err.message}` });
        },
    });

    const handleEdit = (coupon: StripeCouponResponse) => {
        setEditingCoupon(coupon);
        setShowFormModal(true); // Open the modal for editing
        // toast({ title: "未実装", description: "編集機能は現在実装中です。" }); // Remove placeholder toast
    };

    const handleDelete = (couponId: string) => {
        deleteMutation.mutate(couponId);
    };

    const handleOpenCreateModal = () => {
        setEditingCoupon(null); // Ensure not in edit mode
        setShowFormModal(true); // Open the modal for creating
        // toast({ title: "未実装", description: "新規作成機能は現在実装中です。" }); // Remove placeholder toast
    };

    const handleCloseModal = () => {
        setShowFormModal(false);
        setEditingCoupon(null); // Clear editing state when closing
    };

    const columns = getColumns(handleEdit, handleDelete);

    if (error) {
        return (
            <AdminLayout>
                <div className="text-red-500">エラー: {error.message}</div>
                 {/* ★ エラー時にもレスポンス内容をログに出力してみる */}
                <p>Error details:</p>
                <pre>{JSON.stringify(error, null, 2)}</pre>
            </AdminLayout>
        );
    }

    // ★ DataTableに渡す直前のデータもログに出力
    const tableData = couponsResponse ?? [];
    console.log("AdminCouponsPage - tableData for DataTable:", tableData);

    return (
        <AdminLayout>
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-bold">Stripe Coupon 管理</h1>
                <Button onClick={handleOpenCreateModal}> {/* Call handler to open create modal */} 
                    <PlusCircle className="mr-2 h-4 w-4" /> 新規 Coupon 作成
                </Button>
            </div>

            {/* Render the Modal */} 
             <CouponFormModal 
                isOpen={showFormModal}
                onClose={handleCloseModal}
                initialData={editingCoupon}
             />

            <DataTable columns={columns} data={tableData} isLoading={isLoading} /> 

        </AdminLayout>
    );
};

export default AdminCouponsPage; 
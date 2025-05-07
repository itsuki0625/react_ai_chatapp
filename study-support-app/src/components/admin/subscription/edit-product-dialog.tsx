'use client';

import React from 'react';
import { ControllerRenderProps, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import {
  Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { updateProduct } from '@/lib/api/admin'; // API関数
import { StripeProductUpdate, StripeProductResponse, StripeProductWithPricesResponse } from '@/types/stripe';
import { getRoles } from '@/services/adminService'; // ★ getRoles をインポート
import { Role } from '@/types/user'; // ★ Role型をインポート

// フォームのバリデーションスキーマ (Update用)
const formSchema = z.object({
  name: z.string().min(1, { message: "商品名は必須です。" }),
  description: z.string().optional().nullable(),
  active: z.boolean(),
  role: z.string().optional(), // ★ Role ID を文字列として保持
});

type ProductFormValues = z.infer<typeof formSchema>;

interface EditProductDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void; 
  product: StripeProductWithPricesResponse; // 編集対象の商品データ
}

export function EditProductDialog({ isOpen, onClose, onSuccess, product }: EditProductDialogProps) {
  const { toast } = useToast();

  const form = useForm<ProductFormValues>({
    resolver: zodResolver(formSchema),
  });

  // ロール一覧を取得
  const { data: roles, isLoading: isLoadingRoles, error: rolesError } = useQuery<Role[], Error>({
    queryKey: ['roles'],
    queryFn: async () => {
      const fetchedRoles = await getRoles();
      console.log('Fetched roles in EditProductDialog:', JSON.stringify(fetchedRoles, null, 2));
      return fetchedRoles;
    },
    enabled: isOpen, 
  });

  const updateProductMutation = useMutation<
    StripeProductResponse,
    Error,
    { productId: string; data: StripeProductUpdate }
  >({
    mutationFn: (variables) => updateProduct(variables.productId, variables.data),
    onSuccess: (data) => {
      toast({ title: "成功", description: `商品「${data.name}」を更新しました。` });
      onSuccess(); 
    },
    onError: (error) => {
      toast({ title: "エラー", description: `商品の更新に失敗: ${error.message}`, variant: "destructive" });
    },
  });

  const onSubmit = (values: ProductFormValues) => {
    const productToUpdate: StripeProductUpdate = {
        name: values.name,
        description: values.description,
        active: values.active,
        metadata: values.role && values.role !== "none"
          ? { assigned_role: values.role } // Stripeのメタデータキーは assigned_role のまま
          : undefined,
    };
    updateProductMutation.mutate({ productId: product.id, data: productToUpdate });
  };

  React.useEffect(() => {
    if (product && isOpen && roles) {
      console.log("EditProductDialog: useEffect - product data:", JSON.stringify(product, null, 2));
      console.log("EditProductDialog: useEffect - roles data:", JSON.stringify(roles, null, 2));

      // metadata に保存されているロールIDを直接使用する
      const assignedRoleIdFromMetadata = product.metadata?.assigned_role;
      console.log("EditProductDialog: useEffect - assignedRoleIdFromMetadata:", assignedRoleIdFromMetadata);

      let determinedInitialRoleId = "none"; // デフォルトは "none"

      if (assignedRoleIdFromMetadata) {
        const foundRole = roles.find(r => r.id === assignedRoleIdFromMetadata);
        if (foundRole) {
          determinedInitialRoleId = foundRole.id;
          console.log("EditProductDialog: useEffect - Found role by ID in metadata:", JSON.stringify(foundRole, null, 2));
        } else {
          console.warn("EditProductDialog: useEffect - Role ID from metadata not found in roles list:", assignedRoleIdFromMetadata);
          const roleNameFallback = product.assigned_role_name;
          if (roleNameFallback) {
            const foundRoleByName = roles.find(r => r.name === roleNameFallback);
            if (foundRoleByName) {
              determinedInitialRoleId = foundRoleByName.id;
              console.log("EditProductDialog: useEffect - Found role by name (fallback from assigned_role_name):", JSON.stringify(foundRoleByName, null, 2));
            } else {
              console.warn("EditProductDialog: useEffect - Role name from assigned_role_name not found in roles list:", roleNameFallback);
            }
          }
        }
      } else {
        console.log("EditProductDialog: useEffect - No assigned_role in metadata.");
      }
      
      console.log("EditProductDialog: useEffect - Determined initialRoleId for form:", determinedInitialRoleId);

      form.reset({
        name: product.name || "",
        description: product.description || "",
        active: product.active,
        role: determinedInitialRoleId, // フォームのフィールド名を role に変更
      });
    } else if (isOpen && !product && !isLoadingRoles && !rolesError) {
      console.log("EditProductDialog: useEffect - Resetting form for new product or no roles.");
      form.reset({ name: "", description: "", active: true, role: "none" }); // フォームのフィールド名を role に変更
    }
  }, [product, isOpen, roles, form, isLoadingRoles, rolesError]);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>商品を編集</DialogTitle>
          <DialogDescription>商品情報を変更します。ID: {product.id}</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8 py-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }: { field: ControllerRenderProps<ProductFormValues, 'name'> }) => (
                <FormItem>
                  <FormLabel>商品名 *</FormLabel>
                  <FormControl><Input placeholder="例: プレミアムプラン" {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }: { field: ControllerRenderProps<ProductFormValues, 'description'> }) => (
                <FormItem>
                  <FormLabel>説明</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="商品の詳細な説明"
                      className="resize-none"
                      {...field}
                      value={field.value ?? ''} 
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="active"
              render={({ field }: { field: ControllerRenderProps<ProductFormValues, 'active'> }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">有効ステータス</FormLabel>
                    <FormDescription>この商品を有効/無効にします。</FormDescription>
                  </div>
                  <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} /></FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="role" // フォームフィールド名を role に変更
              render={({ field }) => (
                <FormItem>
                  <FormLabel>ロール (購入後)</FormLabel> {/* ラベルを調整 (任意) */}
                  <Select 
                    onValueChange={field.onChange} 
                    value={field.value || "none"} 
                    disabled={isLoadingRoles || !roles}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="ロールを選択してください" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="none">割り当てなし</SelectItem>
                      {roles?.map((role) => (
                        <SelectItem key={role.id} value={role.id}>
                          {role.name} {role.description ? `(${role.description})` : ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    この商品を購入したユーザーに自動的に割り当てられるロールです。
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose} disabled={updateProductMutation.isPending}>
                キャンセル
              </Button>
              <Button type="submit" disabled={updateProductMutation.isPending || isLoadingRoles}>
                {updateProductMutation.isPending ? "更新中..." : "変更を保存"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
} 
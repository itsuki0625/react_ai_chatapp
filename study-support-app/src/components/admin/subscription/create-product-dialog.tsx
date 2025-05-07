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
import { createProduct } from '@/lib/api/admin'; // API関数
import { StripeProductCreate, StripeProductResponse } from '@/types/stripe'; // 型定義
import { getRoles } from '@/services/adminService'; // ★ getRoles をインポート (パスは適宜調整)
import { Role } from '@/types/user'; // ★ Role型をインポート (パスは適宜調整)

// フォームのバリデーションスキーマ
const formSchema = z.object({
  name: z.string().min(1, { message: "商品名は必須です。" }),
  description: z.string().optional(),
  active: z.boolean().default(true),
  assigned_role: z.string().optional(), // ★ 追加: 割り当てるロール名
});

type ProductFormValues = z.infer<typeof formSchema>;

interface CreateProductDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void; 
}

export function CreateProductDialog({ isOpen, onClose, onSuccess }: CreateProductDialogProps) {
  const { toast } = useToast();

  const form = useForm<ProductFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      active: true,
      assigned_role: "", // ★ 追加
    },
  });

  // ロール一覧を取得
  const { data: roles, isLoading: isLoadingRoles } = useQuery<Role[]>({
    queryKey: ['adminRoles'],
    queryFn: getRoles,
    enabled: isOpen, // ダイアログが開いているときだけ取得
  });

  // 商品作成APIを呼び出す Mutation
  const createProductMutation = useMutation<
    StripeProductResponse, 
    Error, 
    StripeProductCreate
  >({
    mutationFn: createProduct,
    onSuccess: (data) => {
      toast({ title: "成功", description: `商品「${data.name}」を作成しました。` });
      onSuccess(); 
      form.reset(); 
    },
    onError: (error) => {
      toast({ title: "エラー", description: `商品の作成に失敗: ${error.message}`, variant: "destructive" });
    },
  });

  const onSubmit = (values: ProductFormValues) => {
    const productToCreate: StripeProductCreate = {
        name: values.name,
        description: values.description || undefined, // null より undefined の方が一般的かも
        active: values.active,
        metadata: values.assigned_role ? { assigned_role: values.assigned_role } : undefined, // ★ 修正: undefined も許容
    };
    createProductMutation.mutate(productToCreate);
  };

  React.useEffect(() => {
    if (!isOpen) {
      form.reset();
    }
  }, [isOpen, form]);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>新しい商品を作成</DialogTitle>
          <DialogDescription>Stripeに新しい商品を追加します。</DialogDescription>
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
                    <FormDescription>この商品を有効にしますか？</FormDescription>
                  </div>
                  <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} /></FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="assigned_role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>割り当てるロール (購入後)</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger disabled={isLoadingRoles}>
                        <SelectValue placeholder="ロールを選択してください" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="">割り当てなし</SelectItem>
                      {roles?.map((role) => (
                        <SelectItem key={role.id} value={role.name}>
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
              <Button type="button" variant="outline" onClick={onClose} disabled={createProductMutation.isPending || isLoadingRoles}>
                キャンセル
              </Button>
              <Button type="submit" disabled={createProductMutation.isPending || isLoadingRoles}>
                {createProductMutation.isPending ? "作成中..." : "商品を作成"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
} 
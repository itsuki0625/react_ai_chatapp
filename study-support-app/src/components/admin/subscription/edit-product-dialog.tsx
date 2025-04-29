'use client';

import React from 'react';
import { ControllerRenderProps, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation } from '@tanstack/react-query';
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
import { useToast } from "@/hooks/use-toast";
import { updateProduct } from '@/lib/api/admin'; // API関数
import { StripeProductUpdate, StripeProductResponse, StripeProductWithPricesResponse } from '@/types/stripe';

// フォームのバリデーションスキーマ (Update用)
const formSchema = z.object({
  name: z.string().min(1, { message: "商品名は必須です。" }),
  description: z.string().optional().nullable(),
  active: z.boolean(),
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
    defaultValues: {
      name: product.name || "",
      description: product.description || "",
      active: product.active,
    },
  });

  // 商品更新APIを呼び出す Mutation
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
    };
    updateProductMutation.mutate({ productId: product.id, data: productToUpdate });
  };

  React.useEffect(() => {
    if (product) {
      form.reset({
        name: product.name || "",
        description: product.description || "",
        active: product.active,
      });
    }
  }, [product, form]);

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
            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose} disabled={updateProductMutation.isPending}>
                キャンセル
              </Button>
              <Button type="submit" disabled={updateProductMutation.isPending}>
                {updateProductMutation.isPending ? "更新中..." : "変更を保存"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
} 
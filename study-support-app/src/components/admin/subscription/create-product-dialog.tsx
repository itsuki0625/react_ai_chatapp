'use client';

import React from 'react';
import { ControllerRenderProps, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
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
import { createProduct } from '@/lib/api/admin'; // API関数
import { StripeProductCreate, StripeProductResponse } from '@/types/stripe'; // 型定義

// フォームのバリデーションスキーマ
const formSchema = z.object({
  name: z.string().min(1, { message: "商品名は必須です。" }),
  description: z.string().optional(),
  active: z.boolean().default(true),
});

type ProductFormValues = z.infer<typeof formSchema>;

interface CreateProductDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void; 
}

export function CreateProductDialog({ isOpen, onClose, onSuccess }: CreateProductDialogProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const form = useForm<ProductFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      active: true,
    },
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
      onSuccess(); // 親コンポーネントに成功を通知 (リスト更新は親で行う)
      form.reset(); 
    },
    onError: (error) => {
      toast({ title: "エラー", description: `商品の作成に失敗: ${error.message}`, variant: "destructive" });
    },
  });

  const onSubmit = (values: ProductFormValues) => {
    const productToCreate: StripeProductCreate = {
        name: values.name,
        description: values.description || null,
        active: values.active,
        metadata: null 
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
            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose} disabled={createProductMutation.isPending}>
                キャンセル
              </Button>
              <Button type="submit" disabled={createProductMutation.isPending}>
                {createProductMutation.isPending ? "作成中..." : "商品を作成"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
} 
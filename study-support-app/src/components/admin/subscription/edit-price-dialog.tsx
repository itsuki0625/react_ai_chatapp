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
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { updatePrice } from '@/lib/api/admin'; 
import { StripePriceUpdate, StripePriceResponse } from '@/types/stripe';

// フォームのバリデーションスキーマ (Price Update用)
const formSchema = z.object({
  active: z.boolean(),
  lookup_key: z.string().optional().nullable(),
});

type PriceFormValues = z.infer<typeof formSchema>;

interface EditPriceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void; 
  price: StripePriceResponse; // 編集対象の価格データ
}

export function EditPriceDialog({ isOpen, onClose, onSuccess, price }: EditPriceDialogProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const form = useForm<PriceFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      active: price.active,
      lookup_key: price.lookup_key || "",
    },
  });

  // 価格更新APIを呼び出す Mutation
  const updatePriceMutation = useMutation<
    StripePriceResponse,
    Error,
    { priceId: string; data: StripePriceUpdate }
  >({
    mutationFn: (variables) => updatePrice(variables.priceId, variables.data),
    onSuccess: (data) => {
      toast({ title: "成功", description: `価格 (ID: ${data.id}) を更新しました。` });
      onSuccess(); 
    },
    onError: (error) => {
      toast({ title: "エラー", description: `価格の更新に失敗: ${error.message}`, variant: "destructive" });
    },
  });

  const onSubmit = (values: PriceFormValues) => {
    const priceToUpdate: StripePriceUpdate = {
        active: values.active,
        lookup_key: values.lookup_key || null,
    };
    updatePriceMutation.mutate({ priceId: price.id, data: priceToUpdate });
  };

  React.useEffect(() => {
    if (price) {
      form.reset({
        active: price.active,
        lookup_key: price.lookup_key || "",
      });
    }
  }, [price, form]);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>価格を編集</DialogTitle>
          <DialogDescription>
            価格情報を変更します。Price ID: {price.id} <br />
            <span className="text-xs text-muted-foreground">商品 ID: {price.product}</span>
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8 py-4">
            <FormField
              control={form.control}
              name="active"
              render={({ field }: { field: ControllerRenderProps<PriceFormValues, 'active'> }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">有効ステータス</FormLabel>
                    <FormDescription>この価格を有効/無効にします。</FormDescription>
                  </div>
                  <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} /></FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="lookup_key"
              render={({ field }: { field: ControllerRenderProps<PriceFormValues, 'lookup_key'> }) => (
                <FormItem>
                  <FormLabel>ルックアップキー (任意)</FormLabel>
                  <FormControl><Input placeholder="例: premium_monthly" {...field} value={field.value ?? ''} /></FormControl>
                  <FormDescription>API経由で価格を取得する際に使用できる一意のキー。</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose} disabled={updatePriceMutation.isPending}>
                キャンセル
              </Button>
              <Button type="submit" disabled={updatePriceMutation.isPending}>
                {updatePriceMutation.isPending ? "更新中..." : "変更を保存"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
} 
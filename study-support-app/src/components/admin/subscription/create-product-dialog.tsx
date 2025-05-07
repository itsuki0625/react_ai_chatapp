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
import { adminService } from '@/services/adminService'; // ★ adminService をインポート
import { 
  StripeProductCreate, 
  StripeDbProductData // ★ DB保存後のデータ型をインポート
} from '@/types/stripe'; // 型定義
import { getRoles } from '@/services/adminService'; // ★ getRoles をインポート (パスは適宜調整)
import { Role } from '@/types/user'; // ★ Role型をインポート (パスは適宜調整)

// フォームのバリデーションスキーマ
const formSchema = z.object({
  name: z.string().min(1, { message: "商品名は必須です。" }),
  description: z.string().optional(),
  active: z.boolean().default(true),
  assigned_role: z.string().optional(), // ★ ここにはロールIDが文字列として入る
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
      assigned_role: "__NONE__", // デフォルトは「割り当てなし」を示すID (または空文字)
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
    StripeDbProductData, // ★ レスポンス型を StripeDbProductData に変更
    Error, 
    StripeProductCreate
  >({
    mutationFn: adminService.createProduct, // ★ adminService.createProduct を使用
    onSuccess: (data: StripeDbProductData) => { // ★ data の型を明示
      // data にはDBのID (data.id) や Stripeの商品ID (data.stripe_product_id) が含まれる
      toast({ title: "成功", description: `商品「${data.name}」(Stripe ID: ${data.stripe_product_id}) を作成し、DBに保存しました。DB ID: ${data.id}` });
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
        description: values.description || undefined,
        active: values.active,
        metadata: values.assigned_role && values.assigned_role !== "__NONE__" 
                    ? { assigned_role: values.assigned_role } // ★ values.assigned_role はロールID
                    : undefined,
    };
    console.log("Creating product with metadata:", productToCreate.metadata); // 送信内容確認用ログ
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
              name="assigned_role" // このフィールドにはロールIDがセットされる
              render={({ field }) => (
                <FormItem>
                  <FormLabel>割り当てるロール (購入後)</FormLabel>
                  <Select 
                    onValueChange={field.onChange} 
                    value={field.value || "__NONE__"} // field.value にはロールIDが期待される
                    disabled={isLoadingRoles}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="ロールを選択してください" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="__NONE__">割り当てなし</SelectItem>
                      {roles?.map((role) => (
                        // ★ SelectItemのvalueにrole.idを設定
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
'use client';

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  // DialogClose, // Explicit close button is optional
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { RoleRead, RoleCreate, RoleUpdate } from '@/types/role';

// Validation Schema
const roleFormSchema = z.object({
  name: z.string().min(1, { message: "ロール名は必須です。" }).max(50, { message: "50文字以内で入力してください。" }),
  description: z.string().max(200, { message: "200文字以内で入力してください。" }).optional().nullable(),
  is_active: z.boolean().default(true),
});

type RoleFormValues = z.infer<typeof roleFormSchema>;

interface RoleDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: RoleCreate | RoleUpdate) => void;
  role: RoleRead | null; // Role being edited (null for add mode)
  mode: 'add' | 'edit';
  isLoading: boolean; // Loading state for save operation
}

export const RoleDialog: React.FC<RoleDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  role,
  mode,
  isLoading,
}) => {
  const form = useForm<RoleFormValues>({
    resolver: zodResolver(roleFormSchema),
    // Set initial default values
    defaultValues: {
      name: '',
      description: '', // Use empty string initially
      is_active: true,
    },
  });

  // Effect to reset form when role or mode changes
  // biome-ignore lint/correctness/useExhaustiveDependencies: <explanation>
useEffect(() => {
    if (mode === 'edit' && role) {
      form.reset({
        name: role.name,
        description: role.description ?? '', // Handle null from API
        is_active: role.is_active,
      });
    } else {
      form.reset({ // Reset for 'add' mode
        name: '',
        description: '',
        is_active: true,
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role, mode]); // form.reset is stable, no need to include form

  const onSubmit = (values: RoleFormValues) => {
    console.log("Role form submitted:", values);
    // Prepare data for saving, ensuring description is null if empty
    const dataToSave = {
        ...values,
        description: values.description || null,
    };
    onSave(dataToSave);
  };

  return (
    // Control the Dialog open state using the isOpen prop
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]" onInteractOutside={(e) => e.preventDefault()} /* Prevent closing on overlay click */>
        <DialogHeader>
          <DialogTitle>{mode === 'add' ? '新規ロール作成' : 'ロール編集'}</DialogTitle>
          <DialogDescription>
            {mode === 'add' ? '新しいロールの情報を入力してください。' : `ロール '${role?.name || ''}' の情報を編集します。`}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>ロール名 <span className="text-red-500">*</span></FormLabel>
                  <FormControl>
                    <Input placeholder="例: プレミアム会員" {...field} disabled={isLoading} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>説明</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="このロールの目的や権限について説明します (任意)。"
                      className="resize-none"
                      {...field}
                      value={field.value ?? ''} // Ensure value is not null for textarea
                      disabled={isLoading}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm bg-white">
                  <div className="space-y-0.5">
                    <FormLabel>アクティブ</FormLabel>
                    <p className="text-xs text-muted-foreground">
                      非アクティブなロールは新規ユーザーに割り当てられません。
                    </p>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      disabled={isLoading}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
             <DialogFooter className="pt-4">
                  <Button type="button" variant="outline" onClick={onClose} disabled={isLoading}>
                    キャンセル
                  </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                    <><svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> 保存中...</>
                 ) : (
                    '保存'
                 )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}; 
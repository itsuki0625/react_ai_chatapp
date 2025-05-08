'use client';

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { User } from '@/types/user';
import { RoleRead } from '@/types/role';
import { UserCreatePayload, UserUpdatePayload } from '@/services/adminService';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from 'react-hot-toast';

// Validation Schema - Ensure it matches form fields
const passwordSchema = z.string()
  .min(8, { message: "パスワードは8文字以上である必要があります。" })
  .regex(/[a-z]/, { message: "パスワードには小文字を含める必要があります。" })
  .regex(/[A-Z]/, { message: "パスワードには大文字を含める必要があります。" })
  .regex(/[0-9]/, { message: "パスワードには数字を含める必要があります。" });

const userFormSchema = z.object({
  name: z.string().min(1, { message: "名前は必須です。" }),
  email: z.string().email({ message: "有効なメールアドレスを入力してください。" }),
  role: z.string().min(1, { message: "ロールを選択してください。" }), // API expects string role name
  status: z.enum(['active', 'inactive', 'pending', 'unpaid']), // Ensure 'unpaid' is included
  // passwordは新規作成時のみ必須とするバリデーションを refine で行う
  password: z.string().optional(),
  confirmPassword: z.string().optional(),
}).refine(data => {
  // パスワードが入力されていれば、強度と一致をチェック
  if (data.password) {
    // 強度チェック - 新規作成時またはパスワード変更時
    try {
      passwordSchema.parse(data.password); // 強度要件をチェック
    } catch (e: any) {
      // バリデーションエラーがあれば refine でエラーとする
      // Zodのエラーメッセージを使うため、ここでは false を返すだけで良い
      return false;
    }
    // 一致チェック
    if (data.password !== data.confirmPassword) {
      return false;
    }
  }
  return true;
}, {
  // refine のエラーメッセージは、どのフィールドに紐づけるかで挙動が変わる
  // ここでは password フィールドに紐づける例（強度 or 一致エラーのどちらかを示す汎用メッセージ）
  // より詳細なメッセージが必要な場合は、refine を分けるか、フィールドレベルのバリデーションを調整
  message: "パスワードの要件を満たしていないか、確認用パスワードと一致しません。",
  path: ["password"], // または ["confirmPassword"]
}).refine(data => {
    // 新規作成時 (user propがnullの場合) はパスワードが必須
    // この refine は mode を参照できないため、onSubmit で別途チェックするのが現実的
    // ※ useForm の context を使うなどの方法もあるが複雑になる
    return true;
});

type UserFormValues = z.infer<typeof userFormSchema>;

interface UserDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  mode: 'view' | 'edit' | 'add';
  onSave: (data: UserCreatePayload | UserUpdatePayload) => void;
  availableRoles: RoleRead[];
  isLoadingRoles: boolean;
}

// Helper: API Payload
const createSavePayload = (data: UserFormValues): UserCreatePayload | UserUpdatePayload => {
    // --- 型定義を adminService.ts から参照 ---
    type ExpectedRole = UserCreatePayload['role'];
    type ExpectedStatus = UserCreatePayload['status'];
    // --- ここまで ---

    const payload: Partial<UserCreatePayload & UserUpdatePayload> = {
        // --- FIX: Map form 'name' to backend 'full_name' ---
        full_name: data.name,
        // -----------------------------------------------------
        email: data.email,
        role: data.role as ExpectedRole, // Role from form should already match expected strings
        status: data.status as ExpectedStatus, // Status from form needs to match expected strings ('unpaid' がもしバックエンドで非対応なら別途対応要)
    };
    if (data.password) {
        payload.password = data.password;
    }
    // The final object should conform to either Create or Update payload
    return payload as UserCreatePayload | UserUpdatePayload;
};

// Helper: Date Formatter (using Intl.DateTimeFormat)
const formatModalDate = (dateString: string | undefined | null): string => {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
        if (isNaN(date.getTime())) {
            return dateString;
        }
        return new Intl.DateTimeFormat('ja-JP', {
             year: 'numeric', month: 'numeric', day: 'numeric',
             hour: 'numeric', minute: 'numeric', second: 'numeric',
             hour12: false,
             timeZone: 'Asia/Tokyo'
        }).format(date);
    } catch (e) {
        console.error("Modal Date formatting error:", e);
        return dateString;
    }
};

const UserDetailsModal: React.FC<UserDetailsModalProps> = ({
  isOpen,
  onClose,
  user,
  mode,
  onSave,
  availableRoles,
  isLoadingRoles,
}) => {
  const isViewMode = mode === 'view';
  const isAddMode = mode === 'add';

  // Correctly destructure errors from formState
  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<UserFormValues>({
    resolver: zodResolver(userFormSchema),
    defaultValues: {
      name: '', email: '', role: '', status: 'pending', password: '', confirmPassword: '',
    }
  });

  // Reset form effect (no changes needed here)
  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && user) {
        reset({
          name: user.name, email: user.email, role: user.role, status: user.status,
          password: '', confirmPassword: '',
        });
      } else if (mode === 'add') {
        reset({
          name: '', email: '', role: '', status: 'pending',
          password: '', confirmPassword: '',
        });
      } else {
         reset({}); // Reset for view mode or unexpected cases
      }
    }
  }, [isOpen, user, mode, reset]);

  // onSubmit handler - Explicitly check mode is not 'view'
  const onSubmit = (data: UserFormValues) => {
    console.log("Form Data:", data);
    // Prevent submission in view mode
    if (mode === 'view') {
        console.error("onSubmit called in view mode, aborting.");
        toast.error("不正な操作です。"); // Inform user
        return;
    }
    // Check password requirement for add mode
    if (isAddMode && !data.password) {
      toast.error('新規作成時はパスワードが必須です。');
      return;
    }
    // Now mode is confirmed 'add' or 'edit'
    const payload = createSavePayload(data); // Pass only data

    // --- ★デバッグ用ログ追加: 送信するペイロードの内容を確認 ---
    console.log("Payload being sent:", JSON.stringify(payload, null, 2));
    console.log("Role value being sent:", payload.role); // role の値を具体的に確認
    // ----------------------------------------------------

    onSave(payload);
  };

  // Role Display Map (no changes needed here)
  const roleDisplayMap: Record<string, string> = {
    "管理者": '管理者', "教員": '先生', "生徒": '生徒',
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {mode === 'add' ? '新規ユーザー追加' : mode === 'edit' ? 'ユーザー情報編集' : 'ユーザー詳細'}
          </DialogTitle>
          {mode !== 'view' && (
            <DialogDescription>
              {mode === 'add' ? '新しいユーザーの情報を入力してください。' : `ユーザー '${user?.name || ''}' の情報を編集します。`}
            </DialogDescription>
          )}
        </DialogHeader>

        {isViewMode && user ? (
          // --- View Mode ---
          <div className="grid gap-4 py-4">
             {/* Display fields - using corrected date format */}
             <div className="grid grid-cols-4 items-center gap-4">
               <Label className="text-right text-sm font-medium">ID</Label>
               <div className="col-span-3 text-sm text-gray-700">{user.id}</div>
             </div>
             <div className="grid grid-cols-4 items-center gap-4">
               <Label className="text-right text-sm font-medium">名前</Label>
               <div className="col-span-3 text-sm text-gray-700">{user.name}</div>
             </div>
             <div className="grid grid-cols-4 items-center gap-4">
               <Label className="text-right text-sm font-medium">メール</Label>
               <div className="col-span-3 text-sm text-gray-700">{user.email}</div>
             </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right text-sm font-medium">ロール</Label>
              <div className="col-span-3 text-sm text-gray-700">{roleDisplayMap[user.role] || user.role}</div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right text-sm font-medium">ステータス</Label>
              <div className="col-span-3 text-sm text-gray-700">{user.status}</div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right text-sm font-medium">登録日時</Label>
              <div className="col-span-3 text-sm text-gray-700">{formatModalDate(user.createdAt)}</div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right text-sm font-medium">最終ログイン</Label>
              <div className="col-span-3 text-sm text-gray-700">{formatModalDate(user.lastLogin)}</div>
            </div>
          </div>
        ) : (
          // --- Edit/Add Mode ---
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
             {/* Name */}
             <div className="grid grid-cols-4 items-center gap-4">
               <Label htmlFor="name" className="text-right">名前 <span className="text-red-500">*</span></Label>
               <div className="col-span-3">
                 <Input id="name" {...register("name")} className={errors.name ? 'border-red-500' : ''} />
                 {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>}
               </div>
             </div>
             {/* Email */}
             <div className="grid grid-cols-4 items-center gap-4">
               <Label htmlFor="email" className="text-right">メール <span className="text-red-500">*</span></Label>
               <div className="col-span-3">
                 <Input id="email" type="email" {...register("email")} className={errors.email ? 'border-red-500' : ''} />
                 {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
               </div>
             </div>

              {/* Role Select (Standard HTML) */}
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="role" className="text-right">ロール <span className="text-red-500">*</span></Label>
                <div className="col-span-3">
                  <select
                    id="role"
                    {...register("role")}
                    className={`w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.role ? 'border-red-500' : 'border-gray-300'} ${isLoadingRoles ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                    disabled={isLoadingRoles}
                  >
                    <option value="" disabled={mode === 'add'}>-- ロールを選択 --</option>
                    {availableRoles.map(r => (
                      <option key={r.id} value={r.name}>
                         {roleDisplayMap[r.name] || r.name}
                      </option>
                    ))}
                  </select>
                   {errors.role && <p className="text-xs text-red-500 mt-1">{errors.role.message}</p>}
                   {isLoadingRoles && <p className="text-xs text-gray-500 mt-1">ロールを読み込み中...</p>}
                </div>
              </div>

              {/* Status Select */}
             <div className="grid grid-cols-4 items-center gap-4">
               <Label htmlFor="status" className="text-right">ステータス <span className="text-red-500">*</span></Label>
                 <div className="col-span-3">
                   <select
                     id="status"
                     {...register("status")}
                     className={`w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.status ? 'border-red-500' : 'border-gray-300'}`}
                   >
                     <option value="active">アクティブ</option>
                     <option value="inactive">非アクティブ</option>
                     <option value="pending">保留中</option>
                     <option value="unpaid">未決済</option>
                   </select>
                   {errors.status && <p className="text-xs text-red-500 mt-1">{errors.status.message}</p>}
                 </div>
              </div>

              {/* Password */}
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="password" className="text-right">パスワード {isAddMode && <span className="text-red-500">*</span>}</Label>
                 <div className="col-span-3">
                    <Input id="password" type="password" {...register("password")} placeholder={mode === 'edit' ? '変更する場合のみ入力' : ''} className={errors.password ? 'border-red-500' : ''} />
                    {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
                 </div>
              </div>

               {/* Confirm Password */}
               {watch("password") && (
                 <div className="grid grid-cols-4 items-center gap-4">
                   <Label htmlFor="confirmPassword" className="text-right">パスワード確認 {isAddMode && <span className="text-red-500">*</span>}</Label>
                   <div className="col-span-3">
                     <Input id="confirmPassword" type="password" {...register("confirmPassword")} className={errors.confirmPassword ? 'border-red-500' : ''} />
                     {errors.confirmPassword && <p className="text-xs text-red-500 mt-1">{errors.confirmPassword.message}</p>}
                   </div>
                 </div>
               )}


            </div>

            {/* Footer for Edit/Add Mode */}
            <DialogFooter className="pt-4">
              <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
                キャンセル
              </Button>
              <Button type="submit" disabled={isSubmitting || isLoadingRoles}>
                {isSubmitting ? '保存中...' : '保存'}
              </Button>
            </DialogFooter>
          </form>
        )}
        {/* Footer for View Mode */}
         {isViewMode && (
             <DialogFooter className="pt-4">
                 <Button type="button" variant="outline" onClick={onClose}>閉じる</Button>
             </DialogFooter>
         )}
      </DialogContent>
    </Dialog>
  );
};

export default UserDetailsModal; 
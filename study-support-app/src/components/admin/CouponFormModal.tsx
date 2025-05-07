"use client";

import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { couponAdminService } from '@/services/couponService';
import { StripeCouponCreateSchema, StripeCouponUpdateSchema, StripeCouponResponse, StripeCouponCreate, StripeCouponUpdate } from '@/types/coupon';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription, DialogClose } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea"; // For metadata JSON input
import { useToast } from "@/hooks/use-toast";
import { Calendar } from "@/components/ui/calendar" // For date picker
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover" // For date picker
import { Calendar as CalendarIcon } from "lucide-react"
import { format } from "date-fns"
import { cn } from "@/lib/utils"

interface CouponFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: StripeCouponResponse | null; // Pass coupon data for editing
}

// Base object schema without refinement first
const baseFormObjectSchema = z.object({
    name: z.string().optional(),
    duration: z.enum(['forever', 'once', 'repeating']).optional(),
    duration_in_months: z.number().int().positive().optional(),
    max_redemptions: z.number().int().positive().optional(),
    redeem_by: z.number().int().optional(),
    metadata: z.string().optional(), // Keep as string for Textarea
    discountType: z.enum(['percent', 'amount']).optional(),
    discountValue: z.string().optional(),
    currency: z.string().length(3).optional(),
    // Fields from StripeCouponCreateSchema needed for refinement
    // These are not directly in the form state but used for validation context if needed
    // Let's rely on refine logic using discountType and discountValue for now.
});

// Refine the base schema
const formSchema = baseFormObjectSchema.superRefine((data, ctx) => {
    const discountValueStr = data.discountValue || ''

    // --- Interdependency checks ---

    // 1. Discount Type/Value/Currency Check
    if (data.discountType === 'amount') {
        const amount = parseInt(discountValueStr, 10);
        if (isNaN(amount) || amount <= 0) {
             ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: "割引額は正の整数で入力してください。",
                path: ["discountValue"],
             });
        }
        if (!data.currency) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: "通貨を選択してください。",
                path: ["currency"],
            });
        }
    }
    else if (data.discountType === 'percent') {
        const percent = parseFloat(discountValueStr);
        if (isNaN(percent) || percent <= 0 || percent > 100) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: "割引率は0より大きく100以下の数値を入力してください。",
                path: ["discountValue"],
            });
        }
    }
    // Don't require discountType on initial load, but check on submit if needed (handled in onSubmit)

    // 2. Duration/Duration in Months Check
    if (data.duration === 'repeating' && (!data.duration_in_months || data.duration_in_months <= 0)) {
        ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "期間が「繰り返し」の場合、月数を正の整数で入力してください。",
            path: ["duration_in_months"],
        });
    }

    // 3. ★ NEW: Forever duration only allowed with percent discount ★
    if (data.duration === 'forever' && data.discountType === 'amount') {
        ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "期間「永続」はパーセント割引でのみ利用可能です。固定額割引は選択できません。",
            path: ["duration"], // Or path: ["discountType"]
        });
        // Optionally add issue to discountType as well
        ctx.addIssue({
             code: z.ZodIssueCode.custom,
             message: "期間「永続」が選択されているため、固定額割引は利用できません。",
             path: ["discountType"],
        });
    }

});

export const CouponFormModal: React.FC<CouponFormModalProps> = ({ isOpen, onClose, initialData }) => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const isEditMode = !!initialData;

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: initialData?.name ?? '',
      duration: initialData?.duration ?? 'once',
      duration_in_months: initialData?.duration_in_months === null ? undefined : initialData?.duration_in_months,
      max_redemptions: initialData?.max_redemptions === null ? undefined : initialData?.max_redemptions,
      redeem_by: initialData?.redeem_by_timestamp ? initialData.redeem_by_timestamp : undefined,
      metadata: initialData?.metadata_ ? JSON.stringify(initialData.metadata_, null, 2) : '{}',
      discountType: initialData?.percent_off ? 'percent' : (initialData?.amount_off ? 'amount' : undefined),
      discountValue: initialData?.percent_off?.toString() ?? initialData?.amount_off?.toString() ?? '',
      currency: 'jpy',
    },
  });

   const [redeemByDate, setRedeemByDate] = useState<Date | undefined>(
        initialData?.redeem_by_timestamp ? new Date(initialData.redeem_by_timestamp * 1000) : undefined
    );

  // Reset form when initialData changes (e.g., opening edit modal)
  useEffect(() => {
    if (initialData) {
      const discountType = initialData.percent_off ? 'percent' : (initialData.amount_off ? 'amount' : undefined);
      const discountValue = initialData.percent_off?.toString() ?? initialData.amount_off?.toString() ?? '';
       const redeemDate = initialData.redeem_by_timestamp ? new Date(initialData.redeem_by_timestamp * 1000) : undefined;

      form.reset({
        name: initialData.name ?? '',
        duration: initialData.duration ?? 'once',
        duration_in_months: initialData.duration_in_months === null || initialData.duration_in_months === undefined ? undefined : initialData.duration_in_months,
        max_redemptions: initialData.max_redemptions === null || initialData.max_redemptions === undefined ? undefined : initialData.max_redemptions,
        redeem_by: initialData.redeem_by_timestamp === null || initialData.redeem_by_timestamp === undefined ? undefined : initialData.redeem_by_timestamp,
        metadata: initialData.metadata_ ? JSON.stringify(initialData.metadata_, null, 2) : '{}',
        discountType: discountType,
        discountValue: discountValue,
        currency: 'jpy',
      });
        setRedeemByDate(redeemDate);
    } else {
      // Reset for create mode
      form.reset({
        name: '',
        duration: 'once',
        duration_in_months: undefined,
        max_redemptions: undefined,
        redeem_by: undefined,
        metadata: '{}',
        discountType: undefined,
        discountValue: '',
        currency: 'jpy',
      });
        setRedeemByDate(undefined);
    }
  }, [initialData, form, isOpen]); // Depend on isOpen to reset when modal opens

  // --- Mutations ---
  const createMutation = useMutation({
    mutationFn: couponAdminService.createAndImportCoupon,
    onSuccess: () => {
      toast({ title: "成功", description: "Couponが作成されました。" });
      queryClient.invalidateQueries({ queryKey: ['adminDbCoupons'] });
      onClose(); // Close modal on success
    },
    onError: (error: Error) => {
      toast({ variant: "destructive", title: "作成エラー", description: error.message });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ couponId, updateData }: { couponId: string; updateData: StripeCouponUpdate }) =>
      couponAdminService.updateDbCoupon(couponId, updateData),
    onSuccess: () => {
      toast({ title: "成功", description: "Couponが更新されました。" });
      queryClient.invalidateQueries({ queryKey: ['adminDbCoupons'] });
      onClose(); // Close modal on success
    },
    onError: (error: Error) => {
      toast({ variant: "destructive", title: "更新エラー", description: error.message });
    },
  });

  const isLoading = createMutation.isPending || updateMutation.isPending;

  // --- Form Submission Handler ---
  const onSubmit = (values: z.infer<typeof formSchema>) => {
    console.log("Form values:", values);

    // --- Prepare data for API ---
    let apiData: StripeCouponCreate | StripeCouponUpdate = {};
    let metadataObject: Record<string, string> | undefined;

    // Parse metadata JSON string
    try {
        metadataObject = values.metadata ? JSON.parse(values.metadata) : undefined;
         if (metadataObject && typeof metadataObject === 'object' && metadataObject !== null) {
             Object.keys(metadataObject).forEach(key => {
                 if (typeof metadataObject![key] !== 'string') {
                     throw new Error(`メタデータキー "${key}" の値は文字列である必要があります。`);
                 }
             });
         } else if (values.metadata && values.metadata.trim() !== '{}' && values.metadata.trim() !== '') {
            throw new Error("メタデータは有効なJSONオブジェクト（キー/値は文字列）である必要があります。例: {\"ref\": \"promo123\"}");
         }
    } catch (e) {
        const message = e instanceof Error ? e.message : "無効なJSON形式です。";
        form.setError("metadata", { type: "manual", message: message });
        return;
    }

    if (isEditMode && initialData) {
        // Prepare update data (only name and metadata are typically updatable)
        // Ensure apiData only includes fields allowed for update by StripeCouponUpdate
        const updatePayload: StripeCouponUpdate = {
            name: values.name || undefined,
            metadata: metadataObject,
        };
        console.log("Submitting update data:", updatePayload);
        updateMutation.mutate({ couponId: initialData.id, updateData: updatePayload });

    } else {
        // Prepare create data
        // Explicitly construct the payload ensuring correct types
        const createPayload: Partial<StripeCouponCreate> = {
            name: values.name || undefined,
            duration: values.duration,
            // Fix: Ensure duration_in_months is number | undefined
            duration_in_months: values.duration === 'repeating' ? (values.duration_in_months ? Number(values.duration_in_months) : undefined) : undefined,
            // Fix: Ensure max_redemptions is number | undefined
            max_redemptions: values.max_redemptions ? Number(values.max_redemptions) : undefined,
            redeem_by: redeemByDate ? Math.floor(redeemByDate.getTime() / 1000) : undefined,
            metadata: metadataObject,
        };

        // Handle discount type and value (ensure correct types)
        if (values.discountType === 'percent') {
            const percentValue = values.discountValue ? parseFloat(values.discountValue) : undefined;
             if (percentValue === undefined || isNaN(percentValue) || percentValue <= 0 || percentValue > 100) {
                form.setError("discountValue", { type: "manual", message: "割引率は0より大きく100以下の数値を入力してください。" });
                return;
             }
            createPayload.percent_off = percentValue;
        } else if (values.discountType === 'amount') {
             const amountValue = values.discountValue ? parseInt(values.discountValue, 10) : undefined;
             if (amountValue === undefined || isNaN(amountValue) || amountValue <= 0) {
                 form.setError("discountValue", { type: "manual", message: "割引額は正の整数値を入力してください。" });
                 return;
             }
            createPayload.amount_off = amountValue;
            createPayload.currency = values.currency || 'jpy';
             if (!createPayload.currency) {
                 form.setError("currency", { type: "manual", message: "割引額を指定する場合は通貨も必須です。" });
                 return;
             }
        } else {
             toast({ variant: "destructive", title: "エラー", description: "割引タイプを選択してください。" });
             return;
        }

        console.log("Submitting create data:", createPayload);

        // Validate with the precise Zod schema before sending
        const validationResult = StripeCouponCreateSchema.safeParse(createPayload);
        if (!validationResult.success) {
            console.error("Zod validation failed:", validationResult.error.errors);
            validationResult.error.errors.forEach(err => {
                const field = err.path[0] as keyof z.infer<typeof baseFormObjectSchema>;
                 if (field && field in baseFormObjectSchema.shape) {
                     form.setError(field, { message: err.message });
                 } else {
                      console.warn("Unhandled Zod error path:", err.path);
                      toast({ variant: "destructive", title: "入力エラー", description: err.message });
                 }
            });
            return;
        }

        createMutation.mutate(validationResult.data);
    }
  };

  // Watch duration to conditionally show duration_in_months
  const watchedDuration = form.watch("duration");
  const watchedDiscountType = form.watch("discountType");

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>{isEditMode ? 'Coupon 編集' : '新規 Coupon 作成'}</DialogTitle>
          <DialogDescription>
            {isEditMode ? `Coupon ID: ${initialData?.id}` : '新しい Stripe Coupon を作成します。'}
             {!isEditMode && <span className="text-sm text-muted-foreground block"> 割引タイプ、期間、割引率/額は作成後に変更できません。</span>}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto p-1 pr-3">

            {/* Name */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>名前 (Optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="例: 新規ユーザー向け10%オフ" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Discount Type and Value */}
            <FormField
              control={form.control}
              name="discountType"
                disabled={isEditMode} // Disable changing type/value in edit mode
              render={({ field }) => (
                <FormItem className="space-y-3">
                  <FormLabel>割引タイプ *</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      className="flex space-x-4"
                                disabled={isEditMode}
                    >
                      <FormItem className="flex items-center space-x-2 space-y-0">
                        <FormControl>
                          <RadioGroupItem value="percent" />
                        </FormControl>
                        <FormLabel className="font-normal">パーセント</FormLabel>
                      </FormItem>
                      <FormItem className="flex items-center space-x-2 space-y-0">
                        <FormControl>
                          <RadioGroupItem value="amount" />
                        </FormControl>
                        <FormLabel className="font-normal">固定額</FormLabel>
                      </FormItem>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

             {watchedDiscountType === 'percent' && (
                 <FormField
                    control={form.control}
                    name="discountValue"
                    disabled={isEditMode}
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>割引率 (%) *</FormLabel>
                        <FormControl>
                             <Input type="number" placeholder="例: 10" {...field} step="0.01" min="0.01" max="100" />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                 />
             )}

             {watchedDiscountType === 'amount' && (
                <div className="flex space-x-4">
                    <FormField
                        control={form.control}
                        name="discountValue"
                        disabled={isEditMode}
                        render={({ field }) => (
                            <FormItem className="flex-1">
                            <FormLabel>割引額 *</FormLabel>
                            <FormControl>
                                <Input type="number" placeholder="例: 500 (金額)" {...field} step="1" min="1" />
                            </FormControl>
                            <FormMessage />
                            </FormItem>
                        )}
                    />
                     <FormField
                        control={form.control}
                        name="currency"
                         disabled={isEditMode}
                        render={({ field }) => (
                            <FormItem className="w-[100px]">
                             <FormLabel>通貨 *</FormLabel>
                             <Select onValueChange={field.onChange} defaultValue={field.value || 'jpy'} disabled={isEditMode}>
                                <FormControl>
                                 <SelectTrigger>
                                     <SelectValue placeholder="通貨" />
                                 </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                 <SelectItem value="jpy">JPY</SelectItem>
                                 {/* Add other currencies if needed */}
                                </SelectContent>
                             </Select>
                             <FormMessage />
                            </FormItem>
                        )}
                     />
                 </div>
             )}


            {/* Duration */}
            <FormField
              control={form.control}
              name="duration"
                disabled={isEditMode}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>期間 *</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value} disabled={isEditMode}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="期間を選択" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="forever">永続</SelectItem>
                      <SelectItem value="once">1回のみ</SelectItem>
                      <SelectItem value="repeating">繰り返し</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Duration in Months (Conditional) */}
            {watchedDuration === 'repeating' && (
              <FormField
                control={form.control}
                name="duration_in_months"
                  disabled={isEditMode}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>期間（月数）*</FormLabel>
                    <FormControl>
                      <Input type="number" placeholder="例: 12" {...field} min="1" step="1" onChange={e => field.onChange(parseInt(e.target.value, 10))} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {/* Max Redemptions */}
            <FormField
              control={form.control}
              name="max_redemptions"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>最大利用回数 (Optional)</FormLabel>
                  <FormControl>
                     <Input type="number" placeholder="未入力の場合は無制限" {...field} min="1" step="1" onChange={e => field.onChange(parseInt(e.target.value, 10))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Redeem By */}
            <FormField
              control={form.control}
              name="redeem_by" // Keep timestamp in form state
              render={({ field }) => (
                <FormItem className="flex flex-col">
                  <FormLabel>有効期限 (Optional)</FormLabel>
                   <Popover>
                     <PopoverTrigger asChild>
                         <FormControl>
                         <Button
                             variant={"outline"}
                             className={cn(
                             "w-[240px] pl-3 text-left font-normal",
                             !redeemByDate && "text-muted-foreground"
                             )}
                         >
                             {redeemByDate ? (
                             format(redeemByDate, "yyyy/MM/dd")
                             ) : (
                             <span>日付を選択</span>
                             )}
                             <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                         </Button>
                         </FormControl>
                     </PopoverTrigger>
                     <PopoverContent className="w-auto p-0" align="start">
                         <Calendar
                         mode="single"
                         selected={redeemByDate}
                         onSelect={(date: Date | undefined) => {
                             setRedeemByDate(date);
                             // Update form state with timestamp when date is selected
                             field.onChange(date ? Math.floor(date.getTime() / 1000) : undefined);
                         }}
                         disabled={(date: Date) => date < new Date(new Date().setHours(0,0,0,0)) } // Add type annotation
                         initialFocus
                         />
                     </PopoverContent>
                   </Popover>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Metadata */}
            <FormField
              control={form.control}
              name="metadata"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>メタデータ (Optional, JSON)</FormLabel>
                  <FormControl>
                     <Textarea placeholder={`{\n  "key": "value",\n  "campaign": "summer_sale"\n}`} {...field} rows={4} />
                  </FormControl>
                   <FormDescription>
                     キーと値が文字列の有効なJSONオブジェクトを入力してください。
                   </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* TODO: Add applies_to field if needed (likely requires product selection UI) */}

            <DialogFooter>
                <DialogClose asChild>
                    <Button type="button" variant="outline" onClick={onClose}>
                        キャンセル
                    </Button>
                </DialogClose>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? '保存中...' : (isEditMode ? '更新' : '作成')}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}; 
import { z } from 'zod';

// Base schema for common fields
export const StripeCouponBaseSchema = z.object({
  id: z.string(), // Stripe ID
  name: z.string().nullable().optional(),
  duration: z.enum(['forever', 'once', 'repeating']),
  duration_in_months: z.number().int().positive().nullable().optional(),
  amount_off: z.number().int().positive().nullable().optional(),
  percent_off: z.number().gt(0).lte(100).nullable().optional(),
  currency: z.string().length(3).nullable().optional(),
  redeem_by: z.number().int().nullable().optional(), // Unix timestamp
  max_redemptions: z.number().int().positive().nullable().optional(),
  times_redeemed: z.number().int().nonnegative(),
  valid: z.boolean(),
  metadata: z.record(z.string()).nullable().optional(),
  created: z.number().int(), // Unix timestamp
  livemode: z.boolean(),
  object: z.literal('coupon'),
  applies_to: z.object({
    products: z.array(z.string())
  }).nullable().optional(),
});

// Schema for creating a coupon (matches backend Pydantic)
export const StripeCouponCreateSchema = z.object({
    name: z.string().optional(),
    percent_off: z.number().gt(0).lte(100).optional(),
    amount_off: z.number().int().positive().optional(),
    currency: z.string().length(3).optional(),
    duration: z.enum(['forever', 'once', 'repeating']),
    duration_in_months: z.number().int().positive().optional(),
    max_redemptions: z.number().int().positive().optional(),
    redeem_by: z.number().int().optional(), // Unix timestamp
    metadata: z.record(z.string()).optional(),
    applies_to: z.object({
        products: z.array(z.string())
    }).optional(),
})
// Add refinement for interdependent fields (similar to backend checks)
.refine(data => !(data.amount_off && data.percent_off), {
    message: "割引額と割引率は同時に指定できません。",
    path: ["amount_off"], // Attach error to one field or make it global
})
.refine(data => data.amount_off !== undefined || data.percent_off !== undefined, {
    message: "割引額または割引率のどちらかが必要です。",
    path: ["amount_off"],
})
.refine(data => !(data.amount_off && !data.currency), {
    message: "割引額を指定する場合は通貨も指定してください。",
    path: ["currency"],
})
.refine(data => !(data.duration === 'repeating' && !data.duration_in_months), {
    message: "期間タイプが repeating の場合は duration_in_months を指定してください。",
    path: ["duration_in_months"],
});


// Schema for updating a coupon (matches backend Pydantic)
export const StripeCouponUpdateSchema = z.object({
  name: z.string().optional(),
  metadata: z.record(z.string()).optional(),
});

// TypeScript types inferred from Zod schemas
export type StripeCouponResponse = z.infer<typeof StripeCouponBaseSchema>;
export type StripeCouponCreate = z.infer<typeof StripeCouponCreateSchema>;
export type StripeCouponUpdate = z.infer<typeof StripeCouponUpdateSchema>; 
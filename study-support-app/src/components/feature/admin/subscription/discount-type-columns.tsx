'use client';

import React from 'react'; 
import { ColumnDef } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { DiscountTypeResponse } from "@/types/subscription";
// import { DataTableColumnHeader } from "@/components/ui/data-table-column-header"; // 列ヘッダー用

// アクションセル
// const ActionsCell = ({ row, onEdit, onDelete }: {
//   row: any; // Row<DiscountTypeResponse>; // TODO: 型を正しくする
//   onEdit: (discountType: DiscountTypeResponse) => void;
//   onDelete: (discountTypeId: string) => void;
// }) => {
//   const discountType = row.original as DiscountTypeResponse;
//
//   return (
//     <DropdownMenu>
//       <DropdownMenuTrigger asChild>
//         <Button variant="ghost" className="h-8 w-8 p-0">
//           <span className="sr-only">Open menu</span>
//           <MoreHorizontal className="h-4 w-4" />
//         </Button>
//       </DropdownMenuTrigger>
//       <DropdownMenuContent align="end">
//         <DropdownMenuLabel>アクション</DropdownMenuLabel>
//         <DropdownMenuItem onClick={() => onEdit(discountType)}>
//           編集
//         </DropdownMenuItem>
//         <DropdownMenuItem 
//           onClick={() => onDelete(discountType.id)} 
//           className="text-red-600"
//         >
//           削除
//         </DropdownMenuItem>
//       </DropdownMenuContent>
//     </DropdownMenu>
//   );
// };

// カラム定義
export const columns = (): ColumnDef<DiscountTypeResponse>[] => [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && "indeterminate")
        }
        onCheckedChange={(value: boolean) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value: boolean) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "name",
    header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>名前</Button>
    ),
    cell: ({ row }) => <div className="font-medium">{row.getValue("name")}</div>,
  },
  {
    accessorKey: "description",
    header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>説明</Button>
    ),
    cell: ({ row }) => (
      <div className="text-sm text-muted-foreground truncate max-w-xs">
        {row.getValue("description") || '-'}
      </div>
    ),
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>作成日時</Button>
    ),
    cell: ({ row }) => (
      <div>{new Date(row.getValue("created_at")).toLocaleString('ja-JP')}</div>
    ),
  },
]; 
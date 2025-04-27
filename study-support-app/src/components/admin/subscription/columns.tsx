'use client';

import React from 'react'; // React をインポート
import { ColumnDef, Row, Table as ReactTable, Column } from '@tanstack/react-table';
import { ArrowUpDown, MoreHorizontal, Pencil, ChevronDown, ChevronRight } from 'lucide-react'; // Chevron アイコンを追加
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
// Popover は不要になったので削除
// import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"; 
import { StripeProductWithPricesResponse, StripePriceResponse } from "@/types/stripe";

// オプション型は変更なし
interface ProductColumnsOptions {
  onEdit: (product: StripeProductWithPricesResponse) => void;
  onArchive: (productId: string) => void;
  onEditPrice: (price: StripePriceResponse) => void;
}

// ActionsCell は変更なし
const ActionsCell = ({ row, onEdit, onArchive }: {
  row: Row<StripeProductWithPricesResponse>;
  onEdit: (product: StripeProductWithPricesResponse) => void;
  onArchive: (productId: string) => void;
}) => {
  const product = row.original;

  const handleEditClick = () => {
    onEdit(product);
  };

  const handleArchiveClick = () => {
    onArchive(product.id);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0">
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>アクション</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => navigator.clipboard.writeText(product.id)}>
          商品IDをコピー
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleEditClick}>編集</DropdownMenuItem>
        <DropdownMenuItem onClick={handleArchiveClick} className="text-red-600">
          アーカイブ
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

// フォーマット関数はそのまま
const formatCurrency = (amount: number | null | undefined, currency: string) => {
  if (amount === null || amount === undefined) return '-';
  return new Intl.NumberFormat('ja-JP', { style: 'currency', currency: currency }).format(amount / 100);
};
const formatRecurring = (recurring: StripePriceResponse['recurring']) => {
  if (!recurring) return '都度払い';
  const intervalMap: { [key: string]: string } = {
    day: '日', week: '週', month: '月', year: '年',
  };
  const interval = intervalMap[recurring.interval] || recurring.interval;
  return `${recurring.interval_count > 1 ? recurring.interval_count : ''}${interval}ごと`;
};


// columns 定義を修正
export const columns = ({ onEdit, onArchive, onEditPrice }: ProductColumnsOptions): ColumnDef<StripeProductWithPricesResponse>[] => [
  // 行展開用の列を追加
  {
    id: 'expander',
    header: () => null, // ヘッダー不要
    cell: ({ row }: { row: Row<StripeProductWithPricesResponse> }) => {
      return (
        <Button
          variant="ghost"
          size="sm"
          onClick={row.getToggleExpandedHandler()} // 展開ハンドラ
          disabled={!row.getCanExpand()} // 展開できない場合は無効化 (価格がない場合など)
          className="w-8 h-8 p-0"
          aria-label={row.getIsExpanded() ? "折りたたむ" : "展開する"}
        >
          {row.getIsExpanded() ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </Button>
      );
    },
  },
  // select 列は変更なし
  {
    id: "select",
    // ... header/cell
    header: ({ table }: { table: ReactTable<StripeProductWithPricesResponse> }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && "indeterminate")
        }
        onCheckedChange={(value: boolean) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }: { row: Row<StripeProductWithPricesResponse> }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value: boolean) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  // id, name, description, active 列は変更なし
  {
    accessorKey: "id",
    header: "商品ID",
    cell: ({ row }: { row: Row<StripeProductWithPricesResponse> }) => <div className="lowercase">{row.getValue("id")}</div>,
  },
  {
    accessorKey: "name",
    header: ({ column }: { column: Column<StripeProductWithPricesResponse, unknown> }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          商品名
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }: { row: Row<StripeProductWithPricesResponse> }) => <div className="font-medium">{row.getValue("name")}</div>,
  },
  {
    accessorKey: "description",
    header: "説明",
    cell: ({ row }: { row: Row<StripeProductWithPricesResponse> }) => (
      <div className="text-sm text-muted-foreground truncate max-w-xs">
        {row.getValue("description") || '-'}
      </div>
    ),
  },
  {
    accessorKey: "active",
    header: "ステータス",
    cell: ({ row }: { row: Row<StripeProductWithPricesResponse> }) => {
      const isActive = row.getValue("active") as boolean;
      return <Badge variant={isActive ? "outline" : "secondary"}>{isActive ? "有効" : "無効"}</Badge>;
    },
  },
  // 価格列 (prices) を削除
  // {
  //   accessorKey: "prices",
  //   header: "価格",
  //   cell: ({ row }: { row: Row<StripeProductWithPricesResponse> }) => { ... Popover logic ... }
  // },
  // actions 列は変更なし
  {
    id: "actions",
    enableHiding: false,
    cell: ({ row }: { row: Row<StripeProductWithPricesResponse>}) => <ActionsCell row={row} onEdit={onEdit} onArchive={onArchive} />,
  },
]; 
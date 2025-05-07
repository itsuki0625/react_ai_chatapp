'use client';

import React from 'react'; // React をインポート
import { ColumnDef, Row, Table as ReactTable, Column } from '@tanstack/react-table';
import { ArrowUpDown, MoreHorizontal, ChevronDown, ChevronRight } from 'lucide-react'; // Remove Pencil
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
import { StripeProductWithPricesResponse } from "@/types/stripe";
import { useQuery } from '@tanstack/react-query'; // 追加
import { getRoles } from '@/services/adminService'; // 追加
import { Role } from '@/types/user'; // 追加

// オプション型から onEditPrice を削除
interface ProductColumnsOptions {
  onEdit: (product: StripeProductWithPricesResponse) => void;
  onArchive: (productId: string) => void;
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

// columns 定義を修正 (引数から onEditPrice を削除)
export const columns = ({ onEdit, onArchive }: ProductColumnsOptions): ColumnDef<StripeProductWithPricesResponse>[] => [
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
  {
    accessorKey: "metadata.assigned_role",
    header: "割り当てロール",
    cell: ({ row }: { row: Row<StripeProductWithPricesResponse> }) => {
      const assignedRoleId = row.original.metadata?.assigned_role;

      const { data: roles, isLoading, error } = useQuery<Role[], Error>({
        queryKey: ['roles'],
        queryFn: getRoles,
        staleTime: 1000 * 60 * 5,
      });

      if (isLoading) return <span className="text-xs text-muted-foreground">読込中...</span>;
      if (error) return <span className="text-xs text-red-500">エラー</span>;
      
      if (assignedRoleId && roles) {
        const role = roles.find(r => r.id === assignedRoleId);
        return role ? <Badge variant="outline">{role.name}</Badge> : <span className="text-xs text-muted-foreground">不明なロールID</span>;
      }
      return <span className="text-xs text-muted-foreground">割り当てなし</span>;
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
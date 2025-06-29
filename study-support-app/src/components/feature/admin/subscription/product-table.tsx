'use client';

import * as React from "react";
import {
  ColumnDef,
  // ... other react-table imports
  flexRender,
  getCoreRowModel,
  getExpandedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  Table as ReactTableInstance,
  HeaderGroup,
  Column as ReactTableColumn,
  Row as ReactTableRow,
  Cell as ReactTableCell,
  ExpandedState,
  SortingState,
  ColumnFiltersState,
  VisibilityState
} from "@tanstack/react-table";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { ChevronDown, Pencil } from "lucide-react";
import { StripePriceResponse } from "@/types/stripe";

// 価格フォーマット関数 (columns.tsx からコピーまたはインポート)
const formatCurrency = (amount: number | null | undefined, currency: string) => {
  if (amount === null || amount === undefined) return '-';
  return new Intl.NumberFormat('ja-JP', { style: 'currency', currency: currency }).format(amount / 100);
};
const formatRecurring = (recurring: StripePriceResponse['recurring']) => {
  if (!recurring) return '都度払い';
  const intervalMap: { [key: string]: string } = { day: '日', week: '週', month: '月', year: '年' };
  const interval = intervalMap[recurring.interval] || recurring.interval;
  return `${recurring.interval_count > 1 ? recurring.interval_count : ''}${interval}ごと`;
};

// DataTableProps の TData に制約を追加 (prices プロパティを持つことを期待)
interface DataTableProps<TData extends { prices: StripePriceResponse[] }, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  // onEditPrice を columns から受け取るのではなく、Table 自体に渡す方法も検討可
  onEditPrice: (price: StripePriceResponse) => void;
}

export function ProductTable<TData extends { prices: StripePriceResponse[] }, TValue>({ 
  columns, 
  data, 
  onEditPrice // props で受け取る
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = React.useState({});
  const [expanded, setExpanded] = React.useState<ExpandedState>({}); // 展開状態の state

  const table: ReactTableInstance<TData> = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      expanded, // 展開状態をテーブルに渡す
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    onExpandedChange: setExpanded, // 展開状態の変更ハンドラ
    getExpandedRowModel: getExpandedRowModel(), // 展開モデルを取得
    // 行が展開可能かどうかの判定 (例: prices が存在するか)
    getRowCanExpand: (row: ReactTableRow<TData>) => !!row.original.prices && row.original.prices.length > 0,
  });

  return (
    <div className="w-full">
      {/* Filter and Column Visibility (変更なし) */}
      <div className="flex items-center py-4">
        <Input
          placeholder="商品名でフィルター..."
          value={(table.getColumn("name")?.getFilterValue() as string) ?? ""}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            table.getColumn("name")?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="ml-auto">
              表示列 <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {table
              .getAllColumns()
              .filter((column: ReactTableColumn<TData, unknown>) => column.getCanHide())
              .map((column: ReactTableColumn<TData, unknown>) => {
                return (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    className="capitalize"
                    checked={column.getIsVisible()}
                    onCheckedChange={(value: boolean) =>
                      column.toggleVisibility(!!value)
                    }
                  >
                    {/* Display Header instead of ID if possible */} 
                    {typeof column.columnDef.header === 'string' 
                      ? column.columnDef.header 
                      : column.id}
                  </DropdownMenuCheckboxItem>
                );
              })}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {/* Header rendering (変更なし) */}
            {table.getHeaderGroups().map((headerGroup: HeaderGroup<TData>) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id} style={{ width: header.getSize() !== 150 ? header.getSize() : undefined }}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row: ReactTableRow<TData>) => (
                <React.Fragment key={row.id}> 
                  <TableRow data-state={row.getIsSelected() && "selected"}>
                    {row.getVisibleCells().map((cell: ReactTableCell<TData, unknown>) => (
                      <TableCell key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                  {row.getIsExpanded() && (
                    <TableRow>
                      <TableCell colSpan={row.getVisibleCells().length} className="p-0">
                        <div className="p-4 bg-muted/50">
                          <h5 className="text-sm font-semibold mb-2">価格情報</h5>
                          {row.original.prices.length > 0 ? (
                            <ul className="space-y-2">
                              {row.original.prices.map((price) => (
                                <li key={price.id} className="flex justify-between items-center text-sm border-b pb-2 last:border-b-0">
                                  <div>
                                    <span>{formatCurrency(price.unit_amount, price.currency)} ({formatRecurring(price.recurring)})</span>
                                    <span className={`ml-2 text-xs ${price.active ? 'text-green-600' : 'text-red-600'}`}>
                                      {price.active ? '有効' : '無効'}
                                    </span>
                                    <p className="text-xs text-muted-foreground">ID: {price.id}</p>
                                    {price.lookup_key && <p className="text-xs text-muted-foreground">キー: {price.lookup_key}</p>}
                                  </div>
                                  <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    className="h-7 w-7 p-0" 
                                    onClick={() => onEditPrice(price)} // Call handler passed via props
                                    aria-label="価格を編集"
                                  >
                                    <Pencil className="h-4 w-4" />
                                  </Button>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-sm text-muted-foreground">この商品には価格が設定されていません。</p>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  結果が見つかりません。
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination (変更なし) */}
      <div className="flex items-center justify-end space-x-2 py-4">
        {/* ... pagination buttons ... */}
         <div className="flex-1 text-sm text-muted-foreground">
          {table.getFilteredSelectedRowModel().rows.length} of{" "}
          {table.getFilteredRowModel().rows.length} row(s) selected.
        </div>
        <div className="space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            前へ
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            次へ
          </Button>
        </div>
      </div>
    </div>
  );
} 
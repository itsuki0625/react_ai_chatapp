"use client"

import * as React from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { 
    DropdownMenu, 
    DropdownMenuCheckboxItem, 
    DropdownMenuContent, 
    DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  isLoading?: boolean // Optional loading state prop
  // Add filterColumn prop if needed for global filtering
  filterColumn?: string 
  // Add onRowClick prop if needed
  onRowClick?: (row: TData) => void
}

export function DataTable<TData, TValue>({
  columns,
  data,
  isLoading = false, // Default to false
  filterColumn, // Destructure filterColumn
  onRowClick, // Destructure onRowClick
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({}) // Add visibility state
  const [rowSelection, setRowSelection] = React.useState({}) // Add row selection state if needed
  const [globalFilter, setGlobalFilter] = React.useState('') // State for global filter

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setColumnFilters,
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility, // Add visibility handler
    onRowSelectionChange: setRowSelection, // Add row selection handler if needed
    onGlobalFilterChange: setGlobalFilter, // Add global filter handler
    state: {
      sorting,
      columnFilters,
      columnVisibility, // Pass visibility state
      rowSelection, // Pass row selection state
      globalFilter, // Pass global filter state
    },
  })

  // Handle global filtering input change
  const handleGlobalFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setGlobalFilter(event.target.value)
  }

  const numRows = table.getRowModel().rows?.length || 0;
  const numCols = columns.length;

  return (
    <div>
        {/* Optional Global Filter Input */} 
        {filterColumn && (
             <div className="flex items-center py-4">
                <Input
                placeholder={`Filter by ${filterColumn}...`}
                value={globalFilter ?? ''}
                onChange={handleGlobalFilterChange}
                className="max-w-sm"
                />
             </div>
        )}
        {/* Column Visibility Dropdown */} 
        <div className="flex items-center justify-end space-x-2 py-4">
            <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" className="ml-auto">
                表示列
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                {table
                .getAllColumns()
                .filter(
                    (column) => column.getCanHide()
                )
                .map((column) => {
                    return (
                    <DropdownMenuCheckboxItem
                        key={column.id}
                        className="capitalize"
                        checked={column.getIsVisible()}
                        onCheckedChange={(value) =>
                        column.toggleVisibility(!!value)
                        }
                    >
                        {/* Consider using header string or a custom name */} 
                        {typeof column.columnDef.header === 'string' ? column.columnDef.header : column.id}
                    </DropdownMenuCheckboxItem>
                    )
                })}
            </DropdownMenuContent>
            </DropdownMenu>
        </div>
        {/* Main Table */} 
        <div className="rounded-md border">
            <Table>
            <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => {
                    return (
                        <TableHead key={header.id}>
                        {header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                            )}
                        </TableHead>
                    )
                    })}
                </TableRow>
                ))}
            </TableHeader>
            <TableBody>
                {isLoading ? (
                     // Render Skeleton loaders when loading
                    Array.from({ length: 5 }).map((_, rowIndex) => (
                        <TableRow key={`loading-row-${rowIndex}`}>
                             {Array.from({ length: numCols }).map((_, colIndex) => (
                                <TableCell key={`loading-cell-${rowIndex}-${colIndex}`}>
                                    <Skeleton className="h-6 w-full" />
                                </TableCell>
                            ))}
                        </TableRow>
                    ))
                ) : numRows > 0 ? (
                table.getRowModel().rows.map((row) => (
                    <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    onClick={() => onRowClick && onRowClick(row.original)} // Conditionally add onClick
                    className={onRowClick ? "cursor-pointer" : ""} // Conditionally add cursor style
                    >
                    {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                    ))}
                    </TableRow>
                ))
                ) : (
                <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center">
                    データがありません。
                    </TableCell>
                </TableRow>
                )}
            </TableBody>
            </Table>
        </div>
        {/* Pagination Controls */} 
        <div className="flex items-center justify-end space-x-2 py-4">
            {/* Optional Row Selection Info */} 
            {Object.keys(rowSelection).length > 0 && (
                <div className="flex-1 text-sm text-muted-foreground">
                {table.getFilteredSelectedRowModel().rows.length} of{" "}
                {table.getFilteredRowModel().rows.length} row(s) selected.
                </div>
            )}
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
  )
} 
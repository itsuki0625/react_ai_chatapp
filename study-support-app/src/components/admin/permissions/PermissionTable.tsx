'use client';

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { PermissionRead } from '@/types/permission';

interface PermissionTableProps {
  permissions: PermissionRead[];
}

// Helper function to format date (similar to the one in AdminUsersPage)
const formatDate = (dateString: string | undefined | null): string => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
      return new Intl.DateTimeFormat('ja-JP', {
        year: 'numeric', month: 'numeric', day: 'numeric',
        hour: 'numeric', minute: 'numeric', second: 'numeric',
        hour12: false,
        timeZone: 'Asia/Tokyo'
      }).format(date);
    } catch (e) {
      console.error("Date formatting error:", e);
      return dateString;
    }
  };


export const PermissionTable: React.FC<PermissionTableProps> = ({
  permissions,
}) => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>権限名</TableHead>
          <TableHead>説明</TableHead>
          <TableHead>作成日時</TableHead>
          {/* <TableHead className="text-right">操作</TableHead> */}
        </TableRow>
      </TableHeader>
      <TableBody>
        {permissions.length === 0 ? (
          <TableRow>
            <TableCell colSpan={4} className="h-24 text-center text-gray-500">
              権限が見つかりません。
            </TableCell>
          </TableRow>
        ) : (
          permissions.map((permission) => (
            <TableRow key={permission.id}>
              <TableCell className="font-medium">
                 <Badge variant="secondary">{permission.name}</Badge>
              </TableCell>
              <TableCell className="text-sm text-gray-600 max-w-md truncate" title={permission.description || ''}>{permission.description || '-'}</TableCell>
              <TableCell className="text-sm text-gray-500">{formatDate(permission.created_at)}</TableCell>
              {/* <TableCell className="text-right space-x-1"> */}
                {/* Permissions are often static, so edit/delete might not be needed */}
                {/* Example buttons if needed in future:
                <Button variant="ghost" size="icon" title="編集" disabled> <Edit className="h-4 w-4" /> </Button>
                <Button variant="ghost" size="icon" title="削除" disabled className="text-red-600"> <Trash2 className="h-4 w-4" /> </Button>
                */}
              {/* </TableCell> */}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}; 
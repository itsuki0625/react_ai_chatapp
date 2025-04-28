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
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Edit, Trash2, Settings } from 'lucide-react'; // Settings アイコンをインポート
import { RoleRead } from '@/types/role';
import { useAuthHelpers } from '@/lib/authUtils'; // ★ インポート

interface RoleTableProps {
  roles: RoleRead[];
  onEdit: (role: RoleRead) => void;
  onDelete: (roleId: string) => void;
  onManagePermissions: (role: RoleRead) => void;
  isLoading?: boolean; // 削除時などのローディング状態
}

export const RoleTable: React.FC<RoleTableProps> = ({
  roles,
  onEdit,
  onDelete,
  onManagePermissions,
  isLoading = false,
}) => {
  const { isAdmin } = useAuthHelpers(); // ★ フックを使用

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ロール名</TableHead>
          <TableHead>説明</TableHead>
          <TableHead>状態</TableHead>
          <TableHead className="text-center">権限数</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {roles.length === 0 ? (
          <TableRow>
            <TableCell colSpan={5} className="h-24 text-center text-gray-500">
              ロールが見つかりません。新規ロールを追加してください。
            </TableCell>
          </TableRow>
        ) : (
          roles.map((role) => (
            <TableRow key={role.id}>
              <TableCell className="font-medium">{role.name}</TableCell>
              <TableCell className="text-sm text-gray-600 max-w-xs truncate" title={role.description || ''}>{role.description || '-'}</TableCell>
              <TableCell>
                <Badge variant={role.is_active ? 'default' : 'outline'}>
                  {role.is_active ? 'アクティブ' : '非アクティブ'}
                </Badge>
              </TableCell>
              <TableCell className="text-center">{role.permissions?.length ?? 0}</TableCell>
              <TableCell className="text-right space-x-1">
                {/* Manage Permissions Button - 管理者なら常に有効 */} 
                {(isAdmin /* || hasPermission('role_permission_assign') */) && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onManagePermissions(role)}
                    title="権限設定"
                    disabled={isLoading}
                  >
                    <Settings className="h-4 w-4" />
                  </Button>
                )}
                 {/* Edit Button - 管理者なら常に有効 */}
                 {(isAdmin /* || hasPermission('role_update') */) && (
                   <Button
                     variant="ghost"
                     size="icon"
                     onClick={() => onEdit(role)}
                     title="編集"
                     disabled={isLoading}
                   >
                     <Edit className="h-4 w-4" />
                   </Button>
                 )}
                {/* Delete Button - 管理者なら常に有効 */}
                {(isAdmin /* || hasPermission('role_delete') */) && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(role.id)}
                    title="削除"
                    disabled={isLoading}
                    className="text-red-600 hover:text-red-700 disabled:text-red-300"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}; 
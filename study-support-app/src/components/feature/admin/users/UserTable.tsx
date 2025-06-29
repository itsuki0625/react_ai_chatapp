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
import { Eye, Edit, Trash2 } from 'lucide-react';
import { User } from '@/types/user';
import { useAuthHelpers } from '@/lib/authUtils';

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

interface UserTableProps {
  users: User[];
  onViewDetails: (userId: string) => void;
  onEdit: (userId: string) => void;
  onDelete: (userId: string) => void;
  isLoading?: boolean;
}

export const UserTable: React.FC<UserTableProps> = ({
  users,
  onViewDetails,
  onEdit,
  onDelete,
  isLoading = false,
}) => {
  const { isAdmin } = useAuthHelpers();

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>名前</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>ロール</TableHead>
          <TableHead>ステータス</TableHead>
          <TableHead>最終ログイン</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.length === 0 ? (
          <TableRow>
            <TableCell colSpan={6} className="h-24 text-center text-gray-500">
              ユーザーが見つかりません。
            </TableCell>
          </TableRow>
        ) : (
          users.map((user) => (
            <TableRow key={user.id}>
              <TableCell className="font-medium">{user.name}</TableCell>
              <TableCell>{user.email}</TableCell>
              <TableCell>
                <Badge variant={user.role === '管理者' ? 'destructive' : user.role === '教員' ? 'secondary' : 'outline'}>
                  {user.role}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge variant={user.status === 'active' ? 'default' : 'secondary'}>
                  {user.status}
                </Badge>
              </TableCell>
              <TableCell className="text-sm text-gray-500">{formatDate(user.lastLogin)}</TableCell>
              <TableCell className="text-right space-x-1">
                {isAdmin && (
                  <Button
                     variant="ghost"
                     size="icon"
                     onClick={() => onViewDetails(user.id)}
                     title="詳細表示"
                     disabled={isLoading}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                )}
                {isAdmin && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onEdit(user.id)}
                    title="編集"
                    disabled={isLoading}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                )}
                {isAdmin && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(user.id)}
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
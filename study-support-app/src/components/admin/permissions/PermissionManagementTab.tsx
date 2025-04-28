'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { PermissionTable } from './PermissionTable'; // 作成したテーブルをインポート
import { PermissionRead } from '@/types/permission';
import { getPermissions } from '@/services/permissionService';

const PermissionManagementTab: React.FC = () => {
    // --- React Query Hook for fetching permissions ---
    const { data: permissions = [], isLoading, error } = useQuery<PermissionRead[], Error>({
        queryKey: ['permissions'],
        queryFn: () => getPermissions(), // permissionService から取得
    });

    // --- Render Logic ---
    if (isLoading) return <div className="text-center p-4">権限情報を読み込み中...</div>;
    if (error) return <div className="text-center p-4 text-red-600">エラーが発生しました: {error.message}</div>;

    return (
        <div>
            <h2 className="text-xl font-medium text-gray-800 mb-4">権限一覧</h2>
            <p className="text-sm text-gray-500 mb-6">
                システムで定義されている権限の一覧です。通常、これらの権限は開発者によって管理されます。
            </p>

            {/* Render PermissionTable */}
            <div className="border rounded-md">
                <PermissionTable permissions={permissions} />
            </div>
        </div>
    );
};

export default PermissionManagementTab; 
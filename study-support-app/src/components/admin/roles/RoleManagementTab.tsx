'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Plus, PlusCircle } from 'lucide-react';
import { RoleTable } from './RoleTable';
import { RoleDialog } from './RoleDialog';
import { RolePermissionsDialog } from './RolePermissionsDialog';
import { RoleRead, RoleCreate, RoleUpdate } from '@/types/role';
import { PermissionRead } from '@/types/permission';
import {
    getRoles,
    createRole,
    updateRole,
    deleteRole,
    setRolePermissions,
} from '@/services/roleService';
import { getPermissions } from '@/services/permissionService';
import { useAuthHelpers } from '@/lib/authUtils';

const RoleManagementTab: React.FC = () => {
    const queryClient = useQueryClient();
    const { isAdmin } = useAuthHelpers();
    const [isRoleDialogOpen, setIsRoleDialogOpen] = useState(false);
    const [isPermissionsDialogOpen, setIsPermissionsDialogOpen] = useState(false);
    const [selectedRole, setSelectedRole] = useState<RoleRead | null>(null);
    const [dialogMode, setDialogMode] = useState<'add' | 'edit'>('add');

    // --- React Query Hooks ---
    const { data: roles = [], isLoading: isLoadingRoles, error: errorRoles } = useQuery<RoleRead[], Error>({
        queryKey: ['roles'],
        queryFn: () => getRoles(),
    });

    const { data: permissions = [], isLoading: isLoadingPermissions } = useQuery<PermissionRead[], Error>({
        queryKey: ['permissions'],
        queryFn: () => getPermissions(),
        enabled: isPermissionsDialogOpen,
    });

    // --- Mutations ---
    const createRoleMutation = useMutation<RoleRead, Error, RoleCreate>({
        mutationFn: createRole,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            setIsRoleDialogOpen(false);
            alert('ロールを作成しました。');
        },
        onError: (error) => {
            console.error("ロール作成エラー:", error);
            alert(`ロールの作成に失敗しました: ${error.message}`);
        },
    });

    const updateRoleMutation = useMutation<RoleRead, Error, { id: string; data: RoleUpdate }>({
        mutationFn: async ({ id, data }) => updateRole(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            setIsRoleDialogOpen(false);
            setSelectedRole(null);
            alert('ロールを更新しました。');
        },
        onError: (error) => {
            console.error("ロール更新エラー:", error);
            alert(`ロールの更新に失敗しました: ${error.message}`);
        },
    });

    const deleteRoleMutation = useMutation<RoleRead, Error, string>({
        mutationFn: deleteRole,
        onSuccess: (_, deletedRoleId) => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            alert('ロールを削除しました。');
        },
        onError: (error) => {
            console.error("ロール削除エラー:", error);
            alert(`ロールの削除に失敗しました: ${error.message}`);
        },
    });

    const setPermissionsMutation = useMutation<RoleRead, Error, { roleId: string; permissionIds: string[] }>({
        mutationFn: setRolePermissions,
        onSuccess: (updatedRole) => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            queryClient.setQueryData<RoleRead[]>(['roles'], (oldData) => {
                const currentData = oldData ?? [];
                return currentData.map(role => role.id === updatedRole.id ? updatedRole : role);
            });
            setIsPermissionsDialogOpen(false);
            setSelectedRole(null);
            alert('ロールの権限を更新しました。');
        },
        onError: (error) => {
            console.error("権限設定エラー:", error);
            alert(`権限の設定に失敗しました: ${error.message}`);
        },
    });

    // --- Event Handlers ---
    const handleAddRole = () => {
        setSelectedRole(null);
        setDialogMode('add');
        setIsRoleDialogOpen(true);
    };

    const handleEditRole = (role: RoleRead) => {
        setSelectedRole(role);
        setDialogMode('edit');
        setIsRoleDialogOpen(true);
    };

    const handleDeleteRole = (roleId: string) => {
        if (confirm(`ロール ID: ${roleId} を削除してもよろしいですか？このロールが割り当てられているユーザーには影響が出る可能性があります。`)) {
            deleteRoleMutation.mutate(roleId);
        }
    };

    const handleManagePermissions = (role: RoleRead) => {
        setSelectedRole(role);
        setIsPermissionsDialogOpen(true);
    };

    const handleSaveRole = (data: RoleCreate | RoleUpdate) => {
        if (dialogMode === 'add') {
            createRoleMutation.mutate(data as RoleCreate);
        } else if (dialogMode === 'edit' && selectedRole) {
            updateRoleMutation.mutate({ id: selectedRole.id, data: data as RoleUpdate });
        }
    };

    const handleSavePermissions = (permissionIds: string[]) => {
        if (selectedRole) {
            setPermissionsMutation.mutate({ roleId: selectedRole.id, permissionIds });
        }
    };

    const handleCloseRoleDialog = () => {
        setIsRoleDialogOpen(false);
        setSelectedRole(null);
    };

    const handleClosePermissionsDialog = () => {
        setIsPermissionsDialogOpen(false);
        setSelectedRole(null);
    };

    // --- Render Logic ---
    if (isLoadingRoles) return <div className="text-center p-4">ロール情報を読み込み中...</div>;
    if (errorRoles) return <div className="text-center p-4 text-red-600">エラーが発生しました: {errorRoles.message}</div>;

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-medium text-gray-800">ロール管理</h2>
                {isAdmin && (
                    <Button onClick={handleAddRole} disabled={createRoleMutation.isPending}>
                        <PlusCircle className="mr-2 h-4 w-4" /> 新規ロール追加
                    </Button>
                )}
            </div>

            <div className="border rounded-md">
                <RoleTable
                    roles={roles}
                    onEdit={handleEditRole}
                    onDelete={handleDeleteRole}
                    onManagePermissions={handleManagePermissions}
                    isLoading={deleteRoleMutation.isPending}
                />
            </div>

            {isRoleDialogOpen && (
                <RoleDialog
                    isOpen={isRoleDialogOpen}
                    onClose={handleCloseRoleDialog}
                    onSave={handleSaveRole}
                    role={selectedRole}
                    mode={dialogMode}
                    isLoading={createRoleMutation.isPending || updateRoleMutation.isPending}
                />
            )}

            {isPermissionsDialogOpen && selectedRole && (
                <RolePermissionsDialog
                    isOpen={isPermissionsDialogOpen}
                    onClose={handleClosePermissionsDialog}
                    onSave={handleSavePermissions}
                    role={selectedRole}
                    allPermissions={permissions}
                    isLoadingPermissions={isLoadingPermissions}
                    isSaving={setPermissionsMutation.isPending}
                />
            )}
        </div>
    );
};

export default RoleManagementTab; 
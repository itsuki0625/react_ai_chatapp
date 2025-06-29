'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Label } from "@/components/ui/label";
import { RoleRead } from '@/types/role';
import { PermissionRead } from '@/types/permission';

interface RolePermissionsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (selectedPermissionIds: string[]) => void;
  role: RoleRead;
  allPermissions: PermissionRead[];
  isLoadingPermissions: boolean;
  isSaving: boolean;
}

export const RolePermissionsDialog: React.FC<RolePermissionsDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  role,
  allPermissions,
  isLoadingPermissions,
  isSaving,
}) => {
  // State for selected permission IDs
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Initialize based on role's current permissions
  // biome-ignore lint/correctness/useExhaustiveDependencies: <explanation>
useEffect(() => {
    if (role?.permissions) {
      setSelectedIds(new Set(role.permissions.map(p => p.id)));
    } else {
      setSelectedIds(new Set());
    }
  }, [role]); // Depends only on the role

  // Handle checkbox changes
  const handleCheckedChange = (permissionId: string, checked: boolean | "indeterminate") => {
     setSelectedIds(prev => {
        const newSet = new Set(prev);
        if (checked === true) {
            newSet.add(permissionId);
        } else {
            newSet.delete(permissionId);
        }
        return newSet;
     });
  };

  const handleSaveChanges = () => {
    onSave(Array.from(selectedIds));
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md" onInteractOutside={(e: Event) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle>&apos;{role.name}&apos; の権限設定</DialogTitle>
          <DialogDescription>
            このロールに割り当てる権限を選択してください。
          </DialogDescription>
        </DialogHeader>

        {isLoadingPermissions ? (
          <div className="flex justify-center items-center h-40">
             <p className="text-muted-foreground">権限リストを読み込み中...</p>
          </div>
        ) : allPermissions.length === 0 ? (
          <div className="text-center text-muted-foreground py-4">利用可能な権限がありません。</div>
        ) : (
          <ScrollArea className="h-72 w-full rounded-md border p-4 mt-4 mb-4 bg-muted/30">
             <div className="space-y-3">
                {allPermissions.map((permission) => (
                   <div key={permission.id} className="flex items-start space-x-3 p-2 rounded hover:bg-background transition-colors">
                        <Checkbox
                            id={`perm-${permission.id}`}
                            checked={selectedIds.has(permission.id)}
                            onCheckedChange={(checked: boolean | 'indeterminate') => handleCheckedChange(permission.id, checked)}
                            disabled={isSaving}
                            className="mt-1" // Align checkbox with the first line of label
                        />
                        <Label htmlFor={`perm-${permission.id}`} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex-grow cursor-pointer">
                            {permission.name}
                            {permission.description && (
                                <p className="text-xs text-muted-foreground font-normal mt-1">{permission.description}</p>
                            )}
                        </Label>
                   </div>
                ))}
             </div>
          </ScrollArea>
        )}

        <DialogFooter className="pt-4">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSaving}>
            キャンセル
          </Button>
          <Button
             type="button"
             onClick={handleSaveChanges}
             disabled={isSaving || isLoadingPermissions || allPermissions.length === 0}
          >
            {isSaving ? (
                <><svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> 保存中...</>
             ) : (
                '権限を保存'
             )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}; 
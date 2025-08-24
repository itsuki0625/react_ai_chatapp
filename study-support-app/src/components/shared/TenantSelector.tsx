'use client';

import { useTenant } from '@/contexts/TenantContext';
import { School } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface TenantSelectorProps {
  className?: string;
}

/**
 * 学校選択コンポーネント（システム管理者用）
 */
export function TenantSelector({ className }: TenantSelectorProps) {
  const { 
    currentSchool, 
    availableSchools, 
    switchSchool, 
    isSystemAdmin 
  } = useTenant();

  // システム管理者以外は表示しない
  if (!isSystemAdmin || availableSchools.length <= 1) {
    return null;
  }

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <School className="h-4 w-4 text-gray-500" />
      <Select
        value={currentSchool?.id || ''}
        onValueChange={switchSchool}
      >
        <SelectTrigger className="w-48">
          <SelectValue placeholder="学校を選択" />
        </SelectTrigger>
        <SelectContent>
          {availableSchools.map((school) => (
            <SelectItem key={school.id} value={school.id}>
              <div className="flex flex-col">
                <span className="font-medium">{school.name}</span>
                <span className="text-xs text-gray-500">{school.code}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

/**
 * 現在の学校情報を表示するコンポーネント
 */
export function CurrentSchoolInfo({ className }: { className?: string }) {
  const { currentSchool, currentUser } = useTenant();

  if (!currentSchool) {
    return null;
  }

  return (
    <div className={`flex items-center space-x-2 text-sm text-gray-600 ${className}`}>
      <School className="h-4 w-4" />
      <div className="flex flex-col">
        <span className="font-medium">{currentSchool.name}</span>
        {currentUser && (
          <span className="text-xs text-gray-500">
            {getRoleDisplayName(currentUser.role)}として参加中
          </span>
        )}
      </div>
    </div>
  );
}

function getRoleDisplayName(role: string): string {
  const roleNames = {
    school_admin: '学校管理者',
    teacher: '先生',
    student: '生徒',
    admin: 'システム管理者'
  };
  
  return roleNames[role as keyof typeof roleNames] || role;
}
import { PermissionRead } from './permission'; // 作成した permission.ts からインポート

// Backend RoleRead schema
export interface RoleRead {
  id: string; // UUID
  name: string;
  description?: string | null;
  is_active: boolean;
  permissions: PermissionRead[]; // Import PermissionRead
  created_at: string; // DateTime
  updated_at: string; // DateTime
}

// Backend RoleCreate schema
export interface RoleCreate {
  name: string;
  description?: string | null;
  is_active?: boolean; // Default is True on backend, so optional here
}

// Backend RoleUpdate schema
export interface RoleUpdate {
  name?: string | null; // Allow null to potentially unset? Check API behavior. Usually optional string is fine.
  description?: string | null;
  is_active?: boolean | null;
} 
// study-support-app/src/types/permission.ts
export interface PermissionRead {
  id: string; // UUID は string として扱うのが一般的
  name: string;
  description?: string | null;
  created_at: string; // DateTime は string (ISO 8601) として扱う
  updated_at: string; // DateTime は string (ISO 8601) として扱う
}

// 必要に応じて PermissionCreate, PermissionUpdate も定義できますが、
// 今回の UI では直接使用しないため PermissionRead のみ定義します。
// export interface PermissionCreate {
//   name: string;
//   description?: string | null;
// }
// export interface PermissionUpdate {
//   name?: string;
//   description?: string | null;
// } 
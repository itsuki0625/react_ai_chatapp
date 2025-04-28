import { PermissionRead } from '@/types/permission';

// Assume fetchWithAuth exists in lib for authenticated requests
import { fetchWithAuth } from '@/lib/fetchWithAuth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';

// GET /api/v1/permissions
export const getPermissions = async (params?: { skip?: number; limit?: number }): Promise<PermissionRead[]> => {
  const queryParams = new URLSearchParams(params as Record<string, string>).toString();
  const url = `${API_BASE_URL}/api/v1/permissions${queryParams ? '?' + queryParams : ''}`;
  console.log(`Fetching permissions from: ${url}`);
  // Permissions are often public, but use fetchWithAuth if authentication is required
  const response = await fetchWithAuth(url);
  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch permissions:', response.status, errorText);
    throw new Error(`Failed to fetch permissions: ${response.statusText}`);
  }
  const data = await response.json();
  console.log('Received permissions:', data);
  return data;
};

// --- CRUD for Permissions (Optional) ---
// If you need UI to manage permissions themselves (less common),
// implement createPermission, updatePermission, deletePermission similarly
// to how it was done in roleService.ts, using the corresponding
// /api/v1/permissions endpoints (POST /, PUT /{id}, DELETE /{id}).

/*
Example for creating a permission (if needed):

import { PermissionCreate } from '@/types/permission'; // Assuming you define this type

export const createPermission = async (data: PermissionCreate): Promise<PermissionRead> => {
  const url = `${API_BASE_URL}/api/v1/permissions`;
  const response = await fetchWithAuth(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
     const errorData = await response.json().catch(() => ({ detail: 'Failed to create permission' }));
     throw new Error(errorData.detail || `Failed to create permission: ${response.statusText}`);
  }
  return response.json();
};
*/ 
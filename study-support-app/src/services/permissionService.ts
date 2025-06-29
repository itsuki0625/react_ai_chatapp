import { PermissionRead } from '@/types/permission';
import { apiClient } from '@/lib/api';

// GET /api/v1/permissions
export const getPermissions = async (params?: { skip?: number; limit?: number }): Promise<PermissionRead[]> => {
  try {
    console.log('Fetching permissions from API');
    const response = await apiClient.get('/api/v1/permissions/', { params });
    console.log('Received permissions:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch permissions:', error);
    throw error;
  }
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
  const url = `${API_BASE_URL}/api/v1/permissions/`;
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
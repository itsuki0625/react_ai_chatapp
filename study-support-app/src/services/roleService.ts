import { RoleRead, RoleCreate, RoleUpdate } from '@/types/role';
import { apiClient } from '@/lib/api';

// GET /api/v1/roles
export const getRoles = async (params?: { skip?: number; limit?: number }): Promise<RoleRead[]> => {
  try {
    console.log('Fetching roles from API');
    const response = await apiClient.get('/api/v1/roles/', { params });
    console.log('Received roles:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch roles:', error);
    throw error;
  }
};

// POST /api/v1/roles
export const createRole = async (data: RoleCreate): Promise<RoleRead> => {
  try {
    console.log('Creating role with data:', data);
    const response = await apiClient.post('/api/v1/roles', data);
    console.log('Created role:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to create role:', error);
    throw error;
  }
};

// PUT /api/v1/roles/{role_id}
export const updateRole = async (id: string, data: RoleUpdate): Promise<RoleRead> => {
  try {
    console.log(`Updating role ${id} with data:`, data);
    const response = await apiClient.put(`/api/v1/roles/${id}`, data);
    console.log('Updated role:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to update role:', error);
    throw error;
  }
};

// DELETE /api/v1/roles/{role_id}
export const deleteRole = async (id: string): Promise<RoleRead> => {
  try {
    console.log(`Deleting role: ${id}`);
    const response = await apiClient.delete(`/api/v1/roles/${id}`);
    console.log('Deleted role:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to delete role:', error);
    throw error;
  }
};

// PUT /api/v1/roles/{role_id}/permissions
export const setRolePermissions = async ({ roleId, permissionIds }: { roleId: string; permissionIds: string[] }): Promise<RoleRead> => {
  try {
    console.log(`Setting permissions for role ${roleId}:`, permissionIds);
    const response = await apiClient.put(`/api/v1/roles/${roleId}/permissions`, { permission_ids: permissionIds });
    console.log('Set permissions, updated role:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to set role permissions:', error);
    throw error;
  }
};

// POST /api/v1/roles/{role_id}/permissions/{permission_id}
export const addPermissionToRole = async (roleId: string, permissionId: string): Promise<RoleRead> => {
  try {
    console.log(`Adding permission ${permissionId} to role ${roleId}`);
    const response = await apiClient.post(`/api/v1/roles/${roleId}/permissions/${permissionId}`);
    console.log('Added permission, updated role:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to add permission:', error);
    throw error;
  }
};

// DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
export const removePermissionFromRole = async (roleId: string, permissionId: string): Promise<RoleRead> => {
  try {
    console.log(`Removing permission ${permissionId} from role ${roleId}`);
    const response = await apiClient.delete(`/api/v1/roles/${roleId}/permissions/${permissionId}`);
    console.log('Removed permission, updated role:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to remove permission:', error);
    throw error;
  }
};
import { RoleRead, RoleCreate, RoleUpdate } from '@/types/role';

// Assume fetchWithAuth exists in lib for authenticated requests
// You might need to create this helper function
import { fetchWithAuth } from '@/lib/fetchWithAuth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050'; // Get from environment variables

// GET /api/v1/roles
export const getRoles = async (params?: { skip?: number; limit?: number }): Promise<RoleRead[]> => {
  const queryParams = new URLSearchParams(params as Record<string, string>).toString();
  const url = `${API_BASE_URL}/api/v1/roles${queryParams ? '?' + queryParams : ''}`;
  console.log(`Fetching roles from: ${url}`); // Log the URL
  const response = await fetchWithAuth(url);
  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch roles:', response.status, errorText);
    throw new Error(`Failed to fetch roles: ${response.statusText}`);
  }
  const data = await response.json();
  console.log('Received roles:', data);
  return data;
};

// POST /api/v1/roles
export const createRole = async (data: RoleCreate): Promise<RoleRead> => {
  const url = `${API_BASE_URL}/api/v1/roles`;
  console.log(`Creating role at: ${url} with data:`, data);
  const response = await fetchWithAuth(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
     const errorData = await response.json().catch(() => ({ detail: 'Failed to create role' }));
     console.error('Failed to create role:', response.status, errorData);
     throw new Error(errorData.detail || `Failed to create role: ${response.statusText}`);
  }
   const createdData = await response.json();
   console.log('Created role:', createdData);
  return createdData;
};

// PUT /api/v1/roles/{role_id}
export const updateRole = async (id: string, data: RoleUpdate): Promise<RoleRead> => {
  const url = `${API_BASE_URL}/api/v1/roles/${id}`;
  console.log(`Updating role at: ${url} with data:`, data);
  const response = await fetchWithAuth(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
   if (!response.ok) {
     const errorData = await response.json().catch(() => ({ detail: 'Failed to update role' }));
     console.error('Failed to update role:', response.status, errorData);
     throw new Error(errorData.detail || `Failed to update role: ${response.statusText}`);
   }
   const updatedData = await response.json();
   console.log('Updated role:', updatedData);
  return updatedData;
};

// DELETE /api/v1/roles/{role_id}
export const deleteRole = async (id: string): Promise<RoleRead> => {
  const url = `${API_BASE_URL}/api/v1/roles/${id}`;
  console.log(`Deleting role at: ${url}`);
  const response = await fetchWithAuth(url, {
    method: 'DELETE',
  });
   if (!response.ok) {
     const errorData = await response.json().catch(() => ({ detail: 'Failed to delete role' }));
     console.error('Failed to delete role:', response.status, errorData);
     throw new Error(errorData.detail || `Failed to delete role: ${response.statusText}`);
   }
   // Check if the backend returns the deleted object or just 2xx status
   if (response.status === 204) { // Handle No Content response
       console.log('Successfully deleted role (204 No Content).');
       // Since the object is deleted, we might return a confirmation or minimal data
       // Returning the ID might be useful for cache invalidation
       return { id } as RoleRead; // Cast needed as it's not the full object
   } else {
       const deletedData = await response.json();
       console.log('Deleted role (received object):', deletedData);
       return deletedData;
   }
};

// PUT /api/v1/roles/{role_id}/permissions
export const setRolePermissions = async ({ roleId, permissionIds }: { roleId: string; permissionIds: string[] }): Promise<RoleRead> => {
  const url = `${API_BASE_URL}/api/v1/roles/${roleId}/permissions`;
  console.log(`Setting permissions for role ${roleId} at: ${url} with IDs:`, permissionIds);
  const response = await fetchWithAuth(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ permission_ids: permissionIds }), // Match backend expectation
  });
   if (!response.ok) {
     const errorData = await response.json().catch(() => ({ detail: 'Failed to set role permissions' }));
     console.error('Failed to set permissions:', response.status, errorData);
     throw new Error(errorData.detail || `Failed to set role permissions: ${response.statusText}`);
   }
   const updatedRole = await response.json();
   console.log('Set permissions, updated role:', updatedRole);
  return updatedRole;
};

// --- Optional: Functions to add/remove single permission ---
// POST /api/v1/roles/{role_id}/permissions/{permission_id}
export const addPermissionToRole = async (roleId: string, permissionId: string): Promise<RoleRead> => {
    const url = `${API_BASE_URL}/api/v1/roles/${roleId}/permissions/${permissionId}`;
    console.log(`Adding permission ${permissionId} to role ${roleId} at: ${url}`);
    const response = await fetchWithAuth(url, {
        method: 'POST',
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to add permission' }));
        console.error('Failed to add permission:', response.status, errorData);
        throw new Error(errorData.detail || `Failed to add permission: ${response.statusText}`);
    }
    const updatedRole = await response.json();
    console.log('Added permission, updated role:', updatedRole);
    return updatedRole;
};

// DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
export const removePermissionFromRole = async (roleId: string, permissionId: string): Promise<RoleRead> => {
    const url = `${API_BASE_URL}/api/v1/roles/${roleId}/permissions/${permissionId}`;
    console.log(`Removing permission ${permissionId} from role ${roleId} at: ${url}`);
    const response = await fetchWithAuth(url, {
        method: 'DELETE',
    });
     if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to remove permission' }));
        console.error('Failed to remove permission:', response.status, errorData);
        throw new Error(errorData.detail || `Failed to remove permission: ${response.statusText}`);
     }
     if (response.status === 204) {
         console.log('Successfully removed permission (204 No Content).');
         // Need to decide what to return. Refetching might be the safest.
         // For now, return minimal info.
         return { id: roleId } as RoleRead;
     } else {
        const updatedRole = await response.json();
        console.log('Removed permission, updated role:', updatedRole);
        return updatedRole;
     }
}; 
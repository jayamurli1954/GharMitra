/**
 * Roles Service
 * Manages custom roles and role assignments
 */
import api from './api';

export interface CustomRole {
  id: string;
  role_name: string;
  role_code: string;
  description?: string;
  is_active: boolean;
  is_system_role: boolean;
  user_count?: number;
  created_at: string;
  updated_at: string;
}

export interface RoleCreate {
  role_name: string;
  role_code: string;
  description?: string;
}

export interface RoleUpdate {
  role_name?: string;
  role_code?: string;
  description?: string;
}

export const rolesService = {
  /**
   * Initialize default system roles for the society
   * Should be called during initial setup by admin
   */
  async initializeDefaultRoles(): Promise<{
    message: string;
    roles_created: number;
    roles: CustomRole[];
  }> {
    const response = await api.post('/roles/initialize');
    return response.data;
  },

  /**
   * List all roles for the society
   */
  async listRoles(): Promise<CustomRole[]> {
    const response = await api.get<CustomRole[]>('/roles');
    return response.data;
  },

  /**
   * Create a new custom role
   */
  async createRole(data: RoleCreate): Promise<CustomRole> {
    const response = await api.post<CustomRole>('/roles', data);
    return response.data;
  },

  /**
   * Update a role
   */
  async updateRole(roleId: string, data: RoleUpdate): Promise<CustomRole> {
    const response = await api.patch<CustomRole>(`/roles/${roleId}`, data);
    return response.data;
  },

  /**
   * Delete a custom role (cannot delete system roles)
   */
  async deleteRole(roleId: string): Promise<{message: string}> {
    const response = await api.delete(`/roles/${roleId}`);
    return response.data;
  },

  /**
   * Toggle role active status
   */
  async toggleRoleStatus(roleId: string): Promise<CustomRole> {
    const response = await api.patch<CustomRole>(`/roles/${roleId}/toggle`);
    return response.data;
  },
};


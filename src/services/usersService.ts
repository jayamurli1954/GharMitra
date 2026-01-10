/**
 * Users Service
 * Manages users and members
 */
import api from './api';
import {User} from './authService';

export interface Member {
  id: string;
  name: string;
  apartment_number: string;
  email: string;
  phone_number?: string;
  role: 'admin' | 'member';
  created_at: string;
}

export const usersService = {
  /**
   * Get all users (members)
   */
  async getUsers(params?: {role?: 'admin' | 'member'}): Promise<Member[]> {
    const response = await api.get<User[]>('/users', {params});
    return response.data.map(user => ({
      id: user.id,
      name: user.name,
      apartment_number: user.apartment_number,
      email: user.email,
      phone_number: user.phone_number,
      role: user.role,
      created_at: user.created_at,
    }));
  },

  /**
   * Get a specific user by ID
   */
  async getUser(userId: string): Promise<Member> {
    const response = await api.get<User>(`/users/${userId}`);
    const user = response.data;
    return {
      id: user.id,
      name: user.name,
      apartment_number: user.apartment_number,
      email: user.email,
      phone_number: user.phone_number,
      role: user.role,
      created_at: user.created_at,
    };
  },

  /**
   * Bulk import members from CSV/Excel file
   */
  async bulkImportMembers(formData: FormData): Promise<{
    total_rows: number;
    successful: number;
    failed: number;
    errors: string[];
    warnings?: string[];
    summary?: string;
  }> {
    const response = await api.post('/member-onboarding/bulk-import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};


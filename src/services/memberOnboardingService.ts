import api from './api';

export interface MemberCreate {
  flat_number: string;
  name: string;
  phone_number: string;
  email: string;
  member_type: 'owner' | 'tenant';
  move_in_date: string; // YYYY-MM-DD
  total_occupants?: number;
  is_primary?: boolean;
  occupation?: string; // Occupation: Employed, Business, Professional, etc.
  is_mobile_public?: boolean; // Is mobile number visible to other members?
}

export interface MemberBulkImportResponse {
  total_rows: number;
  successful: number;
  failed: number;
  errors: string[];
  warnings?: string[];
  summary?: string;
}

export interface Member {
  id: string;
  flat_id: string;
  flat_number: string;
  name: string;
  phone_number: string;
  email: string;
  member_type: string;
  status: string;
  move_in_date: string;
  move_out_date?: string | null;
  total_occupants: number;
  is_primary: boolean;
  clerk_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

class MemberOnboardingService {
  /**
   * Create a single member profile (admin only)
   */
  async createMember(memberData: MemberCreate): Promise<Member> {
    const response = await api.post<Member>('/member-onboarding/', memberData);
    return response.data;
  }

  /**
   * Bulk import members from CSV file (admin only)
   */
  async bulkImportMembers(file: any): Promise<MemberBulkImportResponse> {
    const formData = new FormData();
    formData.append('file', {
      uri: file.uri,
      type: file.type || 'text/csv',
      name: file.name || 'members.csv',
    } as any);

    const response = await api.post<MemberBulkImportResponse>(
      '/member-onboarding/bulk-import',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * List all members in the society (admin only)
   */
  async listMembers(statusFilter?: string, flatNumber?: string): Promise<Member[]> {
    const params: any = {};
    if (statusFilter) params.status_filter = statusFilter;
    if (flatNumber) params.flat_number = flatNumber;

    const response = await api.get<Member[]>('/member-onboarding/', { params });
    return response.data;
  }

  /**
   * Get current user's member profile
   */
  async getMyProfile(): Promise<Member> {
    const response = await api.get<Member>('/member-onboarding/my-profile');
    return response.data;
  }
}

export const memberOnboardingService = new MemberOnboardingService();


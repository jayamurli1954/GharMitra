/**
 * Member Onboarding Service for Web
 */
import api from './api';

class MemberOnboardingService {
  /**
   * Create a single member profile (admin only)
   */
  async createMember(memberData) {
    const response = await api.post('/member-onboarding/', memberData);
    return response.data;
  }

  /**
   * Bulk import members from CSV file (admin only)
   */
  async bulkImportMembers(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/member-onboarding/bulk-import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * List all members in the society
   */
  async listMembers(statusFilter, flatNumber) {
    const params = {};
    if (statusFilter) params.status_filter = statusFilter;
    if (flatNumber) params.flat_number = flatNumber;

    const response = await api.get('/member-onboarding/', { params });
    return response.data;
  }

  /**
   * Get current user's member profile
   */
  async getMyProfile() {
    const response = await api.get('/member-onboarding/my-profile');
    return response.data;
  }

  /**
   * Update member details (admin only)
   */
  async updateMember(memberId, memberData) {
    const response = await api.patch(`/member-onboarding/${memberId}`, memberData);
    return response.data;
  }
}

export const memberOnboardingService = new MemberOnboardingService();
export default memberOnboardingService;


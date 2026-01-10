import api from './api';

export interface AdminGuidelinesSection {
  id: string;
  title: string;
  icon: string;
  dos: string[];
  donts: string[];
  important?: string;
}

export interface AdminGuidelines {
  version: string;
  last_updated: string;
  title: string;
  sections: AdminGuidelinesSection[];
  acknowledgment_required: boolean;
  acknowledgment_message: string;
}

export interface AdminGuidelinesResponse {
  version: string;
  last_updated: string;
  content: AdminGuidelines;
  requires_acknowledgment: boolean;
}

export interface AdminAcknowledgmentRequest {
  version: string;
}

export interface AdminAcknowledgmentResponse {
  user_id: string;
  user_name: string;
  acknowledged: boolean;
  acknowledged_at: string | null;
  acknowledged_version: string | null;
}

class AdminGuidelinesService {
  /**
   * Get admin guidelines (Do's and Don'ts)
   */
  async getGuidelines(): Promise<AdminGuidelinesResponse> {
    const response = await api.get<AdminGuidelinesResponse>('/admin-guidelines/guidelines');
    return response.data;
  }

  /**
   * Check acknowledgment status for current admin
   */
  async getAcknowledgmentStatus(): Promise<AdminAcknowledgmentResponse> {
    const response = await api.get<AdminAcknowledgmentResponse>(
      '/admin-guidelines/guidelines/acknowledgment-status'
    );
    return response.data;
  }

  /**
   * Acknowledge that admin has read and understood the guidelines
   */
  async acknowledgeGuidelines(version: string): Promise<AdminAcknowledgmentResponse> {
    const response = await api.post<AdminAcknowledgmentResponse>(
      '/admin-guidelines/guidelines/acknowledge',
      { version }
    );
    return response.data;
  }

  /**
   * Get acknowledgment status for all admins in the society
   */
  async getAllAcknowledgments(): Promise<AdminAcknowledgmentResponse[]> {
    const response = await api.get<AdminAcknowledgmentResponse[]>(
      '/admin-guidelines/guidelines/all-acknowledgments'
    );
    return response.data;
  }
}

export const adminGuidelinesService = new AdminGuidelinesService();


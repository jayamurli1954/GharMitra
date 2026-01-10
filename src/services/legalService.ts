/**
 * Legal Documents Service
 * Fetches Terms of Service and Privacy Policy from backend
 */
import api from './api';

export interface LegalDocument {
  content: string;
  version: string;
  last_updated: string;
  document_type: 'terms_of_service' | 'privacy_policy';
}

export interface LegalVersion {
  version: string;
  last_updated: string;
  terms_file_exists: boolean;
  privacy_file_exists: boolean;
}

export const legalService = {
  /**
   * Get Terms of Service
   */
  async getTermsOfService(): Promise<LegalDocument> {
    const response = await api.get<LegalDocument>('/legal/terms');
    return response.data;
  },

  /**
   * Get Privacy Policy
   */
  async getPrivacyPolicy(): Promise<LegalDocument> {
    const response = await api.get<LegalDocument>('/legal/privacy');
    return response.data;
  },

  /**
   * Get current version of legal documents
   */
  async getLegalVersion(): Promise<LegalVersion> {
    const response = await api.get<LegalVersion>('/legal/version');
    return response.data;
  },
};







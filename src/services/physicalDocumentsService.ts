/**
 * Physical Documents Service
 * Handles API calls for physical documents checklist
 */
import api from './api';

export interface PhysicalDocument {
  id: string;
  society_id: number;
  member_id: number;
  flat_id: number;
  document_type: string;
  submitted: boolean;
  submission_date: string | null;
  verified: boolean;
  verified_by: number | null;
  verified_by_name: string | null;
  verification_date: string | null;
  storage_location: string | null;
  verification_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreatePhysicalDocumentRequest {
  member_id: string;
  document_type: string;
  storage_location?: string;
  verification_notes?: string;
}

export interface VerifyDocumentRequest {
  verification_notes?: string;
}

export interface UpdateDocumentRequest {
  storage_location?: string;
  verification_notes?: string;
}

class PhysicalDocumentsService {
  /**
   * Get all physical documents checklist for a member
   */
  async getPhysicalDocuments(memberId: string): Promise<PhysicalDocument[]> {
    const response = await api.get<PhysicalDocument[]>(
      `/physical-documents/${memberId}`
    );
    return response.data;
  }

  /**
   * Create a new physical document checklist entry
   */
  async createPhysicalDocument(
    data: CreatePhysicalDocumentRequest
  ): Promise<PhysicalDocument> {
    const response = await api.post<PhysicalDocument>(
      '/physical-documents',
      data
    );
    return response.data;
  }

  /**
   * Verify a physical document
   */
  async verifyPhysicalDocument(
    documentId: string,
    data?: VerifyDocumentRequest
  ): Promise<PhysicalDocument> {
    const response = await api.patch<PhysicalDocument>(
      `/physical-documents/${documentId}/verify`,
      data || {}
    );
    return response.data;
  }

  /**
   * Update a physical document
   */
  async updatePhysicalDocument(
    documentId: string,
    data: UpdateDocumentRequest
  ): Promise<PhysicalDocument> {
    const response = await api.patch<PhysicalDocument>(
      `/physical-documents/${documentId}`,
      data
    );
    return response.data;
  }

  /**
   * Delete a physical document checklist entry
   */
  async deletePhysicalDocument(documentId: string): Promise<void> {
    await api.delete(`/physical-documents/${documentId}`);
  }

  /**
   * Get summary statistics for a society
   */
  async getSocietyDocumentsSummary(societyId: string): Promise<any[]> {
    const response = await api.get(`/physical-documents/society/${societyId}/summary`);
    return response.data;
  }
}

export const physicalDocumentsService = new PhysicalDocumentsService();







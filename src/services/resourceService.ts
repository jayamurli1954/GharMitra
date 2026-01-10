/**
 * Resource Center Service
 * Manages resource files and NOC documents
 */
import api from './api';

export interface ResourceFile {
  id: string;
  society_id: number;
  file_name: string;
  description?: string;
  category?: string;
  file_url: string;
  file_size?: number;
  mime_type?: string;
  created_at: string;
  updated_at: string;
}

export interface NOCDocument {
  id: string;
  flat_id: number;
  member_id: number;
  noc_type: string;
  noc_number: string;
  file_url: string;
  qr_code_url?: string;
  generated_at: string;
  status: 'pending' | 'approved' | 'issued';
}

export interface NOCGenerateRequest {
  flat_id: number;
  member_id: number;
  move_out_date: string;
  move_in_date?: string;
  noc_type: 'society_move_out' | 'owner_tenant_move_in';
  new_owner_name?: string;
  new_tenant_name?: string;
  lease_start_date?: string;
  lease_duration_months?: number;
  tenant_family_members?: number;
}

export const resourceService = {
  async getResourceFiles(category?: string): Promise<ResourceFile[]> {
    const params = category ? { category } : {};
    const response = await api.get<ResourceFile[]>('/resources/files', { params });
    return response.data;
  },

  async uploadResourceFile(data: {
    file_name: string;
    description?: string;
    category?: string;
    file_url: string;
  }): Promise<ResourceFile> {
    const response = await api.post<ResourceFile>('/resources/files', data);
    return response.data;
  },

  async deleteResourceFile(fileId: string): Promise<void> {
    await api.delete(`/resources/files/${fileId}`);
  },

  async generateNOC(data: NOCGenerateRequest): Promise<NOCDocument> {
    const response = await api.post<NOCDocument>('/resources/noc/generate', data);
    return response.data;
  },

  async getNOCDocuments(flatId?: number, memberId?: number): Promise<NOCDocument[]> {
    const params: any = {};
    if (flatId) params.flat_id = flatId;
    if (memberId) params.member_id = memberId;
    const response = await api.get<NOCDocument[]>('/resources/noc', { params });
    return response.data;
  },

  async getNOCDocument(nocId: string): Promise<NOCDocument> {
    const response = await api.get<NOCDocument>(`/resources/noc/${nocId}`);
    return response.data;
  },

  async issueNOC(nocId: string): Promise<NOCDocument> {
    const response = await api.put<NOCDocument>(`/resources/noc/${nocId}/issue`);
    return response.data;
  },
};

// ============ TEMPLATE INTERFACES ============

export interface TemplateCategory {
  category_code: string;
  category_name: string;
  category_description?: string;
  icon_name?: string;
  template_count: number;
  display_order: number;
}

export interface Template {
  id: number;
  template_name: string;
  template_code: string;
  category: string;
  description?: string;
  instructions?: string;
  template_type: 'blank_download' | 'auto_fill';
  can_autofill: boolean;
  autofill_fields?: string[];
  icon_name?: string;
  available_to: string;
  display_order: number;
}

export interface TemplateDetails extends Template {
  template_variables?: string[];
}

export interface GenerateDocumentRequest {
  form_data: Record<string, string>;
}

export interface UsageStats {
  template_id: number;
  template_name: string;
  total_generated: number;
  last_generated?: string;
}

// ============ TEMPLATE SERVICE ============

export const templateService = {
  /**
   * Get all template categories with counts
   */
  async getCategories(): Promise<TemplateCategory[]> {
    const response = await api.get<TemplateCategory[]>('/templates/categories');
    return response.data;
  },

  /**
   * Get templates, optionally filtered by category/type
   */
  async getTemplates(params?: {
    category?: string;
    template_type?: 'blank_download' | 'auto_fill';
  }): Promise<Template[]> {
    const response = await api.get<Template[]>('/templates', { params });
    return response.data;
  },

  /**
   * Get single template details
   */
  async getTemplateDetails(templateId: number): Promise<TemplateDetails> {
    const response = await api.get<TemplateDetails>(`/templates/${templateId}`);
    return response.data;
  },

  /**
   * Download blank template (for blank_download type)
   */
  async downloadBlankTemplate(templateId: number): Promise<Blob> {
    const response = await api.get(`/templates/${templateId}/download-blank`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Generate document with auto-fill (NO STORAGE!)
   */
  async generateDocument(
    templateId: number,
    formData: Record<string, string>
  ): Promise<Blob> {
    const response = await api.post<Blob>(
      `/templates/${templateId}/generate`,
      { form_data: formData },
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  /**
   * Get usage statistics (admin only)
   */
  async getUsageStats(): Promise<UsageStats[]> {
    const response = await api.get<UsageStats[]>('/templates/admin/usage-stats');
    return response.data;
  },
};





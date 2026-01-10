/**
 * Society Service
 * Handles society registration and management
 */
import api from './api';

export interface SocietyRegistrationData {
  // Admin details
  admin_name: string;
  admin_email: string;
  admin_phone?: string;
  admin_password: string;
  
  // Society details
  society_name: string;
  society_address?: string;
  registration_no?: string;
  pan_no?: string;
  
  // Optional document URLs (uploaded to Cloudinary first)
  reg_cert_url?: string;
  pan_card_url?: string;
}

export interface Society {
  id: string;
  name: string;
  address?: string;
  registration_no?: string;
  pan_no?: string;
  reg_cert_url?: string;
  pan_card_url?: string;
  logo_url?: string; // Society logo URL (optional, for branding in reports)
  total_flats: number;
  financial_year_start?: string;
  financial_year_end?: string;
  accounting_type: 'cash' | 'accrual';
  // Address details
  address_line?: string;
  pin_code?: string;
  city?: string;
  state?: string;
  // Contact information
  email?: string;
  landline?: string;
  mobile?: string;
  // GST registration
  gst_registration_applicable?: boolean;
  created_at: string;
  updated_at: string;
}

export interface SocietyUpdate {
  financial_year_start?: string;
  financial_year_end?: string;
  accounting_type?: 'cash' | 'accrual';
  logo_url?: string; // Society logo URL (optional)
  // Address details
  address_line?: string;
  pin_code?: string;
  city?: string;
  state?: string;
  // Contact information
  email?: string;
  landline?: string;
  mobile?: string;
  // GST registration
  gst_registration_applicable?: boolean;
}

export interface PincodeLookup {
  pincode: string;
  city: string | null;
  state: string | null;
  found: boolean;
  message?: string;
}

export const societyService = {
  async registerSociety(data: SocietyRegistrationData): Promise<{
    access_token: string;
    token_type: string;
    user: any;
  }> {
    const response = await api.post('/society/register', data);
    return response.data;
  },

  async getSociety(societyId: string): Promise<Society> {
    const response = await api.get<Society>(`/society/${societyId}`);
    return response.data;
  },

  async updateSocietySettings(data: SocietyUpdate): Promise<Society> {
    const response = await api.patch<Society>('/society/settings', data);
    return response.data;
  },

  async lookupPincode(pincode: string): Promise<PincodeLookup> {
    const response = await api.get<PincodeLookup>(`/pincode/lookup?pincode=${pincode}`);
    return response.data;
  },

  async getStates(): Promise<{states: string[]}> {
    const response = await api.get<{states: string[]}>('/pincode/states');
    return response.data;
  },
};



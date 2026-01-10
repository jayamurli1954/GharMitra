/**
 * Settings Service
 * Manages society configuration settings
 */
import api from './api';

export interface SocietySettings {
  id: string;
  society_id: number;
  
  // Penalty/Interest
  late_payment_penalty_type?: string;
  late_payment_penalty_value?: number;
  late_payment_grace_days?: number;
  interest_on_overdue: boolean;
  interest_rate?: number;
  
  // Tax
  gst_enabled: boolean;
  gst_number?: string;
  gst_rate?: number;
  tds_enabled: boolean;
  tds_rate?: number;
  tds_threshold?: number;
  
  // Payment Gateway
  payment_gateway_enabled: boolean;
  payment_gateway_provider?: string;
  payment_gateway_key_id?: string;
  payment_gateway_key_secret?: string;
  upi_enabled: boolean;
  upi_id?: string;
  
  // Bank Accounts
  bank_accounts?: Array<{
    account_name: string;
    account_number: string;
    bank_name: string;
    ifsc_code: string;
    branch?: string;
    account_type?: string;
    is_primary: boolean;
  }>;
  
  // Vendor
  vendor_approval_required: boolean;
  vendor_approval_workflow?: string;
  
  // Audit Trail
  audit_trail_enabled: boolean;
  audit_retention_days?: number;
  
  // Billing
  billing_cycle?: string;
  auto_generate_bills: boolean;
  bill_due_days?: number;
  
  // Member
  bill_to_bill_tracking: boolean;
  
  created_at: string;
  updated_at: string;
}

export interface SocietySettingsUpdate {
  // Penalty/Interest
  late_payment_penalty_type?: string;
  late_payment_penalty_value?: number;
  late_payment_grace_days?: number;
  interest_on_overdue?: boolean;
  interest_rate?: number;
  
  // Tax
  gst_enabled?: boolean;
  gst_number?: string;
  gst_rate?: number;
  tds_enabled?: boolean;
  tds_rate?: number;
  tds_threshold?: number;
  
  // Payment Gateway
  payment_gateway_enabled?: boolean;
  payment_gateway_provider?: string;
  payment_gateway_key_id?: string;
  payment_gateway_key_secret?: string;
  upi_enabled?: boolean;
  upi_id?: string;
  
  // Bank Accounts
  bank_accounts?: Array<{
    account_name: string;
    account_number: string;
    bank_name: string;
    ifsc_code: string;
    branch?: string;
    account_type?: string;
    is_primary: boolean;
  }>;
  
  // Vendor
  vendor_approval_required?: boolean;
  vendor_approval_workflow?: string;
  
  // Audit Trail
  audit_trail_enabled?: boolean;
  audit_retention_days?: number;
  
  // Billing
  billing_cycle?: string;
  auto_generate_bills?: boolean;
  bill_due_days?: number;
  
  // Member
  bill_to_bill_tracking?: boolean;
}

export const settingsService = {
  async getSocietySettings(): Promise<SocietySettings> {
    const response = await api.get<SocietySettings>('/settings/society');
    return response.data;
  },

  async updateSocietySettings(data: SocietySettingsUpdate): Promise<SocietySettings> {
    const response = await api.patch<SocietySettings>('/settings/society', data);
    return response.data;
  },
};


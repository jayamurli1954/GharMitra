/**
 * Maintenance Billing Service
 * Handles maintenance bill generation and management
 */
import api from './api';

export interface ApartmentSettings {
  id: string;
  apartment_name: string;
  total_flats: number;
  calculation_method: 'sqft_rate' | 'variable';
  sqft_rate?: number;
  sinking_fund_total?: number;
  created_at: string;
  updated_at: string;
}

export interface ApartmentSettingsCreate {
  apartment_name: string;
  total_flats: number;
  calculation_method: 'sqft_rate' | 'variable';
  sqft_rate?: number;
  sinking_fund_total?: number;
}

export interface FixedExpense {
  id: string;
  name: string;
  amount: number;
  frequency: 'monthly' | 'quarterly' | 'annual';
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface FixedExpenseCreate {
  name: string;
  amount: number;
  frequency: 'monthly' | 'quarterly' | 'annual';
  description?: string;
}

export interface WaterExpense {
  id: string;
  month: number;
  year: number;
  tanker_charges: number;
  government_charges: number;
  other_charges: number;
  total_water_expense: number;
  created_at: string;
}

export interface WaterExpenseCreate {
  month: number;
  year: number;
  tanker_charges: number;
  government_charges: number;
  other_charges: number;
}

export interface BillBreakdown {
  water_charges?: number;
  per_person_water_charge?: number;
  fixed_expenses?: number;
  sinking_fund?: number;
  sqft_calculation?: string;
}

export interface MaintenanceBill {
  id: string;
  flat_id: string;
  flat_number: string;
  month: number;
  year: number;
  amount: number;
  breakdown: BillBreakdown;
  status: 'unpaid' | 'paid';
  created_at: string;
  paid_at?: string;
}

export interface BillGenerationResponse {
  total_bills_generated: number;
  total_amount: number;
  month: number;
  year: number;
  bills: MaintenanceBill[];
}

import {Linking} from 'react-native';
import ENV from '../config/env';

export const maintenanceService = {
  // ===== Apartment Settings =====
  async getSettings(): Promise<ApartmentSettings | null> {
    try {
      const response = await api.get<ApartmentSettings>('/maintenance/settings');
      return response.data;
    } catch (error: any) {
      // 404 means settings don't exist yet - that's okay
      if (error.response?.status === 404) {
        return null;
      }
      // Re-throw other errors
      throw error;
    }
  },

  async createOrUpdateSettings(data: ApartmentSettingsCreate): Promise<ApartmentSettings> {
    const response = await api.post<ApartmentSettings>('/maintenance/settings', data);
    return response.data;
  },

  // ===== Fixed Expenses =====
  async getFixedExpenses(): Promise<FixedExpense[]> {
    const response = await api.get<FixedExpense[]>('/maintenance/fixed-expenses');
    return response.data;
  },

  async createFixedExpense(data: FixedExpenseCreate): Promise<FixedExpense> {
    const response = await api.post<FixedExpense>('/maintenance/fixed-expenses', data);
    return response.data;
  },

  async deleteFixedExpense(expenseId: string): Promise<void> {
    await api.delete(`/maintenance/fixed-expenses/${expenseId}`);
  },

  // ===== Water Expenses =====
  async getWaterExpenses(month?: number, year?: number): Promise<WaterExpense[]> {
    const params: any = {};
    if (month) params.month = month;
    if (year) params.year = year;

    const response = await api.get<WaterExpense[]>('/maintenance/water-expenses', { params });
    return response.data;
  },

  async createWaterExpense(data: WaterExpenseCreate): Promise<WaterExpense> {
    const response = await api.post<WaterExpense>('/maintenance/water-expenses', data);
    return response.data;
  },

  // ===== Bill Generation =====
  async getAllowedBillMonth(): Promise<{
    allowed_month: number;
    allowed_year: number;
    current_month: number;
    current_year: number;
    already_generated: boolean;
    month_name: string;
    formatted: string;
  }> {
    const response = await api.get('/maintenance/allowed-bill-month');
    return response.data;
  },

  async generateBills(month: number, year: number): Promise<BillGenerationResponse> {
    const response = await api.post<BillGenerationResponse>('/maintenance/generate-bills', {
      month,
      year,
    });
    return response.data;
  },

  async getBills(params?: {
    month?: number;
    year?: number;
    flat_id?: string;
    status?: string;
  }): Promise<MaintenanceBill[]> {
    const response = await api.get<MaintenanceBill[]>('/maintenance/bills', { params });
    return response.data;
  },

  async markBillPaid(billId: string): Promise<MaintenanceBill> {
    const response = await api.patch<MaintenanceBill>(`/maintenance/bills/${billId}/mark-paid`);
    return response.data;
  },

  async deleteBillsForMonth(month: number, year: number): Promise<void> {
    await api.delete(`/maintenance/bills/${month}/${year}`);
  },

  /**
   * Download bill PDF
   * @param billId Bill ID
   */
  async downloadBillPDF(billId: string): Promise<void> {
    const baseURL = api.defaults.baseURL || ENV.API_URL || 'http://localhost:8000';
    const url = `${baseURL}/maintenance/bills/${billId}/download-pdf`;
    await Linking.openURL(url);
  },
};

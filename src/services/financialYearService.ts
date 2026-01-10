/**
 * Financial Year Service
 * Handles three-stage closing workflow:
 * OPEN → PROVISIONAL_CLOSE → FINAL_CLOSE
 */
import api from './api';

export interface FinancialYear {
  id: string;
  society_id: string;
  year_name: string;
  start_date: string;
  end_date: string;
  status: 'open' | 'provisional_close' | 'final_close';
  is_active: boolean;
  is_closed: boolean;
  provisional_close_date?: string;
  provisional_closed_by?: string;
  final_close_date?: string;
  final_closed_by?: string;
  audit_start_date?: string;
  audit_end_date?: string;
  auditor_name?: string;
  auditor_firm?: string;
  audit_report_date?: string;
  audit_report_file_url?: string;
  opening_balances_status: 'provisional' | 'finalized';
  closing_bank_balance?: number;
  closing_cash_balance?: number;
  total_income?: number;
  total_expenses?: number;
  net_surplus_deficit?: number;
  closing_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface OpeningBalance {
  id: string;
  society_id: string;
  financial_year_id: string;
  account_head_id: string;
  account_name: string;
  opening_balance: number;
  balance_type: 'debit' | 'credit';
  status: 'provisional' | 'finalized';
  calculated_from_previous_year: boolean;
  manual_entry: boolean;
  manual_entry_reason?: string;
  created_at: string;
  created_by?: string;
  finalized_at?: string;
  finalized_by?: string;
}

export interface ProvisionalClosingRequest {
  closing_date: string;
  notes?: string;
}

export interface FinalClosingRequest {
  audit_completion_date: string;
  auditor_name: string;
  auditor_firm: string;
  audit_report_file_url: string;
  final_statements_approved: boolean;
  committee_approval_date?: string;
  notes?: string;
}

export interface JournalEntryItem {
  account_head_id: string;
  account_name: string;
  entry_type: 'debit' | 'credit';
  amount: number;
  description?: string;
}

export interface AuditAdjustmentRequest {
  effective_date: string;
  adjustment_type: string;
  description: string;
  reason: string;
  auditor_reference?: string;
  entries: JournalEntryItem[];
}

export interface YearEndClosingSummary {
  financial_year_id: string;
  year_name: string;
  closing_date: string;
  bank_balance: number;
  cash_balance: number;
  total_income: number;
  total_expenses: number;
  net_surplus_deficit: number;
  opening_balances_created: boolean;
  next_year_activated: boolean;
  message: string;
}

export interface AuditAdjustmentResponse {
  success: boolean;
  message: string;
  adjustment_id: string;
  adjustment_number: string;
  entry_number: string;
  effective_date: string;
  amount: number;
  financial_year: string;
  note: string;
  affected_accounts: Array<{
    account_name: string;
    adjustment: number;
    type: string;
  }>;
}

export interface OpeningBalanceListResponse {
  financial_year_id: string;
  financial_year_name: string;
  opening_balances_status: string;
  balances: OpeningBalance[];
  summary: {
    total_accounts: number;
    total_debit: number;
    total_credit: number;
    difference: number;
    is_balanced: boolean;
    provisional_count: number;
    finalized_count: number;
    all_finalized: boolean;
  };
}

class FinancialYearService {
  /**
   * Get all financial years
   */
  async getFinancialYears(): Promise<FinancialYear[]> {
    const response = await api.get<FinancialYear[]>('/financial-years');
    return response.data;
  }

  /**
   * Get active financial year
   */
  async getActiveFinancialYear(): Promise<FinancialYear> {
    const response = await api.get<FinancialYear>('/financial-years/active');
    return response.data;
  }

  /**
   * Get specific financial year
   */
  async getFinancialYear(yearId: string): Promise<FinancialYear> {
    const response = await api.get<FinancialYear>(`/financial-years/${yearId}`);
    return response.data;
  }

  /**
   * Create new financial year
   */
  async createFinancialYear(data: {
    year_name: string;
    start_date: string;
    end_date: string;
  }): Promise<FinancialYear> {
    const response = await api.post<FinancialYear>('/financial-years', data);
    return response.data;
  }

  /**
   * STAGE 1: Provisional Close
   * Lock year for audit while allowing adjustments
   */
  async provisionalCloseYear(
    yearId: string,
    data: ProvisionalClosingRequest,
  ): Promise<YearEndClosingSummary> {
    const response = await api.post<YearEndClosingSummary>(
      `/financial-years/${yearId}/provisional-close`,
      data,
    );
    return response.data;
  }

  /**
   * STAGE 2: Post Adjustment Entry
   * Post audit adjustments to provisionally closed year
   */
  async postAdjustmentEntry(
    yearId: string,
    data: AuditAdjustmentRequest,
  ): Promise<AuditAdjustmentResponse> {
    const response = await api.post<AuditAdjustmentResponse>(
      `/financial-years/${yearId}/adjustment-entry`,
      data,
    );
    return response.data;
  }

  /**
   * STAGE 3: Final Close
   * Permanently lock year after audit completion
   */
  async finalCloseYear(
    yearId: string,
    data: FinalClosingRequest,
  ): Promise<any> {
    const response = await api.post(`/financial-years/${yearId}/final-close`, data);
    return response.data;
  }

  /**
   * Get opening balances for a year
   */
  async getOpeningBalances(yearId: string): Promise<OpeningBalanceListResponse> {
    const response = await api.get<OpeningBalanceListResponse>(
      `/opening-balances/year/${yearId}`,
    );
    return response.data;
  }

  /**
   * Create manual opening balance
   */
  async createManualOpeningBalance(data: {
    financial_year_id: string;
    account_head_id: string;
    account_name: string;
    opening_balance: number;
    balance_type: 'debit' | 'credit';
    manual_entry_reason: string;
  }): Promise<OpeningBalance> {
    const response = await api.post<OpeningBalance>('/opening-balances', data);
    return response.data;
  }
}

export const financialYearService = new FinancialYearService();

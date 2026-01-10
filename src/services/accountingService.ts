/**
 * Accounting Service
 * Manages chart of accounts
 */
import api from './api';

export interface AccountCode {
  id: string;
  code: string;
  name: string;
  type: 'asset' | 'liability' | 'capital' | 'income' | 'expense';
  description?: string;
  opening_balance: number;
  current_balance: number;
  is_fixed_expense?: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChartAccountSuggestion {
  name: string;
  description: string;
  category: string;
  sub_category?: string;
  suggested_code?: string;
}

export const accountingService = {
  async searchChartOfAccounts(
    query: string,
    accountType?: string
  ): Promise<ChartAccountSuggestion[]> {
    if (query.length < 3) {
      return [];
    }
    const params: any = { query };
    if (accountType) {
      params.account_type = accountType;
    }
    const response = await api.get<ChartAccountSuggestion[]>(
      '/chart-of-accounts/search',
      { params }
    );
    return response.data;
  },

  async initializeChartOfAccounts(): Promise<{
    message: string;
    accounts_created: number;
  }> {
    const response = await api.post('/accounting/initialize-chart-of-accounts');
    return response.data;
  },

  async getAccountCodes(type?: string): Promise<AccountCode[]> {
    const params = type ? { type } : {};
    const response = await api.get<any[]>('/accounting/accounts', { params });
    
    // Map _id to id and ensure type is a string
    return response.data.map((account: any) => ({
      ...account,
      id: account.id || account._id || String(account._id),
      type: account.type?.value || account.type || String(account.type),
      is_fixed_expense: account.is_fixed_expense || false,
    }));
  },

  async updateOpeningBalance(
    code: string,
    openingBalance: number
  ): Promise<AccountCode> {
    const response = await api.patch<any>(
      `/accounting/accounts/${code}/opening-balance`,
      { opening_balance: openingBalance }
    );
    return {
      ...response.data,
      id: response.data.id || response.data._id || String(response.data._id),
      type: response.data.type?.value || response.data.type || String(response.data.type),
    };
  },

  async getAccountCode(code: string): Promise<AccountCode> {
    const response = await api.get<any>(`/accounting/accounts/${code}`);
    // Map _id to id and ensure type is a string
    return {
      ...response.data,
      id: response.data.id || response.data._id || String(response.data._id),
      type: response.data.type?.value || response.data.type || String(response.data.type),
      is_fixed_expense: response.data.is_fixed_expense || false,
    };
  },

  async createAccountCode(data: {
    code: string;
    name: string;
    type: 'asset' | 'liability' | 'capital' | 'income' | 'expense';
    description?: string;
    opening_balance?: number;
  }): Promise<AccountCode> {
    const response = await api.post<any>('/accounting/accounts', data);
    // Map _id to id and ensure type is a string
    return {
      ...response.data,
      id: response.data.id || response.data._id || String(response.data._id),
      type: response.data.type?.value || response.data.type || String(response.data.type),
    };
  },

  async deleteAccountCode(code: string): Promise<void> {
    await api.delete(`/accounting/accounts/${code}`);
  },

  async deleteAllAccountCodes(): Promise<{
    message: string;
    deleted_count: number;
  }> {
    const response = await api.delete<{
      message: string;
      deleted_count: number;
    }>('/accounting/accounts');
    return response.data;
  },

  async toggleFixedExpense(
    code: string,
    isFixedExpense: boolean
  ): Promise<AccountCode> {
    const response = await api.patch<any>(
      `/accounting/accounts/${code}/fixed-expense`,
      { is_fixed_expense: isFixedExpense }
    );
    return {
      ...response.data,
      id: response.data.id || response.data._id || String(response.data._id),
      type: response.data.type?.value || response.data.type || String(response.data.type),
    };
  },

  async validateBalanceSheet(): Promise<{
    total_assets: number;
    total_liabilities: number;
    total_equity: number;
    difference: number;
    is_balanced: boolean;
    equity_account_code?: string;
    equity_account_name?: string;
    message: string;
  }> {
    const response = await api.get('/accounting/validate-balance-sheet');
    return response.data;
  },

  /**
   * Create Journal Entry
   */
  async createJournalEntry(data: {
    date?: string;
    description: string;
    entries: Array<{
      account_code: string;
      debit_amount: number;
      credit_amount: number;
      description?: string;
    }>;
  }): Promise<any> {
    const response = await api.post('/journal', data);
    return response.data;
  },

  /**
   * Get Journal Entries
   */
  async getJournalEntries(params?: {
    from_date?: string;
    to_date?: string;
  }): Promise<any[]> {
    const response = await api.get('/journal', {params});
    return response.data;
  },

  /**
   * Get Single Journal Entry
   */
  async getJournalEntry(entryId: string): Promise<any> {
    const response = await api.get(`/journal/${entryId}`);
    return response.data;
  },
};

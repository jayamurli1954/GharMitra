/**
 * Transactions Service
 * Manages financial transactions (income/expenses)
 */
import api from './api';

export interface Transaction {
  id: string;
  document_number?: string; // Auto-generated document number (TXN-YYYYMMDD-001)
  type: 'income' | 'expense';
  category: string;
  account_code?: string;
  amount: number;
  description: string;
  date: string;
  expense_month?: string; // Period allocation (e.g. "December, 2025")
  added_by: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionCreate {
  type: 'income' | 'expense';
  category: string;
  account_code?: string;
  amount: number;
  description: string;
  date?: string; // ISO date string (YYYY-MM-DD)
  expense_month?: string; // Optional period tag (e.g. "December, 2025")
}

export interface TransactionUpdate {
  type?: 'income' | 'expense';
  category?: string;
  account_code?: string;
  amount?: number;
  description?: string;
  date?: string;
  expense_month?: string;
}

export interface TransactionSummary {
  total_income: number;
  total_expense: number;
  income_count: number;
  expense_count: number;
  net_balance: number;
}

export const transactionsService = {
  /**
   * Get all transactions with optional filters
   */
  async getTransactions(params?: {
    type?: 'income' | 'expense';
    from_date?: string;
    to_date?: string;
    account_code?: string;
    category?: string;
    limit?: number;
  }): Promise<Transaction[]> {
    const response = await api.get<Transaction[]>('/transactions', { params });
    return response.data;
  },

  /**
   * Create a new transaction
   */
  async createTransaction(data: TransactionCreate): Promise<Transaction> {
    const response = await api.post<Transaction>('/transactions', data);
    return response.data;
  },

  /**
   * Get a specific transaction by ID
   */
  async getTransaction(transactionId: string): Promise<Transaction> {
    const response = await api.get<Transaction>(`/transactions/${transactionId}`);
    return response.data;
  },

  /**
   * Update a transaction
   */
  async updateTransaction(
    transactionId: string,
    data: TransactionUpdate
  ): Promise<Transaction> {
    const response = await api.put<Transaction>(`/transactions/${transactionId}`, data);
    return response.data;
  },

  /**
   * Delete a transaction
   */
  async deleteTransaction(transactionId: string): Promise<void> {
    await api.delete(`/transactions/${transactionId}`);
  },

  /**
   * Get transaction summary statistics
   */
  async getTransactionSummary(params?: {
    from_date?: string;
    to_date?: string;
  }): Promise<TransactionSummary> {
    const response = await api.get<TransactionSummary>('/transactions/statistics/summary', {
      params,
    });
    return response.data;
  },

  /**
   * Get list of categories
   */
  async getCategories(type?: 'income' | 'expense'): Promise<string[]> {
    const params = type ? { type } : {};
    const response = await api.get<{ categories: string[] }>('/transactions/categories/list', {
      params,
    });
    return response.data.categories;
  },
};

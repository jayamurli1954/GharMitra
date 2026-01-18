/**
 * Accounting Service
 * Handles chart of accounts and accounting operations
 */
import api from './api';

const BASE_URL = '/accounting';

export const accountingService = {
  /**
   * Get all account codes
   */
  async getAccounts(type = null) {
    const url = type ? `${BASE_URL}/accounts?type=${type}` : `${BASE_URL}/accounts`;
    const response = await api.get(url);
    return response.data;
  },

  /**
   * Get a specific account by code
   */
  async getAccount(code) {
    const response = await api.get(`${BASE_URL}/accounts/${code}`);
    return response.data;
  },

  /**
   * Create a new account
   */
  async createAccount(accountData) {
    const response = await api.post(`${BASE_URL}/accounts`, accountData);
    return response.data;
  },

  /**
   * Update an account (name, description, etc.) - code cannot be changed
   */
  async updateAccount(code, updateData) {
    const response = await api.patch(`${BASE_URL}/accounts/${code}`, updateData);
    return response.data;
  },

  /**
   * Delete an account
   */
  async deleteAccount(code) {
    await api.delete(`${BASE_URL}/accounts/${code}`);
  },

  /**
   * Initialize chart of accounts from predefined list
   */
  async initializeChartOfAccounts() {
    const response = await api.post(`${BASE_URL}/initialize-chart-of-accounts`);
    return response.data;
  },

  /**
   * Update opening balance for an account
   */
  async updateOpeningBalance(code, openingBalance) {
    const response = await api.patch(`${BASE_URL}/accounts/${code}/opening-balance`, {
      opening_balance: openingBalance
    });
    return response.data;
  },

  /**
   * Validate balance sheet
   */
  async validateBalanceSheet() {
    const response = await api.get(`${BASE_URL}/validate-balance-sheet`);
    return response.data;
  },

  /**
   * Delete all account codes (admin only)
   */
  async deleteAccounts() {
    const response = await api.delete(`${BASE_URL}/accounts`);
    return response.data;
  }
};

export default accountingService;


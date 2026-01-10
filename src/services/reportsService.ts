/**
 * Reports Service
 * Generates financial reports
 */
import api from './api';
import {Linking} from 'react-native';

export const reportsService = {
  async getReceiptsAndPaymentsReport(from_date: string, to_date: string): Promise<any> {
    const response = await api.get('/reports/receipts-and-payments', {
      params: { from_date, to_date },
    });
    return response.data;
  },

  async getIncomeAndExpenditureReport(from_date: string, to_date: string): Promise<any> {
    const response = await api.get('/reports/income-and-expenditure', {
      params: { from_date, to_date },
    });
    return response.data;
  },

  async getBalanceSheet(as_on_date: string): Promise<any> {
    const response = await api.get('/reports/balance-sheet', {
      params: { as_on_date },
    });
    return response.data;
  },

  async getMemberDuesReport(): Promise<any> {
    const response = await api.get('/reports/member-dues');
    return response.data;
  },

  async getMemberLedger(
    flatId: string,
    from_date?: string,
    to_date?: string
  ): Promise<any> {
    const params: any = {};
    if (from_date) params.from_date = from_date;
    if (to_date) params.to_date = to_date;

    const response = await api.get(`/reports/member-ledger/${flatId}`, { params });
    return response.data;
  },

  async getTrialBalance(as_on_date: string): Promise<any> {
    const response = await api.get('/reports/trial-balance', {
      params: { as_on_date },
    });
    return response.data;
  },

  async getCashBookLedger(from_date: string, to_date: string): Promise<any> {
    const response = await api.get('/reports/cash-book', {
      params: { from_date, to_date },
    });
    return response.data;
  },

  async getBankLedger(
    from_date: string,
    to_date: string,
    account_code?: string
  ): Promise<any> {
    const params: any = { from_date, to_date };
    if (account_code) params.account_code = account_code;

    const response = await api.get('/reports/bank-ledger', { params });
    return response.data;
  },

  async getGeneralLedgerReport(from_date: string, to_date: string): Promise<any> {
    const response = await api.get('/reports/general-ledger', {
      params: { from_date, to_date },
    });
    return response.data;
  },

  /**
   * Export General Ledger Report
   * @param from_date Start date (YYYY-MM-DD)
   * @param to_date End date (YYYY-MM-DD)
   * @param format Export format ('excel' or 'pdf')
   */
  async exportGeneralLedger(
    from_date: string,
    to_date: string,
    format: 'excel' | 'pdf'
  ): Promise<void> {
    const endpoint = format === 'excel' 
      ? '/reports/general-ledger/export/excel'
      : '/reports/general-ledger/export/pdf';
    
    // Get base URL from API config
    const baseURL = api.defaults.baseURL || 'http://localhost:8000';
    const token = await api.defaults.headers?.common?.Authorization;
    
    // Construct full URL with params
    const url = `${baseURL}${endpoint}?from_date=${from_date}&to_date=${to_date}`;
    
    // Open in browser for download (works on mobile)
    await Linking.openURL(url);
  },

  /**
   * Export Receipts & Payments Report
   * @param from_date Start date (YYYY-MM-DD)
   * @param to_date End date (YYYY-MM-DD)
   * @param format Export format ('excel' or 'pdf')
   */
  async exportReceiptsPayments(
    from_date: string,
    to_date: string,
    format: 'excel' | 'pdf'
  ): Promise<void> {
    const endpoint = format === 'excel' 
      ? '/reports/receipts-and-payments/export/excel'
      : '/reports/receipts-and-payments/export/pdf';
    
    const baseURL = api.defaults.baseURL || 'http://localhost:8000';
    const url = `${baseURL}${endpoint}?from_date=${from_date}&to_date=${to_date}`;
    
    await Linking.openURL(url);
  },

  /**
   * Export Cash Book Ledger
   * @param from_date Start date (YYYY-MM-DD)
   * @param to_date End date (YYYY-MM-DD)
   * @param format Export format ('excel' or 'pdf')
   */
  async exportCashBook(
    from_date: string,
    to_date: string,
    format: 'excel' | 'pdf'
  ): Promise<void> {
    const endpoint = format === 'excel' 
      ? '/reports/cash-book/export/excel'
      : '/reports/cash-book/export/pdf';
    
    const baseURL = api.defaults.baseURL || 'http://localhost:8000';
    const url = `${baseURL}${endpoint}?from_date=${from_date}&to_date=${to_date}`;
    
    await Linking.openURL(url);
  },

  /**
   * Export Bank Ledger
   * @param from_date Start date (YYYY-MM-DD)
   * @param to_date End date (YYYY-MM-DD)
   * @param format Export format ('excel' or 'pdf')
   */
  async exportBankLedger(
    from_date: string,
    to_date: string,
    format: 'excel' | 'pdf'
  ): Promise<void> {
    const endpoint = format === 'excel' 
      ? '/reports/bank-ledger/export/excel'
      : '/reports/bank-ledger/export/pdf';
    
    const baseURL = api.defaults.baseURL || 'http://localhost:8000';
    const url = `${baseURL}${endpoint}?from_date=${from_date}&to_date=${to_date}`;
    
    await Linking.openURL(url);
  },

  /**
   * Get Member Transaction Ledger
   * @param flat_id Flat ID
   * @param from_date Start date (YYYY-MM-DD) - optional
   * @param to_date End date (YYYY-MM-DD) - optional
   */
  async getMemberLedger(
    flat_id: string,
    from_date?: string,
    to_date?: string
  ): Promise<any> {
    const params: any = {};
    if (from_date) params.from_date = from_date;
    if (to_date) params.to_date = to_date;
    
    const response = await api.get(`/reports/member-ledger/${flat_id}`, {params});
    return response.data;
  },

  /**
   * Export Member Transaction Ledger
   * @param flat_id Flat ID
   * @param from_date Start date (YYYY-MM-DD) - optional
   * @param to_date End date (YYYY-MM-DD) - optional
   * @param format Export format ('excel' or 'pdf')
   */
  async exportMemberLedger(
    flat_id: string,
    from_date: string,
    to_date: string,
    format: 'excel' | 'pdf'
  ): Promise<void> {
    const endpoint = format === 'excel' 
      ? `/reports/member-ledger/${flat_id}/export/excel`
      : `/reports/member-ledger/${flat_id}/export/pdf`;
    
    const baseURL = api.defaults.baseURL || 'http://localhost:8000';
    let url = `${baseURL}${endpoint}`;
    
    const params = [];
    if (from_date) params.push(`from_date=${from_date}`);
    if (to_date) params.push(`to_date=${to_date}`);
    if (params.length > 0) {
      url += `?${params.join('&')}`;
    }
    
    await Linking.openURL(url);
  },

  /**
   * Generic export function for other reports
   * @param reportType Type of report
   * @param params Query parameters
   * @param format Export format ('excel' or 'pdf')
   */
  async exportReport(
    reportType: string,
    params: Record<string, string>,
    format: 'excel' | 'pdf'
  ): Promise<void> {
    const endpoint = `/reports/${reportType}/export/${format}`;
    const baseURL = api.defaults.baseURL || 'http://localhost:8000';
    
    // Build query string
    const queryString = new URLSearchParams(params).toString();
    const url = `${baseURL}${endpoint}?${queryString}`;
    
    await Linking.openURL(url);
  },
};

/**
 * Payment Service
 * Handles payment collection, receipts, reconciliation, and reminders
 */
import api from './api';

export interface PaymentRecordRequest {
  bill_id: string;
  payment_date: string;  // YYYY-MM-DD
  payment_mode: string;  // cash, cheque, upi, neft, rtgs, etc.
  amount: number;
  transaction_reference?: string;
  bank_name?: string;
  remarks?: string;
  late_fee_charged?: number;
}

export interface Payment {
  id: string;
  society_id: string;
  bill_id: string;
  flat_id: string;
  member_id: string;
  receipt_number: string;
  payment_date: string;
  payment_mode: string;
  amount: number;
  transaction_reference?: string;
  bank_name?: string;
  remarks?: string;
  status: string;
  late_fee_charged: number;
  is_partial_payment: boolean;
  receipt_generated: boolean;
  receipt_file_url?: string;
  created_at: string;
  flat_number?: string;
  member_name?: string;
  bill_amount?: number;
}

export interface PaymentHistoryResponse {
  payments: Payment[];
  summary: {
    total_payments: number;
    total_amount: number;
    payment_modes_breakdown: Record<string, number>;
    period: {
      start: string;
      end: string;
    };
  };
}

export interface ReconciliationSummary {
  period_start: string;
  period_end: string;
  total_bills_generated: number;
  total_bills_amount: number;
  total_payments_received: number;
  total_payments_amount: number;
  total_outstanding_bills: number;
  total_outstanding_amount: number;
  total_overdue_bills: number;
  total_overdue_amount: number;
  payment_by_mode: Record<string, number>;
  collection_rate: number;
  average_collection_days: number;
}

export interface OverdueBill {
  bill_id: string;
  bill_number: string;
  flat_number: string;
  member_name: string;
  bill_date: string;
  due_date: string;
  amount: number;
  days_overdue: number;
  last_reminder_sent?: string;
  member_phone?: string;
  member_email?: string;
}

export interface OverdueBillsResponse {
  overdue_bills: OverdueBill[];
  summary: {
    total_count: number;
    total_amount: number;
    oldest_overdue_days: number;
  };
}

export interface PaymentReminderRequest {
  bill_ids: string[];
  reminder_type: string;  // email, sms, whatsapp, push
  custom_message?: string;
}

export interface PaymentReminderResponse {
  success: boolean;
  reminders_sent: number;
  failed: number;
  details: Array<{
    bill_id: string;
    flat_number?: string;
    member_name?: string;
    days_overdue?: number;
    status: string;
    delivery_status?: string;
    reason?: string;
  }>;
}

class PaymentService {
  /**
   * Record a payment against a maintenance bill
   */
  async recordPayment(data: PaymentRecordRequest): Promise<Payment> {
    const response = await api.post<Payment>('/payments', data);
    return response.data;
  }

  /**
   * Get all payments for a specific bill
   */
  async getBillPayments(billId: string): Promise<Payment[]> {
    const response = await api.get<Payment[]>(`/payments/bill/${billId}`);
    return response.data;
  }

  /**
   * Get payment history for a flat
   */
  async getFlatPaymentHistory(
    flatId: string,
    startDate?: string,
    endDate?: string,
  ): Promise<PaymentHistoryResponse> {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    const response = await api.get<PaymentHistoryResponse>(
      `/payments/flat/${flatId}/history`,
      {params},
    );
    return response.data;
  }

  /**
   * Get reconciliation summary for a period
   */
  async getReconciliationSummary(
    startDate: string,
    endDate: string,
  ): Promise<ReconciliationSummary> {
    const response = await api.get<ReconciliationSummary>('/payments/reconciliation', {
      params: {start_date: startDate, end_date: endDate},
    });
    return response.data;
  }

  /**
   * Get all overdue bills
   */
  async getOverdueBills(): Promise<OverdueBillsResponse> {
    const response = await api.get<OverdueBillsResponse>('/payments/overdue');
    return response.data;
  }

  /**
   * Send payment reminders
   */
  async sendPaymentReminders(
    data: PaymentReminderRequest,
  ): Promise<PaymentReminderResponse> {
    const response = await api.post<PaymentReminderResponse>(
      '/payments/reminders/send',
      data,
    );
    return response.data;
  }

  /**
   * Download payment receipt PDF
   */
  async downloadPaymentReceipt(paymentId: string): Promise<Blob> {
    const response = await api.get(`/payments/${paymentId}/receipt/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Helper: Save receipt PDF to device
   */
  async downloadAndSaveReceipt(
    paymentId: string,
    receiptNumber: string,
  ): Promise<string> {
    const blob = await this.downloadPaymentReceipt(paymentId);

    // For React Native, use react-native-fs or similar
    // This is a simplified example
    const fileName = `Receipt_${receiptNumber.replace(/\//g, '_')}.pdf`;

    // Implementation would depend on your file handling library
    // For now, return the filename
    return fileName;
  }

  /**
   * Helper: Format payment mode for display
   */
  formatPaymentMode(mode: string): string {
    const modeMap: Record<string, string> = {
      cash: 'Cash',
      cheque: 'Cheque',
      upi: 'UPI',
      neft: 'NEFT',
      rtgs: 'RTGS',
      imps: 'IMPS',
      bank_transfer: 'Bank Transfer',
      online: 'Online',
      debit_card: 'Debit Card',
      credit_card: 'Credit Card',
      other: 'Other',
    };
    return modeMap[mode.toLowerCase()] || mode;
  }

  /**
   * Helper: Get payment mode icon
   */
  getPaymentModeIcon(mode: string): string {
    const iconMap: Record<string, string> = {
      cash: 'cash-outline',
      cheque: 'document-text-outline',
      upi: 'phone-portrait-outline',
      neft: 'swap-horizontal-outline',
      rtgs: 'swap-horizontal-outline',
      imps: 'flash-outline',
      bank_transfer: 'business-outline',
      online: 'globe-outline',
      debit_card: 'card-outline',
      credit_card: 'card-outline',
      other: 'ellipsis-horizontal-outline',
    };
    return iconMap[mode.toLowerCase()] || 'wallet-outline';
  }
}

export const paymentService = new PaymentService();



import api from './api';

export interface FinancialSummary {
  total_collection_today: number;
  total_collection_this_month: number;
  total_collection_this_year: number;
  pending_dues_total: number;
  pending_bills_count: number;
  overdue_bills_count: number;
  total_expenses_this_month: number;
  net_balance: number;
  bank_balance?: number;
  cash_balance?: number;
}

export interface PendingPayment {
  flat_number: string;
  member_name: string;
  amount_due: number;
  bill_month: string;
  days_overdue: number;
  bill_id: string;
}

export interface RecentActivity {
  id: string;
  type: string;
  title: string;
  description: string;
  amount?: number;
  timestamp: string;
  icon: string;
  color: string;
}

export interface QuickStat {
  label: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: string;
  color: string;
}

export interface DashboardSummary {
  financial_summary: FinancialSummary;
  pending_payments: PendingPayment[];
  recent_activities: RecentActivity[];
  quick_stats: QuickStat[];
}

export const dashboardService = {
  /**
   * Get comprehensive dashboard summary
   */
  async getDashboardSummary(): Promise<DashboardSummary> {
    const response = await api.get<DashboardSummary>('/api/dashboard/summary');
    return response.data;
  },
};


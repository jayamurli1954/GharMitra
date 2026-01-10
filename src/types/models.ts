export interface User {
  id: string;
  email: string;
  name: string;
  apartmentNumber: string;
  role: 'admin' | 'member';
  phoneNumber?: string;
  createdAt: Date;
}

export interface Transaction {
  id: string;
  type: 'income' | 'expense';
  category: string;
  amount: number;
  description: string;
  date: Date;
  addedBy: string;
  accountCode?: string; // Link to chart of accounts
  attachments?: string[];
  createdAt: Date;
}

export interface Member {
  id: string;
  name: string;
  apartmentNumber: string;
  email: string;
  phoneNumber?: string;
  monthlyDues: number;
  duesStatus: 'paid' | 'pending' | 'overdue';
  joinDate: Date;
}

export interface Message {
  id: string;
  roomId: string;
  senderId: string;
  senderName: string;
  text: string;
  timestamp: Date;
  read: boolean;
}

export interface ChatRoom {
  id: string;
  name: string;
  type: 'general' | 'maintenance' | 'announcements';
  lastMessage?: string;
  lastMessageTime?: Date;
  unreadCount: number;
}

export interface DuesPayment {
  id: string;
  memberId: string;
  amount: number;
  month: string;
  year: number;
  paymentDate: Date;
  paymentMethod: string;
  status: 'completed' | 'pending';
}

// Maintenance Billing Models
export interface ApartmentSettings {
  id: string;
  apartmentName: string;
  totalFlats: number;
  calculationMethod: 'sqft_rate' | 'variable';
  sqftRate?: number; // For sqft_rate method
  sinkingFundAmount?: number; // Monthly sinking fund
  createdAt: Date;
  updatedAt: Date;
}

export interface Flat {
  id: string;
  flatNumber: string;
  area: number; // in sq ft
  numberOfOccupants: number;
  ownerName: string;
  ownerEmail?: string;
  ownerPhone?: string;
  userId?: string; // Link to user account
  createdAt: Date;
  updatedAt: Date;
}

export interface FixedExpense {
  id: string;
  name: string;
  category: string; // 'salary' | 'electricity' | 'amc' | 'security' | 'other'
  amount: number;
  frequency: 'monthly' | 'annual' | 'quarterly';
  description?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface WaterExpense {
  id: string;
  month: string; // 'YYYY-MM'
  year: number;
  tankerCharges: number;
  governmentCharges: number;
  otherCharges: number;
  totalAmount: number;
  totalOccupants: number;
  perPersonCharge: number;
  createdAt: Date;
}

export interface MaintenanceBill {
  id: string;
  month: string; // 'YYYY-MM'
  year: number;
  flatId: string;
  flatNumber: string;
  calculationMethod: 'sqft_rate' | 'variable';

  // Sqft rate method
  area?: number;
  sqftRate?: number;
  sqftCharges?: number;

  // Variable method
  waterCharges?: number;
  fixedExpenses?: number;
  sinkingFund?: number;

  totalAmount: number;
  status: 'generated' | 'paid' | 'overdue';
  generatedDate: Date;
  paidDate?: Date;
  paymentMethod?: string;
  notes?: string;

  // Breakdown for transparency
  breakdown?: {
    waterExpenses?: {
      totalOccupants: number;
      perPersonCharge: number;
      flatOccupants: number;
      amount: number;
    };
    fixedExpensesList?: Array<{
      name: string;
      amount: number;
    }>;
    calculations?: string;
  };

  createdAt: Date;
  updatedAt: Date;
}

// Financial Accounting Models
export type AccountType = 'asset' | 'liability' | 'income' | 'expense' | 'capital';
export type AccountSubType =
  | 'current_asset'
  | 'fixed_asset'
  | 'current_liability'
  | 'long_term_liability'
  | 'capital'
  | 'revenue'
  | 'direct_expense'
  | 'indirect_expense';

export interface AccountCode {
  id: string;
  code: string; // e.g., '1001', '2001', '3001'
  name: string; // e.g., 'Cash in Hand', 'Bank Account'
  type: AccountType;
  subType: AccountSubType;
  description?: string;
  parentCode?: string; // For sub-accounts
  isActive: boolean;
  openingBalance?: number;
  currentBalance?: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface MemberTransaction {
  id: string;
  memberId: string;
  memberName: string;
  flatNumber: string;
  transactionType: 'bill' | 'payment' | 'adjustment';
  billId?: string; // Link to maintenance bill
  amount: number;
  date: Date;
  description: string;
  paymentMethod?: string;
  createdAt: Date;
}

export interface FinancialReport {
  id: string;
  reportType: 'receipts_payments' | 'income_expenditure' | 'balance_sheet';
  fromDate: Date;
  toDate: Date;
  generatedBy: string;
  generatedAt: Date;
  data: any; // Report-specific data structure
}

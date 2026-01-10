import {AccountCode, AccountType, AccountSubType} from '../types/models';

export const DEFAULT_CHART_OF_ACCOUNTS: Omit<
  AccountCode,
  'id' | 'createdAt' | 'updatedAt' | 'currentBalance'
>[] = [
  // ASSETS (1000-1999)
  {
    code: '1001',
    name: 'Cash in Hand',
    type: 'asset',
    subType: 'current_asset',
    description: 'Physical cash maintained by association',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '1002',
    name: 'Bank Account - Current',
    type: 'asset',
    subType: 'current_asset',
    description: 'Current bank account',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '1003',
    name: 'Bank Account - Savings',
    type: 'asset',
    subType: 'current_asset',
    description: 'Savings bank account',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '1004',
    name: 'Fixed Deposit',
    type: 'asset',
    subType: 'current_asset',
    description: 'Fixed deposits with banks',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '1005',
    name: 'Accounts Receivable - Members',
    type: 'asset',
    subType: 'current_asset',
    description: 'Outstanding maintenance dues from members',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '1101',
    name: 'Building',
    type: 'asset',
    subType: 'fixed_asset',
    description: 'Building and structure',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '1102',
    name: 'Generator',
    type: 'asset',
    subType: 'fixed_asset',
    description: 'Power backup generator',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '1103',
    name: 'Lift/Elevator',
    type: 'asset',
    subType: 'fixed_asset',
    description: 'Elevator equipment',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '1104',
    name: 'Furniture & Fixtures',
    type: 'asset',
    subType: 'fixed_asset',
    description: 'Common area furniture',
    isActive: true,
    openingBalance: 0,
  },

  // LIABILITIES (2000-2999)
  {
    code: '2001',
    name: 'Accounts Payable',
    type: 'liability',
    subType: 'current_liability',
    description: 'Outstanding bills to vendors',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '2002',
    name: 'Advance from Members',
    type: 'liability',
    subType: 'current_liability',
    description: 'Advance payments from members',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '2003',
    name: 'Security Deposits',
    type: 'liability',
    subType: 'current_liability',
    description: 'Security deposits from tenants/vendors',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '2101',
    name: 'Long Term Loans',
    type: 'liability',
    subType: 'long_term_liability',
    description: 'Long term loans and borrowings',
    isActive: true,
    openingBalance: 0,
  },

  // CAPITAL/EQUITY (3000-3999)
  {
    code: '3001',
    name: 'Capital Fund',
    type: 'capital',
    subType: 'capital',
    description: 'Initial capital contribution',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '3002',
    name: 'Sinking Fund',
    type: 'capital',
    subType: 'capital',
    description: 'Reserve for major repairs and replacements',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '3003',
    name: 'Repair & Maintenance Fund',
    type: 'capital',
    subType: 'capital',
    description: 'Reserve for routine repairs',
    isActive: true,
    openingBalance: 0,
  },
  {
    code: '3004',
    name: 'Retained Earnings',
    type: 'capital',
    subType: 'capital',
    description: 'Accumulated surplus',
    isActive: true,
    openingBalance: 0,
  },

  // INCOME (4000-4999)
  {
    code: '4001',
    name: 'Maintenance Charges',
    type: 'income',
    subType: 'revenue',
    description: 'Monthly maintenance dues from members',
    isActive: true,
  },
  {
    code: '4002',
    name: 'Water Charges',
    type: 'income',
    subType: 'revenue',
    description: 'Water charges collected from members',
    isActive: true,
  },
  {
    code: '4003',
    name: 'Parking Fees',
    type: 'income',
    subType: 'revenue',
    description: 'Parking space rental fees',
    isActive: true,
  },
  {
    code: '4004',
    name: 'Late Payment Charges',
    type: 'income',
    subType: 'revenue',
    description: 'Penalty for late payment',
    isActive: true,
  },
  {
    code: '4005',
    name: 'Interest Income',
    type: 'income',
    subType: 'revenue',
    description: 'Interest from FD and bank accounts',
    isActive: true,
  },
  {
    code: '4006',
    name: 'Amenity Booking Charges',
    type: 'income',
    subType: 'revenue',
    description: 'Charges for amenity booking',
    isActive: true,
  },
  {
    code: '4007',
    name: 'Other Income',
    type: 'income',
    subType: 'revenue',
    description: 'Miscellaneous income',
    isActive: true,
  },

  // EXPENSES (5000-5999)
  // Staff Expenses
  {
    code: '5001',
    name: 'Salaries - Security Staff',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Salaries for security personnel',
    isActive: true,
  },
  {
    code: '5002',
    name: 'Salaries - Housekeeping Staff',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Salaries for housekeeping staff',
    isActive: true,
  },
  {
    code: '5003',
    name: 'Salaries - Gardener',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Salary for gardener',
    isActive: true,
  },
  {
    code: '5004',
    name: 'Salaries - Electrician',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Salary for electrician',
    isActive: true,
  },
  {
    code: '5005',
    name: 'Salaries - Plumber',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Salary for plumber',
    isActive: true,
  },

  // Utilities
  {
    code: '5101',
    name: 'Electricity Charges',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Electricity bills for common areas',
    isActive: true,
  },
  {
    code: '5102',
    name: 'Water Charges - Tanker',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Tanker water charges',
    isActive: true,
  },
  {
    code: '5103',
    name: 'Water Charges - Corporation',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Municipal water charges',
    isActive: true,
  },

  // Maintenance & Repairs
  {
    code: '5201',
    name: 'Building Repairs',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Building maintenance and repairs',
    isActive: true,
  },
  {
    code: '5202',
    name: 'Painting',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Painting and whitewashing',
    isActive: true,
  },
  {
    code: '5203',
    name: 'Plumbing Repairs',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Plumbing maintenance',
    isActive: true,
  },
  {
    code: '5204',
    name: 'Electrical Repairs',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Electrical maintenance',
    isActive: true,
  },
  {
    code: '5205',
    name: 'Lift Maintenance',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Elevator AMC and repairs',
    isActive: true,
  },
  {
    code: '5206',
    name: 'Generator Maintenance',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Generator servicing and repairs',
    isActive: true,
  },
  {
    code: '5207',
    name: 'Pest Control',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Pest control services',
    isActive: true,
  },

  // Cleaning & Supplies
  {
    code: '5301',
    name: 'Housekeeping Supplies',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Cleaning materials and supplies',
    isActive: true,
  },
  {
    code: '5302',
    name: 'Gardening Expenses',
    type: 'expense',
    subType: 'direct_expense',
    description: 'Plants, fertilizers, gardening tools',
    isActive: true,
  },

  // Insurance & Professional Fees
  {
    code: '5401',
    name: 'Insurance Premium',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Building and other insurance',
    isActive: true,
  },
  {
    code: '5402',
    name: 'Legal & Professional Fees',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Legal, CA, and professional consultation fees',
    isActive: true,
  },
  {
    code: '5403',
    name: 'Audit Fees',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Annual audit fees',
    isActive: true,
  },

  // Administrative Expenses
  {
    code: '5501',
    name: 'Office Supplies',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Stationery and office supplies',
    isActive: true,
  },
  {
    code: '5502',
    name: 'Printing & Stationery',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Printing of notices, bills, etc.',
    isActive: true,
  },
  {
    code: '5503',
    name: 'Postage & Courier',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Postal and courier charges',
    isActive: true,
  },
  {
    code: '5504',
    name: 'Telephone & Internet',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Communication expenses',
    isActive: true,
  },
  {
    code: '5505',
    name: 'Bank Charges',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Bank transaction charges',
    isActive: true,
  },
  {
    code: '5506',
    name: 'Miscellaneous Expenses',
    type: 'expense',
    subType: 'indirect_expense',
    description: 'Other miscellaneous expenses',
    isActive: true,
  },
];

export const getAccountsByType = (
  accounts: AccountCode[],
  type: AccountType,
): AccountCode[] => {
  return accounts.filter(acc => acc.type === type && acc.isActive);
};

export const getAccountsBySubType = (
  accounts: AccountCode[],
  subType: AccountSubType,
): AccountCode[] => {
  return accounts.filter(acc => acc.subType === subType && acc.isActive);
};

export const getAccountByCode = (
  accounts: AccountCode[],
  code: string,
): AccountCode | undefined => {
  return accounts.find(acc => acc.code === code);
};

export const formatAccountDisplay = (account: AccountCode): string => {
  return `${account.code} - ${account.name}`;
};

import {
  Transaction,
  AccountCode,
  MemberTransaction,
  MaintenanceBill,
} from '../types/models';
import {formatCurrency} from './maintenanceCalculations';

export interface ReceiptsPaymentsData {
  receipts: {
    [key: string]: {
      accountName: string;
      amount: number;
      transactions: Transaction[];
    };
  };
  payments: {
    [key: string]: {
      accountName: string;
      amount: number;
      transactions: Transaction[];
    };
  };
  openingBalance: number;
  totalReceipts: number;
  totalPayments: number;
  closingBalance: number;
}

export interface IncomeExpenditureData {
  income: {
    [key: string]: {
      accountName: string;
      amount: number;
    };
  };
  expenditure: {
    [key: string]: {
      accountName: string;
      amount: number;
    };
  };
  totalIncome: number;
  totalExpenditure: number;
  surplus: number; // or deficit if negative
}

export interface BalanceSheetData {
  assets: {
    currentAssets: {[key: string]: {accountName: string; amount: number}};
    fixedAssets: {[key: string]: {accountName: string; amount: number}};
    totalCurrentAssets: number;
    totalFixedAssets: number;
    totalAssets: number;
  };
  liabilities: {
    currentLiabilities: {[key: string]: {accountName: string; amount: number}};
    longTermLiabilities: {[key: string]: {accountName: string; amount: number}};
    totalCurrentLiabilities: number;
    totalLongTermLiabilities: number;
    totalLiabilities: number;
  };
  capital: {
    funds: {[key: string]: {accountName: string; amount: number}};
    surplus: number;
    totalCapital: number;
  };
}

export const generateReceiptsPaymentsReport = (
  transactions: Transaction[],
  accounts: AccountCode[],
  fromDate: Date,
  toDate: Date,
  openingBalance: number,
): ReceiptsPaymentsData => {
  const data: ReceiptsPaymentsData = {
    receipts: {},
    payments: {},
    openingBalance,
    totalReceipts: 0,
    totalPayments: 0,
    closingBalance: 0,
  };

  // Filter transactions by date
  const filteredTransactions = transactions.filter(txn => {
    const txnDate = txn.date;
    return txnDate >= fromDate && txnDate <= toDate;
  });

  // Group transactions by account code
  filteredTransactions.forEach(txn => {
    const account = accounts.find(acc => acc.code === txn.accountCode);
    const accountName = account ? account.name : txn.category;
    const accountCode = txn.accountCode || 'MISC';

    if (txn.type === 'income') {
      if (!data.receipts[accountCode]) {
        data.receipts[accountCode] = {
          accountName,
          amount: 0,
          transactions: [],
        };
      }
      data.receipts[accountCode].amount += txn.amount;
      data.receipts[accountCode].transactions.push(txn);
      data.totalReceipts += txn.amount;
    } else {
      if (!data.payments[accountCode]) {
        data.payments[accountCode] = {
          accountName,
          amount: 0,
          transactions: [],
        };
      }
      data.payments[accountCode].amount += txn.amount;
      data.payments[accountCode].transactions.push(txn);
      data.totalPayments += txn.amount;
    }
  });

  data.closingBalance = openingBalance + data.totalReceipts - data.totalPayments;

  return data;
};

export const generateIncomeExpenditureReport = (
  transactions: Transaction[],
  accounts: AccountCode[],
  fromDate: Date,
  toDate: Date,
): IncomeExpenditureData => {
  const data: IncomeExpenditureData = {
    income: {},
    expenditure: {},
    totalIncome: 0,
    totalExpenditure: 0,
    surplus: 0,
  };

  // Filter transactions by date
  const filteredTransactions = transactions.filter(txn => {
    const txnDate = txn.date;
    return txnDate >= fromDate && txnDate <= toDate;
  });

  // Group by account code
  filteredTransactions.forEach(txn => {
    const account = accounts.find(acc => acc.code === txn.accountCode);
    const accountName = account ? account.name : txn.category;
    const accountCode = txn.accountCode || 'MISC';

    if (txn.type === 'income') {
      if (!data.income[accountCode]) {
        data.income[accountCode] = {
          accountName,
          amount: 0,
        };
      }
      data.income[accountCode].amount += txn.amount;
      data.totalIncome += txn.amount;
    } else {
      if (!data.expenditure[accountCode]) {
        data.expenditure[accountCode] = {
          accountName,
          amount: 0,
        };
      }
      data.expenditure[accountCode].amount += txn.amount;
      data.totalExpenditure += txn.amount;
    }
  });

  data.surplus = data.totalIncome - data.totalExpenditure;

  return data;
};

export const generateBalanceSheet = (
  accounts: AccountCode[],
  transactions: Transaction[],
  asOfDate: Date,
): BalanceSheetData => {
  const data: BalanceSheetData = {
    assets: {
      currentAssets: {},
      fixedAssets: {},
      totalCurrentAssets: 0,
      totalFixedAssets: 0,
      totalAssets: 0,
    },
    liabilities: {
      currentLiabilities: {},
      longTermLiabilities: {},
      totalCurrentLiabilities: 0,
      totalLongTermLiabilities: 0,
      totalLiabilities: 0,
    },
    capital: {
      funds: {},
      surplus: 0,
      totalCapital: 0,
    },
  };

  // Calculate current balances for each account
  const accountBalances = new Map<string, number>();

  accounts.forEach(account => {
    accountBalances.set(account.code, account.openingBalance || 0);
  });

  // Adjust balances based on transactions up to asOfDate
  transactions
    .filter(txn => txn.date <= asOfDate && txn.accountCode)
    .forEach(txn => {
      const account = accounts.find(acc => acc.code === txn.accountCode);
      if (!account) return;

      const currentBalance = accountBalances.get(account.code) || 0;

      // For assets and expenses: debit increases, credit decreases
      // For liabilities, capital, and income: credit increases, debit decreases
      if (
        account.type === 'asset' ||
        account.type === 'expense'
      ) {
        accountBalances.set(
          account.code,
          currentBalance + (txn.type === 'income' ? -txn.amount : txn.amount),
        );
      } else {
        accountBalances.set(
          account.code,
          currentBalance + (txn.type === 'income' ? txn.amount : -txn.amount),
        );
      }
    });

  // Populate balance sheet
  accounts.forEach(account => {
    const balance = accountBalances.get(account.code) || 0;
    if (balance === 0 && !account.openingBalance) return; // Skip zero balance accounts

    if (account.type === 'asset') {
      if (account.subType === 'current_asset') {
        data.assets.currentAssets[account.code] = {
          accountName: account.name,
          amount: balance,
        };
        data.assets.totalCurrentAssets += balance;
      } else if (account.subType === 'fixed_asset') {
        data.assets.fixedAssets[account.code] = {
          accountName: account.name,
          amount: balance,
        };
        data.assets.totalFixedAssets += balance;
      }
    } else if (account.type === 'liability') {
      if (account.subType === 'current_liability') {
        data.liabilities.currentLiabilities[account.code] = {
          accountName: account.name,
          amount: balance,
        };
        data.liabilities.totalCurrentLiabilities += balance;
      } else if (account.subType === 'long_term_liability') {
        data.liabilities.longTermLiabilities[account.code] = {
          accountName: account.name,
          amount: balance,
        };
        data.liabilities.totalLongTermLiabilities += balance;
      }
    } else if (account.type === 'capital') {
      data.capital.funds[account.code] = {
        accountName: account.name,
        amount: balance,
      };
    }
  });

  data.assets.totalAssets =
    data.assets.totalCurrentAssets + data.assets.totalFixedAssets;
  data.liabilities.totalLiabilities =
    data.liabilities.totalCurrentLiabilities +
    data.liabilities.totalLongTermLiabilities;

  // Calculate surplus from income & expenditure
  const incomeExpData = generateIncomeExpenditureReport(
    transactions,
    accounts,
    new Date(asOfDate.getFullYear(), 3, 1), // Financial year start (April 1)
    asOfDate,
  );
  data.capital.surplus = incomeExpData.surplus;

  // Calculate total capital
  Object.values(data.capital.funds).forEach(fund => {
    data.capital.totalCapital += fund.amount;
  });
  data.capital.totalCapital += data.capital.surplus;

  return data;
};

export interface MemberDuesReport {
  members: Array<{
    memberId: string;
    memberName: string;
    flatNumber: string;
    totalBilled: number;
    totalPaid: number;
    balance: number;
    status: 'clear' | 'due' | 'overdue';
  }>;
  summary: {
    totalBilled: number;
    totalPaid: number;
    totalDue: number;
    totalMembers: number;
    membersClear: number;
    membersDue: number;
    membersOverdue: number;
  };
}

export const generateMemberDuesReport = (
  bills: MaintenanceBill[],
  memberTransactions: MemberTransaction[],
  fromDate: Date,
  toDate: Date,
): MemberDuesReport => {
  const memberData = new Map<
    string,
    {
      memberName: string;
      flatNumber: string;
      totalBilled: number;
      totalPaid: number;
    }
  >();

  // Calculate billed amounts
  bills
    .filter(bill => {
      const billDate = bill.generatedDate;
      return billDate >= fromDate && billDate <= toDate;
    })
    .forEach(bill => {
      const key = bill.flatNumber;
      if (!memberData.has(key)) {
        memberData.set(key, {
          memberName: '', // Will be filled from transactions
          flatNumber: bill.flatNumber,
          totalBilled: 0,
          totalPaid: 0,
        });
      }
      const data = memberData.get(key)!;
      data.totalBilled += bill.totalAmount;
    });

  // Calculate paid amounts
  memberTransactions
    .filter(txn => {
      return (
        txn.transactionType === 'payment' &&
        txn.date >= fromDate &&
        txn.date <= toDate
      );
    })
    .forEach(txn => {
      const key = txn.flatNumber;
      if (!memberData.has(key)) {
        memberData.set(key, {
          memberName: txn.memberName,
          flatNumber: txn.flatNumber,
          totalBilled: 0,
          totalPaid: 0,
        });
      }
      const data = memberData.get(key)!;
      data.memberName = txn.memberName;
      data.totalPaid += txn.amount;
    });

  const members = Array.from(memberData.entries()).map(
    ([memberId, data]) => {
      const balance = data.totalBilled - data.totalPaid;
      let status: 'clear' | 'due' | 'overdue' = 'clear';
      if (balance > 0) {
        // Simple logic: if balance exists, it's due
        // Can be enhanced to check if it's overdue based on due date
        status = 'due';
      }

      return {
        memberId,
        memberName: data.memberName,
        flatNumber: data.flatNumber,
        totalBilled: data.totalBilled,
        totalPaid: data.totalPaid,
        balance,
        status,
      };
    },
  );

  const summary = {
    totalBilled: 0,
    totalPaid: 0,
    totalDue: 0,
    totalMembers: members.length,
    membersClear: 0,
    membersDue: 0,
    membersOverdue: 0,
  };

  members.forEach(member => {
    summary.totalBilled += member.totalBilled;
    summary.totalPaid += member.totalPaid;
    summary.totalDue += member.balance;

    if (member.status === 'clear') summary.membersClear++;
    else if (member.status === 'due') summary.membersDue++;
    else summary.membersOverdue++;
  });

  return {members, summary};
};

export interface MemberLedger {
  memberName: string;
  flatNumber: string;
  transactions: Array<{
    date: Date;
    description: string;
    debit: number; // Bills
    credit: number; // Payments
    balance: number;
  }>;
  openingBalance: number;
  closingBalance: number;
}

export const generateMemberLedger = (
  flatNumber: string,
  bills: MaintenanceBill[],
  memberTransactions: MemberTransaction[],
  fromDate: Date,
  toDate: Date,
): MemberLedger => {
  const memberBills = bills.filter(
    bill =>
      bill.flatNumber === flatNumber &&
      bill.generatedDate >= fromDate &&
      bill.generatedDate <= toDate,
  );

  const payments = memberTransactions.filter(
    txn =>
      txn.flatNumber === flatNumber &&
      txn.date >= fromDate &&
      txn.date <= toDate,
  );

  // Combine and sort by date
  const allTransactions: Array<{
    date: Date;
    type: 'bill' | 'payment';
    amount: number;
    description: string;
  }> = [
    ...memberBills.map(bill => ({
      date: bill.generatedDate,
      type: 'bill' as const,
      amount: bill.totalAmount,
      description: `Maintenance Bill - ${bill.month}`,
    })),
    ...payments.map(payment => ({
      date: payment.date,
      type: 'payment' as const,
      amount: payment.amount,
      description: payment.description,
    })),
  ].sort((a, b) => a.date.getTime() - b.date.getTime());

  let balance = 0; // Assuming opening balance is 0, can be enhanced
  const transactions = allTransactions.map(txn => {
    const debit = txn.type === 'bill' ? txn.amount : 0;
    const credit = txn.type === 'payment' ? txn.amount : 0;
    balance += debit - credit;

    return {
      date: txn.date,
      description: txn.description,
      debit,
      credit,
      balance,
    };
  });

  return {
    memberName: payments[0]?.memberName || '',
    flatNumber,
    transactions,
    openingBalance: 0,
    closingBalance: balance,
  };
};

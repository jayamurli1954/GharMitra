import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

const ReportsDashboardScreen = ({navigation}: any) => {
  // Reports list - Opening Balances is included
  const reports = [
    {
      id: 'receipts_payments',
      title: 'Receipts & Payments Account',
      description: 'Cash-based report showing all receipts and payments',
      icon: 'cash',
      color: '#4CAF50',
      screen: 'ReceiptsPaymentsReport',
    },
    {
      id: 'income_expenditure',
      title: 'Income & Expenditure Account',
      description: 'Accrual-based profit & loss statement',
      icon: 'trending-up',
      color: '#2196F3',
      screen: 'IncomeExpenditureReport',
    },
    {
      id: 'balance_sheet',
      title: 'Balance Sheet',
      description: 'Assets, Liabilities and Capital position',
      icon: 'analytics',
      color: '#9C27B0',
      screen: 'BalanceSheetReport',
    },
    {
      id: 'member_dues',
      title: 'Members Due Report',
      description: 'Outstanding dues from all members',
      icon: 'people',
      color: '#FF9800',
      screen: 'MemberDuesReport',
    },
    {
      id: 'member_ledger',
      title: 'Member Transaction Ledger',
      description: 'Detailed transaction history for a member',
      icon: 'document-text',
      color: '#F44336',
      screen: 'MemberLedger',
    },
    {
      id: 'general_ledger',
      title: 'General Ledger Report',
      description: 'Consolidated transaction ledger by account head',
      icon: 'book',
      color: '#673AB7',
      screen: 'GeneralLedgerReport',
    },
    {
      id: 'opening_balance',
      title: 'Opening Balances',
      description: 'View and manage account opening balances',
      icon: 'calculator',
      color: '#795548',
      screen: 'OpeningBalance',
    },
    {
      id: 'chart_of_accounts',
      title: 'Chart of Accounts',
      description: 'View and manage account codes',
      icon: 'list',
      color: '#607D8B',
      screen: 'ChartOfAccounts',
    },
    {
      id: 'trial_balance',
      title: 'Trial Balance',
      description: 'All account balances - Debit must equal Credit',
      icon: 'calculator',
      color: '#00BCD4',
      screen: 'TrialBalanceReport',
    },
    {
      id: 'cash_book',
      title: 'Cash Book Ledger',
      description: 'All cash transactions and balance',
      icon: 'wallet',
      color: '#4CAF50',
      screen: 'CashBookLedger',
    },
    {
      id: 'bank_ledger',
      title: 'Bank Ledger',
      description: 'All bank transactions and balance',
      icon: 'card',
      color: '#2196F3',
      screen: 'BankLedger',
    },
    {
      id: 'journal_entry',
      title: 'Create Journal Entry',
      description: 'Create double-entry journal entries',
      icon: 'create',
      color: '#9C27B0',
      screen: 'JournalEntry',
    },
    {
      id: 'journal_report',
      title: 'Journal Entry Report',
      description: 'View all journal entries',
      icon: 'document-text',
      color: '#FF5722',
      screen: 'JournalEntryReport',
    },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Icon name="bar-chart" size={50} color="#007AFF" />
        <Text style={styles.headerTitle}>Financial Reports</Text>
        <Text style={styles.headerSubtitle}>
          Comprehensive financial analysis and reporting
        </Text>
      </View>

      <View style={styles.content}>
        {reports.map(report => (
          <TouchableOpacity
            key={report.id}
            style={styles.reportCard}
            onPress={() => navigation.navigate(report.screen)}>
            <View
              style={[styles.reportIcon, {backgroundColor: report.color}]}>
              <Icon name={report.icon} size={30} color="#FFF" />
            </View>
            <View style={styles.reportDetails}>
              <Text style={styles.reportTitle}>{report.title}</Text>
              <Text style={styles.reportDescription}>
                {report.description}
              </Text>
            </View>
            <Icon name="chevron-forward" size={24} color="#999" />
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.infoBox}>
        <Icon name="information-circle" size={24} color="#007AFF" />
        <View style={styles.infoContent}>
          <Text style={styles.infoTitle}>About Financial Reports</Text>
          <Text style={styles.infoText}>
            These reports help you understand the financial health of your
            apartment association. Generate reports for any period to analyze
            income, expenses, and member dues.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 30,
    alignItems: 'center',
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFF',
    marginTop: 15,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginTop: 5,
    textAlign: 'center',
  },
  content: {
    padding: 15,
  },
  reportCard: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 15,
    marginBottom: 12,
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  reportIcon: {
    width: 60,
    height: 60,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  reportDetails: {
    flex: 1,
    marginLeft: 15,
  },
  reportTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  reportDescription: {
    fontSize: 13,
    color: '#666',
  },
  infoBox: {
    flexDirection: 'row',
    margin: 15,
    padding: 15,
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  infoContent: {
    flex: 1,
    marginLeft: 10,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 5,
  },
  infoText: {
    fontSize: 13,
    color: '#333',
    lineHeight: 20,
  },
});

export default ReportsDashboardScreen;

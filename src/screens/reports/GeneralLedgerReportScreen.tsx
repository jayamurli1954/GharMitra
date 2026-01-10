import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { reportsService } from '../../services/reportsService';

const GeneralLedgerReportScreen = ({ navigation }: any) => {
  const [loading, setLoading] = useState(false);
  const getCurrentFYStart = () => {
    const today = new Date();
    const currentMonth = today.getMonth(); // 0-indexed, April is 3
    const currentYear = today.getFullYear();
    // If before April, FY started last year
    const fyStartYear = currentMonth < 3 ? currentYear - 1 : currentYear;
    return new Date(fyStartYear, 3, 1); // April 1st
  };

  const [fromDate, setFromDate] = useState(getCurrentFYStart());
  const [toDate, setToDate] = useState(new Date());
  const [showFromDatePicker, setShowFromDatePicker] = useState(false);
  const [showToDatePicker, setShowToDatePicker] = useState(false);
  const [reportData, setReportData] = useState<any>(null);

  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const loadReport = async () => {
    if (fromDate > toDate) {
      Alert.alert('Error', 'From date cannot be after To date');
      return;
    }

    setLoading(true);
    try {
      const data = await reportsService.getGeneralLedgerReport(
        formatDate(fromDate),
        formatDate(toDate)
      );
      setReportData(data);
    } catch (error: any) {
      console.error('Error loading report:', error);
      Alert.alert(
        'Error',
        error?.response?.data?.detail || 'Failed to load report. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'excel' | 'pdf') => {
    try {
      setLoading(true);
      await reportsService.exportGeneralLedger(
        formatDate(fromDate),
        formatDate(toDate),
        format
      );
      Alert.alert(
        'Success',
        `${format.toUpperCase()} report exported successfully!`,
        [{ text: 'OK' }]
      );
    } catch (error: any) {
      console.error('Export error:', error);
      Alert.alert(
        'Export Error',
        error?.response?.data?.detail || `Failed to export ${format.toUpperCase()}. Please try again.`,
        [{ text: 'OK' }]
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, []);

  return (
    <View style={styles.container}>
      {/* Date Range Selector */}
      <View style={styles.dateSelector}>
        <View style={styles.dateRow}>
          <Text style={styles.dateLabel}>From Date:</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowFromDatePicker(true)}
            activeOpacity={0.7}>
            <Icon name="calendar-outline" size={20} color="#007AFF" />
            <Text style={styles.dateText}>{formatDate(fromDate)}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.dateRow}>
          <Text style={styles.dateLabel}>To Date:</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowToDatePicker(true)}
            activeOpacity={0.7}>
            <Icon name="calendar-outline" size={20} color="#007AFF" />
            <Text style={styles.dateText}>{formatDate(toDate)}</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.generateButton}
          onPress={loadReport}
          disabled={loading}
          activeOpacity={0.7}>
          {loading ? (
            <ActivityIndicator size="small" color="#FFF" />
          ) : (
            <>
              <Icon name="refresh" size={20} color="#FFF" />
              <Text style={styles.generateButtonText}>Generate Report</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Export Buttons */}
      {reportData && (
        <View style={styles.exportContainer}>
          <TouchableOpacity
            style={[styles.exportButton, styles.excelButton]}
            onPress={() => handleExport('excel')}
            activeOpacity={0.7}>
            <Icon name="document-text" size={20} color="#FFF" />
            <Text style={styles.exportButtonText}>Export Excel</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.exportButton, styles.pdfButton]}
            onPress={() => handleExport('pdf')}
            activeOpacity={0.7}>
            <Icon name="document" size={20} color="#FFF" />
            <Text style={styles.exportButtonText}>Export PDF</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Report Content */}
      {loading && !reportData ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading report...</Text>
        </View>
      ) : reportData ? (
        <ScrollView style={styles.reportContainer} showsVerticalScrollIndicator={false}>
          {/* Report Header */}
          <View style={styles.reportHeader}>
            {reportData.society?.logo_url && (
              <View style={styles.logoContainer}>
                <Text style={styles.logoPlaceholder}>[Logo]</Text>
              </View>
            )}
            <View style={styles.headerContent}>
              <Text style={styles.reportTitle}>{reportData.report_type}</Text>
              <Text style={styles.societyName}>{reportData.society?.name || 'Society'}</Text>
              <Text style={styles.periodText}>
                Period: {formatDate(new Date(reportData.period.from))} to{' '}
                {formatDate(new Date(reportData.period.to))}
              </Text>
            </View>
          </View>

          {/* Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Summary</Text>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Income Accounts:</Text>
              <Text style={styles.summaryValue}>
                {reportData.summary?.total_income_accounts || 0}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Expense Accounts:</Text>
              <Text style={styles.summaryValue}>
                {reportData.summary?.total_expense_accounts || 0}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Total Income:</Text>
              <Text style={[styles.summaryValue, styles.positiveAmount]}>
                {formatCurrency(reportData.summary?.total_income || 0)}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Total Expense:</Text>
              <Text style={[styles.summaryValue, styles.negativeAmount]}>
                {formatCurrency(reportData.summary?.total_expense || 0)}
              </Text>
            </View>
            <View style={[styles.summaryRow, styles.netIncomeRow]}>
              <Text style={styles.summaryLabel}>Net Income:</Text>
              <Text
                style={[
                  styles.summaryValue,
                  (reportData.summary?.net_income || 0) >= 0
                    ? styles.positiveAmount
                    : styles.negativeAmount,
                ]}>
                {formatCurrency(reportData.summary?.net_income || 0)}
              </Text>
            </View>
          </View>

          {/* Ledger Entries */}
          <View style={styles.ledgerContainer}>
            <Text style={styles.sectionTitle}>Ledger Entries by Account</Text>
            {reportData.ledger_entries?.map((entry: any, index: number) => {
              if (entry.transactions.length === 0) return null;

              return (
                <View key={index} style={styles.accountCard}>
                  <View style={styles.accountHeader}>
                    <View>
                      <Text style={styles.accountCode}>{entry.account_code}</Text>
                      <Text style={styles.accountName}>{entry.account_name}</Text>
                      <Text style={styles.accountType}>
                        {entry.account_type?.toUpperCase() || 'N/A'}
                      </Text>
                    </View>
                    <View style={styles.accountTotals}>
                      <Text style={styles.totalLabel}>Opening:</Text>
                      <Text style={styles.totalValue}>
                        {formatCurrency(entry.opening_balance || 0)}
                      </Text>
                      <Text style={styles.totalLabel}>Closing:</Text>
                      <Text style={styles.totalValue}>
                        {formatCurrency(entry.closing_balance || 0)}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.transactionsTable}>
                    <View style={styles.tableHeader}>
                      <Text style={[styles.tableHeaderText, { flex: 1 }]}>Date</Text>
                      <Text style={[styles.tableHeaderText, { flex: 2 }]}>Description</Text>
                      <Text style={[styles.tableHeaderText, { flex: 1, textAlign: 'right' }]}>
                        Debit
                      </Text>
                      <Text style={[styles.tableHeaderText, { flex: 1, textAlign: 'right' }]}>
                        Credit
                      </Text>
                    </View>

                    {entry.transactions.map((txn: any, txnIndex: number) => (
                      <View key={txnIndex} style={styles.tableRow}>
                        <Text style={[styles.tableCell, { flex: 1 }]}>
                          {formatDate(new Date(txn.date))}
                        </Text>
                        <Text style={[styles.tableCell, { flex: 2 }]} numberOfLines={2}>
                          {txn.description || '-'}
                        </Text>
                        <Text
                          style={[
                            styles.tableCell,
                            { flex: 1, textAlign: 'right' },
                            txn.debit > 0 && styles.debitAmount,
                          ]}>
                          {txn.debit > 0 ? formatCurrency(txn.debit) : '-'}
                        </Text>
                        <Text
                          style={[
                            styles.tableCell,
                            { flex: 1, textAlign: 'right' },
                            txn.credit > 0 && styles.creditAmount,
                          ]}>
                          {txn.credit > 0 ? formatCurrency(txn.credit) : '-'}
                        </Text>
                      </View>
                    ))}

                    <View style={styles.tableFooter}>
                      <Text style={[styles.tableCell, { flex: 3, fontWeight: '700' }]}>Total:</Text>
                      <Text
                        style={[
                          styles.tableCell,
                          { flex: 1, textAlign: 'right', fontWeight: '700' },
                          entry.total_debit > 0 && styles.debitAmount,
                        ]}>
                        {entry.total_debit > 0 ? formatCurrency(entry.total_debit) : '-'}
                      </Text>
                      <Text
                        style={[
                          styles.tableCell,
                          { flex: 1, textAlign: 'right', fontWeight: '700' },
                          entry.total_credit > 0 && styles.creditAmount,
                        ]}>
                        {entry.total_credit > 0 ? formatCurrency(entry.total_credit) : '-'}
                      </Text>
                    </View>
                  </View>
                </View>
              );
            })}
          </View>

          {/* Report Footer */}
          {reportData.society?.address && (
            <View style={styles.reportFooter}>
              <Text style={styles.footerText}>{reportData.society.address}</Text>
            </View>
          )}
        </ScrollView>
      ) : (
        <View style={styles.emptyContainer}>
          <Icon name="document-text-outline" size={64} color="#C7C7CC" />
          <Text style={styles.emptyText}>No report data</Text>
          <Text style={styles.emptySubtext}>
            Select date range and click "Generate Report"
          </Text>
        </View>
      )}

      {/* Date Pickers */}
      {showFromDatePicker && (
        <DateTimePicker
          value={fromDate}
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowFromDatePicker(false);
            if (selectedDate) setFromDate(selectedDate);
          }}
        />
      )}

      {showToDatePicker && (
        <DateTimePicker
          value={toDate}
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowToDatePicker(false);
            if (selectedDate) setToDate(selectedDate);
          }}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  dateSelector: {
    backgroundColor: '#FFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  dateLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D1D1F',
    width: 100,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    flex: 1,
    gap: 8,
  },
  dateText: {
    fontSize: 14,
    color: '#1D1D1F',
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
  },
  generateButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  exportContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  exportButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  excelButton: {
    backgroundColor: '#4CAF50',
  },
  pdfButton: {
    backgroundColor: '#F44336',
  },
  exportButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  reportContainer: {
    flex: 1,
  },
  reportHeader: {
    backgroundColor: '#FFF',
    padding: 20,
    flexDirection: 'row',
    borderBottomWidth: 2,
    borderBottomColor: '#007AFF',
  },
  logoContainer: {
    width: 60,
    height: 60,
    marginRight: 16,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
  },
  logoPlaceholder: {
    fontSize: 10,
    color: '#999',
  },
  headerContent: {
    flex: 1,
  },
  reportTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  societyName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: 4,
  },
  periodText: {
    fontSize: 13,
    color: '#666',
  },
  summaryCard: {
    backgroundColor: '#FFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  positiveAmount: {
    color: '#4CAF50',
  },
  negativeAmount: {
    color: '#F44336',
  },
  netIncomeRow: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  ledgerContainer: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 16,
  },
  accountCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  accountHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  accountCode: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    fontFamily: 'monospace',
  },
  accountName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginTop: 4,
  },
  accountType: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  accountTotals: {
    alignItems: 'flex-end',
  },
  totalLabel: {
    fontSize: 12,
    color: '#666',
  },
  totalValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  transactionsTable: {
    marginTop: 8,
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#F5F5F5',
    paddingVertical: 8,
    paddingHorizontal: 8,
    borderRadius: 6,
    marginBottom: 4,
  },
  tableHeaderText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 8,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  tableCell: {
    fontSize: 12,
    color: '#1D1D1F',
  },
  debitAmount: {
    color: '#F44336',
  },
  creditAmount: {
    color: '#4CAF50',
  },
  tableFooter: {
    flexDirection: 'row',
    paddingVertical: 8,
    paddingHorizontal: 8,
    marginTop: 4,
    backgroundColor: '#F9F9F9',
    borderRadius: 6,
  },
  reportFooter: {
    backgroundColor: '#FFF',
    padding: 16,
    marginTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  footerText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    color: '#999',
    marginTop: 16,
    fontWeight: '600',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#BBB',
    marginTop: 8,
    textAlign: 'center',
  },
});

export default GeneralLedgerReportScreen;


import React, {useState, useEffect} from 'react';
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
import {reportsService} from '../../services/reportsService';

const BankLedgerScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(false);
  const [fromDate, setFromDate] = useState(new Date(new Date().getFullYear(), 0, 1)); // Jan 1 of current year
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
      const data = await reportsService.getBankLedger(
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
      await reportsService.exportBankLedger(
        formatDate(fromDate),
        formatDate(toDate),
        format
      );
      Alert.alert(
        'Success',
        `${format.toUpperCase()} report exported successfully!`,
        [{text: 'OK'}]
      );
    } catch (error: any) {
      console.error('Export error:', error);
      Alert.alert(
        'Export Error',
        error?.response?.data?.detail || `Failed to export ${format.toUpperCase()}. Please try again.`,
        [{text: 'OK'}]
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

      {/* Date Pickers */}
      {showFromDatePicker && (
        <DateTimePicker
          value={fromDate}
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowFromDatePicker(false);
            if (selectedDate) {
              setFromDate(selectedDate);
            }
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
            if (selectedDate) {
              setToDate(selectedDate);
            }
          }}
        />
      )}

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
          <Text style={styles.loadingText}>Loading bank ledger...</Text>
        </View>
      ) : reportData ? (
        <ScrollView style={styles.reportContainer} showsVerticalScrollIndicator={false}>
          {/* Report Header */}
          <View style={styles.reportHeader}>
            <Text style={styles.reportTitle}>{reportData.report_type}</Text>
            <Text style={styles.periodText}>
              Period: {reportData.period?.from} to {reportData.period?.to}
            </Text>
          </View>

          {/* Opening Balance */}
          <View style={styles.balanceCard}>
            <Text style={styles.balanceLabel}>Opening Balance</Text>
            <Text style={styles.balanceAmount}>
              {formatCurrency(reportData.opening_balance || 0)}
            </Text>
          </View>

          {/* Bank Transactions Table */}
          {reportData.transactions && reportData.transactions.length > 0 ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Bank Transactions</Text>
              <View style={styles.table}>
                {/* Table Header */}
                <View style={styles.tableHeader}>
                  <Text style={[styles.headerCell, {flex: 1.5}]}>Date</Text>
                  <Text style={[styles.headerCell, {flex: 3}]}>Description</Text>
                  <Text style={[styles.headerCell, {flex: 1.5, textAlign: 'right'}]}>Debit</Text>
                  <Text style={[styles.headerCell, {flex: 1.5, textAlign: 'right'}]}>Credit</Text>
                  <Text style={[styles.headerCell, {flex: 2, textAlign: 'right'}]}>Balance</Text>
                </View>

                {/* Table Rows */}
                {reportData.transactions.map((txn: any, index: number) => {
                  const runningBalance = 
                    (reportData.opening_balance || 0) + 
                    reportData.transactions
                      .slice(0, index + 1)
                      .reduce((sum: number, t: any) => 
                        sum + (t.debit || 0) - (t.credit || 0), 0);

                  return (
                    <View key={index} style={styles.tableRow}>
                      <Text style={[styles.tableCell, {flex: 1.5}]}>
                        {new Date(txn.date).toLocaleDateString('en-IN')}
                      </Text>
                      <Text style={[styles.tableCell, {flex: 3}]} numberOfLines={2}>
                        {txn.description}
                      </Text>
                      <Text style={[
                        styles.tableCell, 
                        {flex: 1.5, textAlign: 'right', color: txn.debit > 0 ? '#28a745' : '#999'}
                      ]}>
                        {txn.debit > 0 ? formatCurrency(txn.debit) : '-'}
                      </Text>
                      <Text style={[
                        styles.tableCell, 
                        {flex: 1.5, textAlign: 'right', color: txn.credit > 0 ? '#dc3545' : '#999'}
                      ]}>
                        {txn.credit > 0 ? formatCurrency(txn.credit) : '-'}
                      </Text>
                      <Text style={[styles.tableCell, {flex: 2, textAlign: 'right', fontWeight: '600'}]}>
                        {formatCurrency(runningBalance)}
                      </Text>
                    </View>
                  );
                })}

                {/* Totals Row */}
                <View style={[styles.tableRow, styles.totalRow]}>
                  <Text style={[styles.tableCell, {flex: 1.5, fontWeight: 'bold'}]}>
                    TOTAL
                  </Text>
                  <Text style={[styles.tableCell, {flex: 3}]}></Text>
                  <Text style={[styles.tableCell, {flex: 1.5, textAlign: 'right', fontWeight: 'bold', color: '#28a745'}]}>
                    {formatCurrency(reportData.total_debit || 0)}
                  </Text>
                  <Text style={[styles.tableCell, {flex: 1.5, textAlign: 'right', fontWeight: 'bold', color: '#dc3545'}]}>
                    {formatCurrency(reportData.total_credit || 0)}
                  </Text>
                  <Text style={[styles.tableCell, {flex: 2, textAlign: 'right'}]}></Text>
                </View>
              </View>
            </View>
          ) : (
            <View style={styles.emptyState}>
              <Icon name="card-outline" size={60} color="#CCC" />
              <Text style={styles.emptyText}>No bank transactions found</Text>
              <Text style={styles.emptySubtext}>
                for the selected date range
              </Text>
            </View>
          )}

          {/* Closing Balance */}
          <View style={[styles.balanceCard, styles.closingBalance]}>
            <Text style={styles.balanceLabel}>Closing Balance</Text>
            <Text style={[styles.balanceAmount, styles.closingAmount]}>
              {formatCurrency(reportData.closing_balance || 0)}
            </Text>
          </View>

          {/* Summary Cards */}
          <View style={styles.summaryContainer}>
            <View style={[styles.summaryCard, {borderLeftColor: '#28a745'}]}>
              <Text style={styles.summaryLabel}>Total Deposits</Text>
              <Text style={[styles.summaryAmount, {color: '#28a745'}]}>
                {formatCurrency(reportData.total_debit || 0)}
              </Text>
            </View>
            <View style={[styles.summaryCard, {borderLeftColor: '#dc3545'}]}>
              <Text style={styles.summaryLabel}>Total Withdrawals</Text>
              <Text style={[styles.summaryAmount, {color: '#dc3545'}]}>
                {formatCurrency(reportData.total_credit || 0)}
              </Text>
            </View>
          </View>
        </ScrollView>
      ) : (
        <View style={styles.emptyState}>
          <Icon name="document-text-outline" size={60} color="#CCC" />
          <Text style={styles.emptyText}>No Report Generated</Text>
          <Text style={styles.emptySubtext}>
            Select dates and click Generate Report
          </Text>
        </View>
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
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  dateLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F8FF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#007AFF',
    flex: 2,
  },
  dateText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  generateButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  exportContainer: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  exportButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 8,
    marginHorizontal: 4,
  },
  excelButton: {
    backgroundColor: '#217346',
  },
  pdfButton: {
    backgroundColor: '#DC3545',
  },
  exportButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
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
    padding: 16,
    marginBottom: 8,
    alignItems: 'center',
  },
  reportTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  periodText: {
    fontSize: 14,
    color: '#666',
  },
  balanceCard: {
    backgroundColor: '#FFF',
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  balanceLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  balanceAmount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  closingBalance: {
    backgroundColor: '#E8F5E9',
    marginTop: 16,
  },
  closingAmount: {
    color: '#28a745',
  },
  section: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 12,
    padding: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  table: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    overflow: 'hidden',
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#F8F9FA',
    borderBottomWidth: 2,
    borderBottomColor: '#DEE2E6',
    paddingVertical: 12,
    paddingHorizontal: 8,
  },
  headerCell: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#495057',
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#E9ECEF',
    paddingVertical: 10,
    paddingHorizontal: 8,
  },
  totalRow: {
    backgroundColor: '#F8F9FA',
    borderBottomWidth: 0,
  },
  tableCell: {
    fontSize: 12,
    color: '#333',
  },
  summaryContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: '#FFF',
    padding: 16,
    marginHorizontal: 4,
    borderRadius: 12,
    borderLeftWidth: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  summaryAmount: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#999',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#BBB',
    marginTop: 8,
    textAlign: 'center',
  },
});

export default BankLedgerScreen;



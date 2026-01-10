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
import {flatsService} from '../../services/flatsService';

const MemberTransactionLedgerScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(false);
  const [flatsLoading, setFlatsLoading] = useState(true);
  const [flats, setFlats] = useState<any[]>([]);
  const [selectedFlat, setSelectedFlat] = useState<any>(null);
  const [fromDate, setFromDate] = useState<Date | null>(null);
  const [toDate, setToDate] = useState<Date | null>(null);
  const [showFromDatePicker, setShowFromDatePicker] = useState(false);
  const [showToDatePicker, setShowToDatePicker] = useState(false);
  const [reportData, setReportData] = useState<any>(null);

  const formatDate = (date: Date | null) => {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  useEffect(() => {
    loadFlats();
  }, []);

  const loadFlats = async () => {
    setFlatsLoading(true);
    try {
      const flatsData = await flatsService.getFlats();
      setFlats(flatsData);
      if (flatsData.length === 1) {
        // Auto-select if only one flat
        setSelectedFlat(flatsData[0]);
      }
    } catch (error: any) {
      console.error('Error loading flats:', error);
      Alert.alert('Error', 'Failed to load flats. Please try again.');
    } finally {
      setFlatsLoading(false);
    }
  };

  const loadReport = async () => {
    if (!selectedFlat) {
      Alert.alert('Error', 'Please select a flat first');
      return;
    }

    setLoading(true);
    try {
      const data = await reportsService.getMemberLedger(
        selectedFlat.id,
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
    if (!selectedFlat) {
      Alert.alert('Error', 'Please select a flat first');
      return;
    }

    try {
      setLoading(true);
      await reportsService.exportMemberLedger(
        selectedFlat.id,
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

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'paid':
        return '#28a745';
      case 'unpaid':
        return '#dc3545';
      default:
        return '#ffc107';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'paid':
        return 'checkmark-circle';
      case 'unpaid':
        return 'close-circle';
      default:
        return 'time';
    }
  };

  if (flatsLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading flats...</Text>
      </View>
    );
  }

  if (flats.length === 0) {
    return (
      <View style={styles.emptyState}>
        <Icon name="home-outline" size={60} color="#CCC" />
        <Text style={styles.emptyText}>No flats found</Text>
        <Text style={styles.emptySubtext}>
          Please add flats before viewing member ledgers
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Flat Selector */}
      <View style={styles.selectorContainer}>
        <Text style={styles.selectorLabel}>Select Flat:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {flats.map((flat: any) => (
            <TouchableOpacity
              key={flat.id}
              style={[
                styles.flatChip,
                selectedFlat?.id === flat.id && styles.flatChipSelected,
              ]}
              onPress={() => {
                setSelectedFlat(flat);
                setReportData(null); // Clear previous report
              }}
              activeOpacity={0.7}>
              <Text
                style={[
                  styles.flatChipText,
                  selectedFlat?.id === flat.id && styles.flatChipTextSelected,
                ]}>
                {flat.flat_number}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Date Range Selector */}
      {selectedFlat && (
        <View style={styles.dateSelector}>
          <View style={styles.dateRow}>
            <Text style={styles.dateLabel}>From Date (Optional):</Text>
            <TouchableOpacity
              style={styles.dateButton}
              onPress={() => setShowFromDatePicker(true)}
              activeOpacity={0.7}>
              <Icon name="calendar-outline" size={20} color="#007AFF" />
              <Text style={styles.dateText}>
                {fromDate ? formatDate(fromDate) : 'All Time'}
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.dateRow}>
            <Text style={styles.dateLabel}>To Date (Optional):</Text>
            <TouchableOpacity
              style={styles.dateButton}
              onPress={() => setShowToDatePicker(true)}
              activeOpacity={0.7}>
              <Icon name="calendar-outline" size={20} color="#007AFF" />
              <Text style={styles.dateText}>
                {toDate ? formatDate(toDate) : 'All Time'}
              </Text>
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
      )}

      {/* Date Pickers */}
      {showFromDatePicker && (
        <DateTimePicker
          value={fromDate || new Date()}
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
          value={toDate || new Date()}
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
          <Text style={styles.loadingText}>Loading member ledger...</Text>
        </View>
      ) : reportData ? (
        <ScrollView style={styles.reportContainer} showsVerticalScrollIndicator={false}>
          {/* Report Header */}
          <View style={styles.reportHeader}>
            <Text style={styles.reportTitle}>{reportData.report_type}</Text>
            {reportData.period && (reportData.period.from || reportData.period.to) && (
              <Text style={styles.periodText}>
                Period: {reportData.period.from || 'All'} to {reportData.period.to || 'All'}
              </Text>
            )}
          </View>

          {/* Member Info Card */}
          {reportData.flat && (
            <View style={styles.memberCard}>
              <View style={styles.memberRow}>
                <Icon name="home" size={24} color="#007AFF" />
                <View style={styles.memberInfo}>
                  <Text style={styles.memberLabel}>Flat Number</Text>
                  <Text style={styles.memberValue}>{reportData.flat.flat_number}</Text>
                </View>
              </View>
              {reportData.flat.owner_name && (
                <View style={styles.memberRow}>
                  <Icon name="person" size={24} color="#007AFF" />
                  <View style={styles.memberInfo}>
                    <Text style={styles.memberLabel}>Owner Name</Text>
                    <Text style={styles.memberValue}>{reportData.flat.owner_name}</Text>
                  </View>
                </View>
              )}
              <View style={styles.memberRow}>
                <Icon name="expand" size={24} color="#007AFF" />
                <View style={styles.memberInfo}>
                  <Text style={styles.memberLabel}>Area</Text>
                  <Text style={styles.memberValue}>{reportData.flat.area_sqft} sq ft</Text>
                </View>
              </View>
              <View style={styles.memberRow}>
                <Icon name="people" size={24} color="#007AFF" />
                <View style={styles.memberInfo}>
                  <Text style={styles.memberLabel}>Occupants</Text>
                  <Text style={styles.memberValue}>{reportData.flat.occupants}</Text>
                </View>
              </View>
            </View>
          )}

          {/* Summary Cards */}
          <View style={styles.summaryContainer}>
            <View style={[styles.summaryCard, {borderLeftColor: '#007AFF'}]}>
              <Text style={styles.summaryLabel}>Total Billed</Text>
              <Text style={[styles.summaryAmount, {color: '#007AFF'}]}>
                {formatCurrency(reportData.summary?.total_billed || 0)}
              </Text>
            </View>
            <View style={[styles.summaryCard, {borderLeftColor: '#28a745'}]}>
              <Text style={styles.summaryLabel}>Total Paid</Text>
              <Text style={[styles.summaryAmount, {color: '#28a745'}]}>
                {formatCurrency(reportData.summary?.total_paid || 0)}
              </Text>
            </View>
            <View style={[styles.summaryCard, {borderLeftColor: '#dc3545'}]}>
              <Text style={styles.summaryLabel}>Outstanding</Text>
              <Text style={[styles.summaryAmount, {color: '#dc3545'}]}>
                {formatCurrency(reportData.summary?.outstanding || 0)}
              </Text>
            </View>
          </View>

          {/* Transactions Table */}
          {reportData.transactions && reportData.transactions.length > 0 ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Transaction History</Text>
              <View style={styles.table}>
                {/* Table Header */}
                <View style={styles.tableHeader}>
                  <Text style={[styles.headerCell, {flex: 1.5}]}>Date</Text>
                  <Text style={[styles.headerCell, {flex: 3}]}>Description</Text>
                  <Text style={[styles.headerCell, {flex: 1.5, textAlign: 'right'}]}>Amount</Text>
                  <Text style={[styles.headerCell, {flex: 1.5, textAlign: 'center'}]}>Status</Text>
                </View>

                {/* Table Rows */}
                {reportData.transactions.map((txn: any, index: number) => (
                  <View key={index} style={styles.tableRow}>
                    <Text style={[styles.tableCell, {flex: 1.5}]}>
                      {txn.date}
                    </Text>
                    <Text style={[styles.tableCell, {flex: 3}]} numberOfLines={2}>
                      {txn.description}
                    </Text>
                    <Text style={[styles.tableCell, {flex: 1.5, textAlign: 'right', fontWeight: '600'}]}>
                      {formatCurrency(txn.amount)}
                    </Text>
                    <View style={[styles.tableCell, {flex: 1.5, alignItems: 'center'}]}>
                      <View style={[styles.statusBadge, {backgroundColor: getStatusColor(txn.status)}]}>
                        <Icon name={getStatusIcon(txn.status)} size={12} color="#FFF" />
                        <Text style={styles.statusText}>{txn.status}</Text>
                      </View>
                    </View>
                  </View>
                ))}
              </View>
            </View>
          ) : (
            <View style={styles.emptyState}>
              <Icon name="document-text-outline" size={60} color="#CCC" />
              <Text style={styles.emptyText}>No transactions found</Text>
              <Text style={styles.emptySubtext}>
                for the selected period
              </Text>
            </View>
          )}
        </ScrollView>
      ) : selectedFlat ? (
        <View style={styles.emptyState}>
          <Icon name="document-text-outline" size={60} color="#CCC" />
          <Text style={styles.emptyText}>No Report Generated</Text>
          <Text style={styles.emptySubtext}>
            Click Generate Report to view transactions
          </Text>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  selectorContainer: {
    backgroundColor: '#FFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  selectorLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  flatChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F0F0F0',
    marginRight: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  flatChipSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  flatChipText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  flatChipTextSelected: {
    color: '#FFF',
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
    fontSize: 12,
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
    fontSize: 12,
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
  memberCard: {
    backgroundColor: '#FFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  memberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  memberInfo: {
    marginLeft: 12,
    flex: 1,
  },
  memberLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  memberValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  summaryContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 16,
    flexWrap: 'wrap',
  },
  summaryCard: {
    flex: 1,
    minWidth: '30%',
    backgroundColor: '#FFF',
    padding: 12,
    marginHorizontal: 4,
    marginBottom: 8,
    borderRadius: 12,
    borderLeftWidth: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  summaryLabel: {
    fontSize: 11,
    color: '#666',
    marginBottom: 4,
  },
  summaryAmount: {
    fontSize: 16,
    fontWeight: 'bold',
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
    alignItems: 'center',
  },
  tableCell: {
    fontSize: 12,
    color: '#333',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 10,
    color: '#FFF',
    fontWeight: '600',
    marginLeft: 4,
    textTransform: 'uppercase',
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

export default MemberTransactionLedgerScreen;



import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
  TextInput,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import {maintenanceService, MaintenanceBill} from '../../services/maintenanceService';
import {formatCurrency} from '../../utils/maintenanceCalculations';
import {authService} from '../../services/authService';

const BillHistoryScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [bills, setBills] = useState<MaintenanceBill[]>([]);
  const [filteredBills, setFilteredBills] = useState<MaintenanceBill[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [deleting, setDeleting] = useState<{[key: string]: boolean}>({});
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [showMonthPicker, setShowMonthPicker] = useState(false);
  const [showYearPicker, setShowYearPicker] = useState(false);
  
  // Filter UI state
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    checkAdminStatus();
    loadBills();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [bills, searchQuery, selectedMonth, selectedYear, selectedStatus]);

  const checkAdminStatus = async () => {
    try {
      const user = await authService.getStoredUser();
      setIsAdmin(user?.role === 'admin' || user?.role === 'super_admin');
    } catch (error) {
      console.error('Error checking admin status:', error);
      setIsAdmin(false);
    }
  };

  const loadBills = async () => {
    setLoading(true);
    try {
      const billsData = await maintenanceService.getBills();
      setBills(billsData);
      setFilteredBills(billsData);
    } catch (error: any) {
      console.error('Error loading bills:', error);
      Alert.alert('Error', error.message || 'Failed to load bills');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadBills();
    setRefreshing(false);
  };

  const applyFilters = () => {
    let filtered = [...bills];

    // Search filter (flat number or member name)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        bill =>
          bill.flat_number?.toLowerCase().includes(query) ||
          bill.member_name?.toLowerCase().includes(query)
      );
    }

    // Month filter
    if (selectedMonth !== null) {
      filtered = filtered.filter(bill => bill.month === selectedMonth);
    }

    // Year filter
    if (selectedYear !== null) {
      filtered = filtered.filter(bill => bill.year === selectedYear);
    }

    // Status filter
    if (selectedStatus) {
      filtered = filtered.filter(bill => bill.status === selectedStatus);
    }

    setFilteredBills(filtered);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedMonth(null);
    setSelectedYear(null);
    setSelectedStatus(null);
  };

  const handleDeleteBills = async (month: number, year: number) => {
    const monthYearKey = `${year}-${month}`;
    const monthName = formatMonthYear(month, year);
    
    Alert.alert(
      'Delete Bills',
      `Are you sure you want to delete all bills for ${monthName}?\n\nThis action cannot be undone. You can regenerate bills after deletion.`,
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            setDeleting(prev => ({...prev, [monthYearKey]: true}));
            try {
              await maintenanceService.deleteBillsForMonth(month, year);
              await loadBills();
              Alert.alert(
                'Success',
                `Bills for ${monthName} deleted successfully. You can now regenerate them with the correct calculation.`,
                [
                  {
                    text: 'Regenerate',
                    onPress: () => {
                      // Navigate and refresh GenerateBills screen
                      navigation.navigate('GenerateBills');
                      // Force refresh by navigating away and back
                      setTimeout(() => {
                        navigation.navigate('GenerateBills');
                      }, 100);
                    },
                  },
                  {text: 'OK'},
                ],
              );
            } catch (error: any) {
              console.error('Error deleting bills:', error);
              Alert.alert(
                'Error',
                error.response?.data?.detail || 'Failed to delete bills. Please try again.',
              );
            } finally {
              setDeleting(prev => {
                const newState = {...prev};
                delete newState[monthYearKey];
                return newState;
              });
            }
          },
        },
      ],
    );
  };

  // Group bills by month/year for display
  const groupBillsByMonth = () => {
    const grouped: {[key: string]: MaintenanceBill[]} = {};
    filteredBills.forEach(bill => {
      const key = `${bill.year}-${bill.month}`;
      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key].push(bill);
    });
    return grouped;
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'paid':
        return '#4CAF50';
      case 'unpaid':
        return '#F44336';
      default:
        return '#FF9800';
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

  const formatMonthYear = (month: number, year: number) => {
    const monthNames = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];
    return `${monthNames[month - 1]} ${year}`;
  };

  const handleDownloadPDF = async (billId: string, flatNumber: string) => {
    try {
      await maintenanceService.downloadBillPDF(billId);
      Alert.alert(
        'Download Started',
        `Downloading bill for ${flatNumber}. Check your downloads folder.`,
        [{text: 'OK'}]
      );
    } catch (error: any) {
      console.error('Error downloading PDF:', error);
      Alert.alert(
        'Download Error',
        error?.response?.data?.detail || 'Failed to download bill PDF. Please try again.',
        [{text: 'OK'}]
      );
    }
  };

  const renderBillItem = ({item}: {item: MaintenanceBill}) => (
    <View style={styles.billCard}>
      <TouchableOpacity
        onPress={() => {
          // Show bill details
          Alert.alert('Bill Details', `Bill for ${item.flat_number}\nAmount: ${formatCurrency(item.amount)}`);
        }}>
        <View style={styles.billHeader}>
          <View style={styles.billHeaderLeft}>
            <Text style={styles.flatNumber}>{item.flat_number}</Text>
            <Text style={styles.billDate}>{formatMonthYear(item.month, item.year)}</Text>
          </View>
          <View
            style={[
              styles.statusBadge,
              {backgroundColor: getStatusColor(item.status || '')},
            ]}>
            <Icon
              name={getStatusIcon(item.status || '')}
              size={14}
              color="#FFF"
              style={styles.statusIcon}
            />
            <Text style={styles.statusText}>
              {item.status?.toUpperCase() || 'UNKNOWN'}
            </Text>
          </View>
        </View>

        <View style={styles.billBody}>
          <View style={styles.billRow}>
            <Text style={styles.billLabel}>Amount:</Text>
            <Text style={styles.billAmount}>{formatCurrency(item.amount)}</Text>
          </View>
          {item.member_name && (
            <View style={styles.billRow}>
              <Text style={styles.billLabel}>Member:</Text>
              <Text style={styles.billValue}>{item.member_name}</Text>
            </View>
          )}
          {item.bill_number && (
            <View style={styles.billRow}>
              <Text style={styles.billLabel}>Bill No:</Text>
              <Text style={styles.billValue}>{item.bill_number}</Text>
            </View>
          )}
          {item.paid_at && (
            <View style={styles.billRow}>
              <Text style={styles.billLabel}>Paid On:</Text>
              <Text style={styles.billValue}>
                {new Date(item.paid_at).toLocaleDateString()}
              </Text>
            </View>
          )}
        </View>
      </TouchableOpacity>

      {/* Download PDF Button */}
      <TouchableOpacity
        style={styles.downloadButton}
        onPress={() => handleDownloadPDF(item.id, item.flat_number)}
        activeOpacity={0.7}>
        <Icon name="download-outline" size={18} color="#FFF" />
        <Text style={styles.downloadButtonText}>Download PDF</Text>
      </TouchableOpacity>
    </View>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="receipt-outline" size={64} color="#C7C7CC" />
      <Text style={styles.emptyStateText}>No bills found</Text>
      <Text style={styles.emptyStateSubtext}>
        {bills.length === 0
          ? 'No bills have been generated yet'
          : 'Try adjusting your filters'}
      </Text>
    </View>
  );

  const hasActiveFilters =
    searchQuery.trim() !== '' ||
    selectedMonth !== null ||
    selectedYear !== null ||
    selectedStatus !== null;

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading bills...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header with Search and Filters */}
      <View style={styles.header}>
        <View style={styles.searchContainer}>
          <Icon name="search" size={20} color="#666" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search by flat number or member name..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor="#999"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity
              onPress={() => setSearchQuery('')}
              style={styles.clearButton}>
              <Icon name="close-circle" size={20} color="#999" />
            </TouchableOpacity>
          )}
        </View>

        <TouchableOpacity
          style={[styles.filterButton, hasActiveFilters && styles.filterButtonActive]}
          onPress={() => setShowFilters(!showFilters)}>
          <Icon
            name="filter"
            size={20}
            color={hasActiveFilters ? '#FFF' : '#007AFF'}
          />
          <Text
            style={[
              styles.filterButtonText,
              hasActiveFilters && styles.filterButtonTextActive,
            ]}>
            Filters
          </Text>
          {hasActiveFilters && (
            <View style={styles.filterBadge}>
              <Text style={styles.filterBadgeText}>
                {[
                  searchQuery ? 1 : 0,
                  selectedMonth ? 1 : 0,
                  selectedYear ? 1 : 0,
                  selectedStatus ? 1 : 0,
                ].reduce((a, b) => a + b, 0)}
              </Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Filter Panel */}
      {showFilters && (
        <View style={styles.filterPanel}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.filterRow}>
              {/* Month Filter */}
              <TouchableOpacity
                style={[
                  styles.filterChip,
                  selectedMonth !== null && styles.filterChipActive,
                ]}
                onPress={() => setShowMonthPicker(true)}>
                <Icon
                  name="calendar"
                  size={16}
                  color={selectedMonth !== null ? '#FFF' : '#007AFF'}
                />
                <Text
                  style={[
                    styles.filterChipText,
                    selectedMonth !== null && styles.filterChipTextActive,
                  ]}>
                  {selectedMonth
                    ? `Month: ${selectedMonth}`
                    : 'Select Month'}
                </Text>
                {selectedMonth !== null && (
                  <TouchableOpacity
                    onPress={e => {
                      e.stopPropagation();
                      setSelectedMonth(null);
                    }}
                    style={styles.filterChipClose}>
                    <Icon name="close" size={14} color="#FFF" />
                  </TouchableOpacity>
                )}
              </TouchableOpacity>

              {/* Year Filter */}
              <TouchableOpacity
                style={[
                  styles.filterChip,
                  selectedYear !== null && styles.filterChipActive,
                ]}
                onPress={() => setShowYearPicker(true)}>
                <Icon
                  name="calendar-outline"
                  size={16}
                  color={selectedYear !== null ? '#FFF' : '#007AFF'}
                />
                <Text
                  style={[
                    styles.filterChipText,
                    selectedYear !== null && styles.filterChipTextActive,
                  ]}>
                  {selectedYear ? `Year: ${selectedYear}` : 'Select Year'}
                </Text>
                {selectedYear !== null && (
                  <TouchableOpacity
                    onPress={e => {
                      e.stopPropagation();
                      setSelectedYear(null);
                    }}
                    style={styles.filterChipClose}>
                    <Icon name="close" size={14} color="#FFF" />
                  </TouchableOpacity>
                )}
              </TouchableOpacity>

              {/* Status Filter */}
              <TouchableOpacity
                style={[
                  styles.filterChip,
                  selectedStatus !== null && styles.filterChipActive,
                ]}
                onPress={() => {
                  if (selectedStatus === null) {
                    setSelectedStatus('unpaid');
                  } else if (selectedStatus === 'unpaid') {
                    setSelectedStatus('paid');
                  } else {
                    setSelectedStatus(null);
                  }
                }}>
                <Icon
                  name="checkmark-circle-outline"
                  size={16}
                  color={selectedStatus !== null ? '#FFF' : '#007AFF'}
                />
                <Text
                  style={[
                    styles.filterChipText,
                    selectedStatus !== null && styles.filterChipTextActive,
                  ]}>
                  {selectedStatus
                    ? `Status: ${selectedStatus.toUpperCase()}`
                    : 'Select Status'}
                </Text>
                {selectedStatus !== null && (
                  <TouchableOpacity
                    onPress={e => {
                      e.stopPropagation();
                      setSelectedStatus(null);
                    }}
                    style={styles.filterChipClose}>
                    <Icon name="close" size={14} color="#FFF" />
                  </TouchableOpacity>
                )}
              </TouchableOpacity>

              {/* Clear All */}
              {hasActiveFilters && (
                <TouchableOpacity
                  style={styles.clearFiltersButton}
                  onPress={clearFilters}>
                  <Icon name="close-circle" size={16} color="#F44336" />
                  <Text style={styles.clearFiltersText}>Clear All</Text>
                </TouchableOpacity>
              )}
            </View>
          </ScrollView>
        </View>
      )}

      {/* Total Summary */}
      {filteredBills.length > 0 && (
        <View style={styles.summaryContainer}>
          <View style={styles.summaryCard}>
            <View style={styles.summaryRow}>
              <Icon name="receipt" size={24} color="#007AFF" />
              <View style={styles.summaryContent}>
                <Text style={styles.summaryLabel}>Total Bills</Text>
                <Text style={styles.summaryCount}>{filteredBills.length} bills</Text>
              </View>
              <View style={styles.summaryAmountContainer}>
                <Text style={styles.summaryAmount}>
                  {formatCurrency(
                    filteredBills.reduce((sum, bill) => sum + (bill.amount || 0), 0)
                  )}
                </Text>
                <Text style={styles.summarySubtext}>Total Amount</Text>
              </View>
            </View>
          </View>
        </View>
      )}

      {/* Bills List - Grouped by Month/Year */}
      {filteredBills.length > 0 ? (
        <ScrollView>
          {Object.entries(groupBillsByMonth())
            .sort(([a], [b]) => b.localeCompare(a)) // Sort by year-month descending
            .map(([key, monthBills]) => {
              const [year, month] = key.split('-').map(Number);
              const monthName = formatMonthYear(month, year);
              const monthTotal = monthBills.reduce((sum, bill) => sum + (bill.amount || 0), 0);
              const monthYearKey = `${year}-${month}`;
              const isDeletingMonth = deleting[monthYearKey];

              return (
                <View key={key} style={styles.monthGroup}>
                  <View style={styles.monthHeader}>
                    <View style={styles.monthHeaderLeft}>
                      <Icon name="calendar" size={20} color="#007AFF" />
                      <View style={styles.monthHeaderText}>
                        <Text style={styles.monthTitle}>{monthName}</Text>
                        <Text style={styles.monthSubtitle}>
                          {monthBills.length} bills • {formatCurrency(monthTotal)}
                        </Text>
                      </View>
                    </View>
                    {isAdmin && (
                      <TouchableOpacity
                        style={styles.deleteMonthButton}
                        onPress={() => handleDeleteBills(month, year)}
                        disabled={isDeletingMonth}
                        activeOpacity={0.7}>
                        {isDeletingMonth ? (
                          <ActivityIndicator size="small" color="#F44336" />
                        ) : (
                          <Icon name="trash-outline" size={20} color="#F44336" />
                        )}
                      </TouchableOpacity>
                    )}
                  </View>
                  {monthBills.map((bill, index) => (
                    <View key={`${bill.id}-${index}`}>
                      {renderBillItem({item: bill})}
                    </View>
                  ))}
                </View>
              );
            })}
        </ScrollView>
      ) : (
        <View style={styles.emptyList}>
          {renderEmptyState()}
        </View>
      )}

      {/* Date Pickers */}
      {showMonthPicker && (
        <View style={styles.pickerContainer}>
          <ScrollView>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(month => (
              <TouchableOpacity
                key={month}
                style={[
                  styles.pickerOption,
                  selectedMonth === month && styles.pickerOptionActive,
                ]}
                onPress={() => {
                  setSelectedMonth(month);
                  setShowMonthPicker(false);
                }}>
                <Text
                  style={[
                    styles.pickerOptionText,
                    selectedMonth === month && styles.pickerOptionTextActive,
                  ]}>
                  {new Date(2000, month - 1).toLocaleString('default', {
                    month: 'long',
                  })}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
          <TouchableOpacity
            style={styles.pickerClose}
            onPress={() => setShowMonthPicker(false)}>
            <Text style={styles.pickerCloseText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      )}

      {showYearPicker && (
        <View style={styles.pickerContainer}>
          <ScrollView>
            {Array.from({length: 10}, (_, i) => new Date().getFullYear() - i).map(
              year => (
                <TouchableOpacity
                  key={year}
                  style={[
                    styles.pickerOption,
                    selectedYear === year && styles.pickerOptionActive,
                  ]}
                  onPress={() => {
                    setSelectedYear(year);
                    setShowYearPicker(false);
                  }}>
                  <Text
                    style={[
                      styles.pickerOptionText,
                      selectedYear === year && styles.pickerOptionTextActive,
                    ]}>
                    {year}
                  </Text>
                </TouchableOpacity>
              )
            )}
          </ScrollView>
          <TouchableOpacity
            style={styles.pickerClose}
            onPress={() => setShowYearPicker(false)}>
            <Text style={styles.pickerCloseText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  summaryContainer: {
    padding: 15,
    backgroundColor: '#F5F5F7',
  },
  summaryCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  summaryContent: {
    flex: 1,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  summaryCount: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  summaryAmountContainer: {
    alignItems: 'flex-end',
  },
  summaryAmount: {
    fontSize: 24,
    fontWeight: '700',
    color: '#007AFF',
    marginBottom: 4,
  },
  summarySubtext: {
    fontSize: 12,
    color: '#666',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },
  header: {
    backgroundColor: '#FFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    flexDirection: 'row',
    gap: 12,
  },
  searchContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
    borderRadius: 12,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: '#1D1D1F',
    paddingVertical: 10,
  },
  clearButton: {
    padding: 4,
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#007AFF',
    gap: 6,
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
  },
  filterButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  filterButtonTextActive: {
    color: '#FFF',
  },
  filterBadge: {
    backgroundColor: '#F44336',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 6,
  },
  filterBadgeText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: '700',
  },
  filterPanel: {
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    paddingVertical: 12,
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 8,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#007AFF',
    gap: 6,
  },
  filterChipActive: {
    backgroundColor: '#007AFF',
  },
  filterChipText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#007AFF',
  },
  filterChipTextActive: {
    color: '#FFF',
  },
  filterChipClose: {
    marginLeft: 4,
    padding: 2,
  },
  clearFiltersButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#F44336',
    gap: 6,
  },
  clearFiltersText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#F44336',
  },
  list: {
    padding: 16,
  },
  emptyList: {
    flexGrow: 1,
  },
  monthGroup: {
    marginBottom: 20,
    backgroundColor: '#F5F5F7',
  },
  monthHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFF',
    padding: 15,
    borderBottomWidth: 2,
    borderBottomColor: '#007AFF',
    marginBottom: 1,
  },
  monthHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  monthHeaderText: {
    flex: 1,
  },
  monthTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  monthSubtitle: {
    fontSize: 14,
    color: '#666',
  },
  deleteMonthButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#FFEBEE',
  },
  billCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  billHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  billHeaderLeft: {
    flex: 1,
  },
  flatNumber: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  billDate: {
    fontSize: 13,
    color: '#8E8E93',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 4,
  },
  statusIcon: {
    marginRight: 2,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFF',
  },
  billBody: {
    gap: 8,
    marginBottom: 12,
  },
  billRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  billLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  billAmount: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  billValue: {
    fontSize: 14,
    color: '#1D1D1F',
    fontWeight: '500',
  },
  downloadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#DC3545',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginTop: 4,
    gap: 6,
  },
  downloadButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
  pickerContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '50%',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: -2},
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
  pickerOption: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  pickerOptionActive: {
    backgroundColor: '#E3F2FD',
  },
  pickerOptionText: {
    fontSize: 16,
    color: '#1D1D1F',
  },
  pickerOptionTextActive: {
    color: '#007AFF',
    fontWeight: '600',
  },
  pickerClose: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    alignItems: 'center',
  },
  pickerCloseText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
});

export default BillHistoryScreen;


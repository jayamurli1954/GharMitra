import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Modal,
  TextInput,
  Platform,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import {
  financialYearService,
  FinancialYear,
  FinancialYearCreate,
  YearEndClosingRequest,
} from '../../services/financialYearService';

const FinancialYearScreen = ({navigation}: any) => {
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showClosingModal, setShowClosingModal] = useState(false);
  const [selectedYear, setSelectedYear] = useState<FinancialYear | null>(null);

  // Create form state
  const [yearName, setYearName] = useState('');
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [showStartDatePicker, setShowStartDatePicker] = useState(false);
  const [showEndDatePicker, setShowEndDatePicker] = useState(false);

  // Closing form state
  const [closingNotes, setClosingNotes] = useState('');
  const [confirmClosure, setConfirmClosure] = useState(false);

  useEffect(() => {
    loadFinancialYears();
  }, []);

  const loadFinancialYears = async () => {
    setLoading(true);
    try {
      const years = await financialYearService.getFinancialYears(true);
      setFinancialYears(years);
    } catch (error: any) {
      console.error('Error loading financial years:', error);
      Alert.alert('Error', 'Failed to load financial years');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadFinancialYears();
  };

  const handleCreateYear = async () => {
    if (!yearName.trim()) {
      Alert.alert('Validation Error', 'Please enter a year name');
      return;
    }

    if (endDate <= startDate) {
      Alert.alert('Validation Error', 'End date must be after start date');
      return;
    }

    try {
      const yearData: FinancialYearCreate = {
        year_name: yearName.trim(),
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
      };

      await financialYearService.createFinancialYear(yearData);
      Alert.alert('Success', 'Financial year created successfully');
      setShowCreateModal(false);
      resetCreateForm();
      loadFinancialYears();
    } catch (error: any) {
      console.error('Error creating financial year:', error);
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to create financial year'
      );
    }
  };

  const handleCloseYear = async () => {
    if (!selectedYear) return;

    if (!confirmClosure) {
      Alert.alert(
        'Confirmation Required',
        'Please check the confirmation box to proceed with year-end closing'
      );
      return;
    }

    try {
      const closingRequest: YearEndClosingRequest = {
        closing_notes: closingNotes.trim() || undefined,
        confirm_closure: true,
      };

      const summary = await financialYearService.closeFinancialYear(
        selectedYear.id,
        closingRequest
      );

      Alert.alert(
        'Year-End Closing Complete',
        `${summary.message}\n\n` +
          `Total Income: ₹${summary.total_income.toLocaleString()}\n` +
          `Total Expenses: ₹${summary.total_expenses.toLocaleString()}\n` +
          `Net Surplus/Deficit: ₹${summary.net_surplus_deficit.toLocaleString()}\n\n` +
          `Bank Balance: ₹${summary.bank_balance.toLocaleString()}\n` +
          `Cash Balance: ₹${summary.cash_balance.toLocaleString()}`,
        [{text: 'OK', onPress: () => {
          setShowClosingModal(false);
          resetClosingForm();
          loadFinancialYears();
        }}]
      );
    } catch (error: any) {
      console.error('Error closing financial year:', error);
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to close financial year'
      );
    }
  };

  const handleReopenYear = async (year: FinancialYear) => {
    Alert.alert(
      'Reopen Financial Year?',
      `Are you sure you want to reopen ${year.year_name}? This will allow modifications to closed accounts.`,
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Reopen',
          style: 'destructive',
          onPress: async () => {
            try {
              await financialYearService.reopenFinancialYear(year.id);
              Alert.alert('Success', 'Financial year reopened successfully');
              loadFinancialYears();
            } catch (error: any) {
              console.error('Error reopening financial year:', error);
              Alert.alert(
                'Error',
                error.response?.data?.detail || 'Failed to reopen financial year'
              );
            }
          },
        },
      ]
    );
  };

  const handleDeleteYear = async (year: FinancialYear) => {
    Alert.alert(
      'Delete Financial Year?',
      `Are you sure you want to delete ${year.year_name}? This action cannot be undone.`,
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await financialYearService.deleteFinancialYear(year.id);
              Alert.alert('Success', 'Financial year deleted successfully');
              loadFinancialYears();
            } catch (error: any) {
              console.error('Error deleting financial year:', error);
              Alert.alert(
                'Error',
                error.response?.data?.detail || 'Failed to delete financial year'
              );
            }
          },
        },
      ]
    );
  };

  const resetCreateForm = () => {
    setYearName('');
    setStartDate(new Date());
    setEndDate(new Date());
  };

  const resetClosingForm = () => {
    setSelectedYear(null);
    setClosingNotes('');
    setConfirmClosure(false);
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`;
  };

  const renderYearCard = (year: FinancialYear) => (
    <View key={year.id} style={styles.yearCard}>
      <View style={styles.yearHeader}>
        <View style={styles.yearTitleContainer}>
          <Text style={styles.yearName}>{year.year_name}</Text>
          <View style={styles.badgeContainer}>
            {year.is_active && (
              <View style={styles.activeBadge}>
                <Text style={styles.activeBadgeText}>Active</Text>
              </View>
            )}
            {year.is_closed && (
              <View style={styles.closedBadge}>
                <Icon name="lock-closed" size={12} color="#FFF" />
                <Text style={styles.closedBadgeText}>Closed</Text>
              </View>
            )}
          </View>
        </View>
      </View>

      <View style={styles.yearDetails}>
        <View style={styles.dateRow}>
          <Icon name="calendar-outline" size={16} color="#8E8E93" />
          <Text style={styles.dateText}>
            {new Date(year.start_date).toLocaleDateString()} -{' '}
            {new Date(year.end_date).toLocaleDateString()}
          </Text>
        </View>

        {year.is_closed && year.total_income !== undefined && (
          <View style={styles.closingSummary}>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Total Income:</Text>
              <Text style={[styles.summaryValue, {color: '#4CAF50'}]}>
                {formatCurrency(year.total_income)}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Total Expenses:</Text>
              <Text style={[styles.summaryValue, {color: '#F44336'}]}>
                {formatCurrency(year.total_expenses || 0)}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Surplus/Deficit:</Text>
              <Text
                style={[
                  styles.summaryValue,
                  {
                    color:
                      (year.net_surplus_deficit || 0) >= 0 ? '#4CAF50' : '#F44336',
                  },
                ]}>
                {formatCurrency(year.net_surplus_deficit || 0)}
              </Text>
            </View>
          </View>
        )}
      </View>

      <View style={styles.yearActions}>
        {!year.is_closed && year.is_active && (
          <TouchableOpacity
            style={[styles.actionButton, styles.closeButton]}
            onPress={() => {
              setSelectedYear(year);
              setShowClosingModal(true);
            }}>
            <Icon name="lock-closed" size={16} color="#FFF" />
            <Text style={styles.actionButtonText}>Close Year</Text>
          </TouchableOpacity>
        )}
        {year.is_closed && (
          <TouchableOpacity
            style={[styles.actionButton, styles.reopenButton]}
            onPress={() => handleReopenYear(year)}>
            <Icon name="lock-open" size={16} color="#FFF" />
            <Text style={styles.actionButtonText}>Reopen</Text>
          </TouchableOpacity>
        )}
        {!year.is_closed && !year.is_active && (
          <TouchableOpacity
            style={[styles.actionButton, styles.deleteButton]}
            onPress={() => handleDeleteYear(year)}>
            <Icon name="trash" size={16} color="#FFF" />
            <Text style={styles.actionButtonText}>Delete</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading financial years...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }>
        {/* Header */}
        <View style={styles.header}>
          <Icon name="calendar" size={32} color="#007AFF" />
          <Text style={styles.headerTitle}>Financial Years</Text>
          <Text style={styles.headerSubtitle}>
            Manage year-wise accounting and year-end closing
          </Text>
        </View>

        {/* Create Button */}
        <TouchableOpacity
          style={styles.createButton}
          onPress={() => setShowCreateModal(true)}>
          <Icon name="add-circle" size={24} color="#FFF" />
          <Text style={styles.createButtonText}>Create New Financial Year</Text>
        </TouchableOpacity>

        {/* Financial Years List */}
        {financialYears.length === 0 ? (
          <View style={styles.emptyState}>
            <Icon name="calendar-outline" size={64} color="#C7C7CC" />
            <Text style={styles.emptyStateText}>No financial years found</Text>
            <Text style={styles.emptyStateSubtext}>
              Create your first financial year to start managing accounts
            </Text>
          </View>
        ) : (
          <View style={styles.yearsList}>{financialYears.map(renderYearCard)}</View>
        )}
      </ScrollView>

      {/* Create Year Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowCreateModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create Financial Year</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Icon name="close" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Year Name *</Text>
                <TextInput
                  style={styles.textInput}
                  value={yearName}
                  onChangeText={setYearName}
                  placeholder="e.g., 2024-2025 or FY 2024-25"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Start Date *</Text>
                <TouchableOpacity
                  style={styles.dateInput}
                  onPress={() => setShowStartDatePicker(true)}>
                  <Text style={styles.dateInputText}>
                    {startDate.toLocaleDateString()}
                  </Text>
                  <Icon name="calendar-outline" size={20} color="#007AFF" />
                </TouchableOpacity>
                {showStartDatePicker && (
                  <DateTimePicker
                    value={startDate}
                    mode="date"
                    display="default"
                    onChange={(event, date) => {
                      setShowStartDatePicker(Platform.OS === 'ios');
                      if (date) setStartDate(date);
                    }}
                  />
                )}
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>End Date *</Text>
                <TouchableOpacity
                  style={styles.dateInput}
                  onPress={() => setShowEndDatePicker(true)}>
                  <Text style={styles.dateInputText}>
                    {endDate.toLocaleDateString()}
                  </Text>
                  <Icon name="calendar-outline" size={20} color="#007AFF" />
                </TouchableOpacity>
                {showEndDatePicker && (
                  <DateTimePicker
                    value={endDate}
                    mode="date"
                    display="default"
                    onChange={(event, date) => {
                      setShowEndDatePicker(Platform.OS === 'ios');
                      if (date) setEndDate(date);
                    }}
                  />
                )}
              </View>

              <View style={styles.modalActions}>
                <TouchableOpacity
                  style={[styles.modalButton, styles.cancelButton]}
                  onPress={() => setShowCreateModal(false)}>
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.modalButton, styles.submitButton]}
                  onPress={handleCreateYear}>
                  <Text style={styles.submitButtonText}>Create</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Year-End Closing Modal */}
      <Modal
        visible={showClosingModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowClosingModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                Year-End Closing: {selectedYear?.year_name}
              </Text>
              <TouchableOpacity onPress={() => setShowClosingModal(false)}>
                <Icon name="close" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.warningBox}>
                <Icon name="warning" size={24} color="#FF9800" />
                <Text style={styles.warningText}>
                  Year-end closing is a critical operation. Once closed, the year will
                  be locked and no further modifications can be made without reopening.
                </Text>
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Closing Notes (Optional)</Text>
                <TextInput
                  style={[styles.textInput, styles.textArea]}
                  value={closingNotes}
                  onChangeText={setClosingNotes}
                  placeholder="Enter any notes about this year-end closing"
                  multiline
                  numberOfLines={4}
                />
              </View>

              <TouchableOpacity
                style={styles.checkboxContainer}
                onPress={() => setConfirmClosure(!confirmClosure)}>
                <View
                  style={[
                    styles.checkbox,
                    confirmClosure && styles.checkboxChecked,
                  ]}>
                  {confirmClosure && <Icon name="checkmark" size={16} color="#FFF" />}
                </View>
                <Text style={styles.checkboxLabel}>
                  I confirm that I want to close this financial year
                </Text>
              </TouchableOpacity>

              <View style={styles.modalActions}>
                <TouchableOpacity
                  style={[styles.modalButton, styles.cancelButton]}
                  onPress={() => setShowClosingModal(false)}>
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.modalButton,
                    styles.submitButton,
                    !confirmClosure && styles.disabledButton,
                  ]}
                  onPress={handleCloseYear}
                  disabled={!confirmClosure}>
                  <Icon name="lock-closed" size={16} color="#FFF" />
                  <Text style={styles.submitButtonText}>Close Year</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#8E8E93',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1D1D1F',
    marginTop: 12,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginTop: 4,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    marginHorizontal: 16,
    marginVertical: 16,
    paddingVertical: 14,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  createButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  yearsList: {
    padding: 16,
  },
  yearCard: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  yearHeader: {
    marginBottom: 12,
  },
  yearTitleContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  yearName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1D1D1F',
  },
  badgeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  activeBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginLeft: 8,
  },
  activeBadgeText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  closedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#8E8E93',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginLeft: 8,
  },
  closedBadgeText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold',
    marginLeft: 4,
  },
  yearDetails: {
    marginBottom: 12,
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  dateText: {
    fontSize: 14,
    color: '#8E8E93',
    marginLeft: 8,
  },
  closingSummary: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  summaryValue: {
    fontSize: 15,
    fontWeight: 'bold',
  },
  yearActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    marginLeft: 8,
  },
  closeButton: {
    backgroundColor: '#FF9800',
  },
  reopenButton: {
    backgroundColor: '#2196F3',
  },
  deleteButton: {
    backgroundColor: '#F44336',
  },
  actionButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1D1D1F',
    marginTop: 16,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 32,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1D1D1F',
  },
  modalBody: {
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: '#1D1D1F',
    borderWidth: 1,
    borderColor: '#E5E5E5',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  dateInput: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E5E5E5',
  },
  dateInputText: {
    fontSize: 16,
    color: '#1D1D1F',
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFF8E1',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  warningText: {
    flex: 1,
    fontSize: 14,
    color: '#856404',
    marginLeft: 12,
    lineHeight: 20,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  checkboxChecked: {
    backgroundColor: '#007AFF',
  },
  checkboxLabel: {
    flex: 1,
    fontSize: 14,
    color: '#1D1D1F',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  modalButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    marginHorizontal: 6,
  },
  cancelButton: {
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#E5E5E5',
  },
  cancelButtonText: {
    color: '#8E8E93',
    fontSize: 16,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#007AFF',
  },
  submitButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 6,
  },
  disabledButton: {
    opacity: 0.5,
  },
});

export default FinancialYearScreen;


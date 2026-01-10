import React, {useEffect, useState, useCallback} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {useNavigation} from '@react-navigation/native';
import {
  financialYearService,
  FinancialYear,
} from '../../services/financialYearService';
import {spacing} from '../../constants/spacing';
import {formatDate, formatCurrency} from '../../utils/formatters';

const FinancialYearManagementScreen: React.FC = () => {
  const navigation = useNavigation();
  const [years, setYears] = useState<FinancialYear[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showProvisionalModal, setShowProvisionalModal] = useState(false);
  const [showFinalModal, setShowFinalModal] = useState(false);
  const [selectedYear, setSelectedYear] = useState<FinancialYear | null>(null);
  const [closingNotes, setClosingNotes] = useState('');

  const loadYears = useCallback(async () => {
    try {
      setLoading(true);
      const data = await financialYearService.getFinancialYears();
      setYears(data);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to load financial years');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadYears();
  }, [loadYears]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadYears();
  }, [loadYears]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return '#34C759';
      case 'provisional_close':
        return '#FF9500';
      case 'final_close':
        return '#FF3B30';
      default:
        return '#8E8E93';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'open':
        return 'Open';
      case 'provisional_close':
        return 'Under Audit';
      case 'final_close':
        return 'Locked';
      default:
        return status;
    }
  };

  const handleProvisionalClose = async () => {
    if (!selectedYear) return;

    Alert.alert(
      'Confirm Provisional Closing',
      `This will provisionally close ${selectedYear.year_name}. The year will be locked for audit but adjustments can still be posted.\n\nAre you sure?`,
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Yes, Close',
          style: 'destructive',
          onPress: async () => {
            try {
              const result = await financialYearService.provisionalCloseYear(
                selectedYear.id,
                {
                  closing_date: new Date().toISOString().split('T')[0],
                  notes: closingNotes,
                },
              );
              Alert.alert('Success', result.message);
              setShowProvisionalModal(false);
              setClosingNotes('');
              setSelectedYear(null);
              loadYears();
            } catch (error: any) {
              Alert.alert('Error', error.message || 'Failed to close year');
            }
          },
        },
      ],
    );
  };

  const handleFinalClose = async () => {
    if (!selectedYear) return;

    navigation.navigate('FinalCloseYear', {yearId: selectedYear.id});
    setShowFinalModal(false);
    setSelectedYear(null);
  };

  const handlePostAdjustment = (year: FinancialYear) => {
    navigation.navigate('PostAdjustmentEntry', {yearId: year.id});
  };

  const handleViewOpeningBalances = (year: FinancialYear) => {
    navigation.navigate('OpeningBalances', {yearId: year.id});
  };

  const renderYearCard = (year: FinancialYear) => {
    return (
      <View key={year.id} style={styles.yearCard}>
        {/* Header */}
        <View style={styles.yearHeader}>
          <View style={styles.yearTitleSection}>
            <Text style={styles.yearName}>{year.year_name}</Text>
            <View
              style={[
                styles.statusBadge,
                {backgroundColor: `${getStatusColor(year.status)}20`},
              ]}>
              <Icon
                name={
                  year.status === 'open'
                    ? 'checkmark-circle'
                    : year.status === 'provisional_close'
                    ? 'time'
                    : 'lock-closed'
                }
                size={14}
                color={getStatusColor(year.status)}
              />
              <Text
                style={[
                  styles.statusText,
                  {color: getStatusColor(year.status)},
                ]}>
                {getStatusLabel(year.status)}
              </Text>
            </View>
          </View>
          {year.is_active && (
            <View style={styles.activeBadge}>
              <Text style={styles.activeText}>Current</Text>
            </View>
          )}
        </View>

        {/* Dates */}
        <View style={styles.datesSection}>
          <Text style={styles.dateText}>
            {formatDate(year.start_date)} - {formatDate(year.end_date)}
          </Text>
        </View>

        {/* Financial Summary (if closed) */}
        {year.status !== 'open' && (
          <View style={styles.summarySection}>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Income:</Text>
              <Text style={styles.summaryValue}>
                {formatCurrency(year.total_income || 0)}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Expenses:</Text>
              <Text style={styles.summaryValue}>
                {formatCurrency(year.total_expenses || 0)}
              </Text>
            </View>
            <View style={[styles.summaryRow, styles.summaryRowLast]}>
              <Text style={styles.summaryLabelBold}>Net Position:</Text>
              <Text
                style={[
                  styles.summaryValueBold,
                  {
                    color:
                      (year.net_surplus_deficit || 0) >= 0
                        ? '#34C759'
                        : '#FF3B30',
                  },
                ]}>
                {formatCurrency(year.net_surplus_deficit || 0)}
              </Text>
            </View>
          </View>
        )}

        {/* Audit Information (if under audit or locked) */}
        {year.status === 'provisional_close' && (
          <View style={styles.auditSection}>
            <Icon name="shield-checkmark-outline" size={16} color="#FF9500" />
            <Text style={styles.auditText}>
              Under Audit - Opening balances are provisional
            </Text>
          </View>
        )}

        {year.status === 'final_close' && year.auditor_name && (
          <View style={styles.auditSection}>
            <Icon name="shield-checkmark" size={16} color="#34C759" />
            <Text style={styles.auditTextFinal}>
              Audited by {year.auditor_name} ({year.auditor_firm})
            </Text>
          </View>
        )}

        {/* Opening Balances Status */}
        <TouchableOpacity
          style={styles.openingBalancesButton}
          onPress={() => handleViewOpeningBalances(year)}>
          <Icon name="list-outline" size={18} color="#007AFF" />
          <Text style={styles.openingBalancesText}>
            Opening Balances:{' '}
            <Text
              style={{
                color:
                  year.opening_balances_status === 'finalized'
                    ? '#34C759'
                    : '#FF9500',
                fontWeight: '600',
              }}>
              {year.opening_balances_status === 'finalized'
                ? 'Finalized'
                : 'Provisional'}
            </Text>
          </Text>
          <Icon name="chevron-forward" size={18} color="#8E8E93" />
        </TouchableOpacity>

        {/* Action Buttons */}
        <View style={styles.actionsSection}>
          {year.status === 'open' && (
            <TouchableOpacity
              style={[styles.actionButton, styles.actionButtonWarning]}
              onPress={() => {
                setSelectedYear(year);
                setShowProvisionalModal(true);
              }}>
              <Icon name="lock-open-outline" size={18} color="#FF9500" />
              <Text style={[styles.actionButtonText, {color: '#FF9500'}]}>
                Provisional Close
              </Text>
            </TouchableOpacity>
          )}

          {year.status === 'provisional_close' && (
            <>
              <TouchableOpacity
                style={[styles.actionButton, styles.actionButtonPrimary]}
                onPress={() => handlePostAdjustment(year)}>
                <Icon name="create-outline" size={18} color="#007AFF" />
                <Text style={[styles.actionButtonText, {color: '#007AFF'}]}>
                  Post Adjustment
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.actionButtonDanger]}
                onPress={() => {
                  setSelectedYear(year);
                  setShowFinalModal(true);
                }}>
                <Icon name="lock-closed-outline" size={18} color="#FF3B30" />
                <Text style={[styles.actionButtonText, {color: '#FF3B30'}]}>
                  Final Close
                </Text>
              </TouchableOpacity>
            </>
          )}

          {year.status === 'final_close' && year.audit_report_file_url && (
            <TouchableOpacity
              style={[styles.actionButton, styles.actionButtonSuccess]}
              onPress={() => {
                // Open audit report
                Alert.alert('Audit Report', `URL: ${year.audit_report_file_url}`);
              }}>
              <Icon name="document-text-outline" size={18} color="#34C759" />
              <Text style={[styles.actionButtonText, {color: '#34C759'}]}>
                View Audit Report
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Financial Years</Text>
        <Text style={styles.subtitle}>
          Manage three-stage year-end closing workflow
        </Text>
      </View>

      {/* Workflow Info Card */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>Three-Stage Closing Process</Text>
        <View style={styles.stageRow}>
          <View style={styles.stageNumber}>
            <Text style={styles.stageNumberText}>1</Text>
          </View>
          <View style={styles.stageContent}>
            <Text style={styles.stageTitle}>Provisional Close</Text>
            <Text style={styles.stageDescription}>
              Lock year for audit, allow adjustments
            </Text>
          </View>
        </View>
        <View style={styles.stageRow}>
          <View style={styles.stageNumber}>
            <Text style={styles.stageNumberText}>2</Text>
          </View>
          <View style={styles.stageContent}>
            <Text style={styles.stageTitle}>Post Adjustments</Text>
            <Text style={styles.stageDescription}>
              Auditor posts correction entries
            </Text>
          </View>
        </View>
        <View style={styles.stageRow}>
          <View style={styles.stageNumber}>
            <Text style={styles.stageNumberText}>3</Text>
          </View>
          <View style={styles.stageContent}>
            <Text style={styles.stageTitle}>Final Close</Text>
            <Text style={styles.stageDescription}>
              Lock permanently after audit
            </Text>
          </View>
        </View>
      </View>

      {/* Years List */}
      {years.map(renderYearCard)}

      {/* Provisional Close Modal */}
      <Modal
        visible={showProvisionalModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowProvisionalModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Provisional Closing</Text>
            <Text style={styles.modalText}>
              Add any notes about this provisional closing:
            </Text>
            <TextInput
              style={styles.modalInput}
              placeholder="Optional notes..."
              value={closingNotes}
              onChangeText={setClosingNotes}
              multiline
              numberOfLines={4}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonCancel]}
                onPress={() => {
                  setShowProvisionalModal(false);
                  setClosingNotes('');
                  setSelectedYear(null);
                }}>
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonConfirm]}
                onPress={handleProvisionalClose}>
                <Text style={[styles.modalButtonText, {color: '#FFF'}]}>
                  Close Year
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Final Close Modal */}
      <Modal
        visible={showFinalModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowFinalModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Final Closing</Text>
            <Text style={styles.modalText}>
              Final closing requires audit completion details. You'll be taken to a
              detailed form.
            </Text>
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonCancel]}
                onPress={() => {
                  setShowFinalModal(false);
                  setSelectedYear(null);
                }}>
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonConfirm]}
                onPress={handleFinalClose}>
                <Text style={[styles.modalButtonText, {color: '#FFF'}]}>
                  Continue
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  contentContainer: {
    padding: spacing.lg,
  },
  header: {
    marginBottom: spacing.lg,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: 15,
    color: '#8E8E93',
  },
  infoCard: {
    backgroundColor: '#E8F4FD',
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderColor: '#007AFF',
    borderWidth: 1,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: spacing.md,
  },
  stageRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  stageNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.sm,
  },
  stageNumberText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '700',
  },
  stageContent: {
    flex: 1,
  },
  stageTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  stageDescription: {
    fontSize: 13,
    color: '#8E8E93',
  },
  yearCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  yearHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  yearTitleSection: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  yearName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
    marginRight: spacing.sm,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs / 2,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: spacing.xs / 2,
  },
  activeBadge: {
    backgroundColor: '#34C759',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs / 2,
    borderRadius: 12,
  },
  activeText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '600',
  },
  datesSection: {
    marginBottom: spacing.md,
  },
  dateText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  summarySection: {
    backgroundColor: '#F9F9F9',
    borderRadius: 8,
    padding: spacing.sm,
    marginBottom: spacing.md,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs / 2,
  },
  summaryRowLast: {
    marginTop: spacing.xs,
    paddingTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    marginBottom: 0,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  summaryValue: {
    fontSize: 14,
    color: '#1D1D1F',
    fontWeight: '500',
  },
  summaryLabelBold: {
    fontSize: 15,
    color: '#1D1D1F',
    fontWeight: '600',
  },
  summaryValueBold: {
    fontSize: 15,
    fontWeight: '700',
  },
  auditSection: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3E0',
    padding: spacing.sm,
    borderRadius: 8,
    marginBottom: spacing.md,
  },
  auditText: {
    fontSize: 13,
    color: '#FF9500',
    marginLeft: spacing.xs,
    flex: 1,
  },
  auditTextFinal: {
    fontSize: 13,
    color: '#34C759',
    marginLeft: spacing.xs,
    flex: 1,
  },
  openingBalancesButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9F9F9',
    padding: spacing.sm,
    borderRadius: 8,
    marginBottom: spacing.md,
  },
  openingBalancesText: {
    fontSize: 14,
    color: '#1D1D1F',
    marginLeft: spacing.xs,
    flex: 1,
  },
  actionsSection: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    minWidth: '45%',
  },
  actionButtonPrimary: {
    borderColor: '#007AFF',
    backgroundColor: '#F0F7FF',
  },
  actionButtonWarning: {
    borderColor: '#FF9500',
    backgroundColor: '#FFF3E0',
  },
  actionButtonDanger: {
    borderColor: '#FF3B30',
    backgroundColor: '#FFEBEA',
  },
  actionButtonSuccess: {
    borderColor: '#34C759',
    backgroundColor: '#E8F5E9',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    marginLeft: spacing.xs,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: spacing.lg,
    width: '100%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: spacing.md,
  },
  modalText: {
    fontSize: 15,
    color: '#8E8E93',
    marginBottom: spacing.md,
  },
  modalInput: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    padding: spacing.sm,
    fontSize: 15,
    color: '#1D1D1F',
    marginBottom: spacing.md,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  modalButton: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalButtonCancel: {
    backgroundColor: '#F9F9F9',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  modalButtonConfirm: {
    backgroundColor: '#007AFF',
  },
  modalButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
});

export default FinancialYearManagementScreen;



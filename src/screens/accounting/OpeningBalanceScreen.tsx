import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Modal,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {accountingService, AccountCode} from '../../services/accountingService';
import {authService} from '../../services/authService';

type AccountTypeFilter = 'cash' | 'bank' | 'asset' | 'liability' | 'all';

const OpeningBalanceScreen = ({navigation}: any) => {
  const [accounts, setAccounts] = useState<AccountCode[]>([]);
  const [filteredAccounts, setFilteredAccounts] = useState<AccountCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<AccountTypeFilter>('all');
  const [isAdmin, setIsAdmin] = useState(false);
  const [editingAccount, setEditingAccount] = useState<AccountCode | null>(null);
  const [openingBalance, setOpeningBalance] = useState('');
  const [saving, setSaving] = useState(false);
  const [balanceValidation, setBalanceValidation] = useState<any>(null);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    checkAdminStatus();
    loadAccounts();
  }, []);

  useEffect(() => {
    filterAccounts();
    validateBalanceSheet();
  }, [accounts, filter]);

  const checkAdminStatus = async () => {
    try {
      const user = await authService.getStoredUser();
      setIsAdmin(user?.role === 'admin' || user?.role === 'super_admin');
    } catch (error) {
      console.error('Error checking admin status:', error);
      setIsAdmin(false);
    }
  };

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const accountsList = await accountingService.getAccountCodes();
      setAccounts(accountsList);
    } catch (error: any) {
      console.error('Error loading accounts:', error);
      Alert.alert('Error', 'Failed to load accounts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filterAccounts = () => {
    let filtered = accounts;

    if (filter === 'cash') {
      filtered = accounts.filter(
        acc => acc.type === 'asset' && acc.name.toLowerCase().includes('cash')
      );
    } else if (filter === 'bank') {
      filtered = accounts.filter(
        acc => acc.type === 'asset' && acc.name.toLowerCase().includes('bank')
      );
    } else if (filter === 'asset') {
      filtered = accounts.filter(acc => acc.type === 'asset');
    } else if (filter === 'liability') {
      filtered = accounts.filter(acc => acc.type === 'liability');
    }

    setFilteredAccounts(filtered);
  };

  const handleEdit = (account: AccountCode) => {
    setEditingAccount(account);
    setOpeningBalance(account.opening_balance.toString());
  };

  const validateBalanceSheet = async () => {
    setValidating(true);
    try {
      const validation = await accountingService.validateBalanceSheet();
      setBalanceValidation(validation);
    } catch (error: any) {
      console.error('Error validating balance sheet:', error);
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async () => {
    if (!editingAccount) return;

    const balance = parseFloat(openingBalance);
    if (isNaN(balance)) {
      Alert.alert('Error', 'Please enter a valid number');
      return;
    }

    setSaving(true);
    try {
      await accountingService.updateOpeningBalance(editingAccount.code, balance);
      Alert.alert('Success', 'Opening balance updated successfully');
      setEditingAccount(null);
      setOpeningBalance('');
      await loadAccounts();
      await validateBalanceSheet();
    } catch (error: any) {
      console.error('Error updating opening balance:', error);
      Alert.alert(
        'Error',
        error?.response?.data?.detail || 'Failed to update opening balance. Please try again.'
      );
    } finally {
      setSaving(false);
    }
  };

  const handleQuickSetEquity = async () => {
    if (!balanceValidation || !balanceValidation.equity_account_code) return;

    const equityAccount = accounts.find(acc => acc.code === balanceValidation.equity_account_code);
    if (!equityAccount) {
      Alert.alert('Error', 'Owner\'s Equity account (3001) not found. Please initialize chart of accounts first.');
      return;
    }

    const currentEquity = equityAccount.opening_balance;
    const newEquity = currentEquity + balanceValidation.difference;

    setSaving(true);
    try {
      await accountingService.updateOpeningBalance(equityAccount.code, newEquity);
      Alert.alert('Success', `Owner's Equity updated to ₹${newEquity.toLocaleString('en-IN', {minimumFractionDigits: 2})}`);
      await loadAccounts();
      await validateBalanceSheet();
    } catch (error: any) {
      console.error('Error updating equity:', error);
      Alert.alert('Error', 'Failed to update Owner\'s Equity. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const getAccountTypeColor = (type: string) => {
    switch (type) {
      case 'asset':
        return '#4CAF50';
      case 'liability':
        return '#FF9800';
      case 'capital':
        return '#2196F3';
      case 'income':
        return '#9C27B0';
      case 'expense':
        return '#F44336';
      default:
        return '#666';
    }
  };

  const renderAccount = ({item}: {item: AccountCode}) => (
    <TouchableOpacity
      style={styles.accountCard}
      onPress={() => isAdmin && handleEdit(item)}
      disabled={!isAdmin}
      activeOpacity={isAdmin ? 0.7 : 1}>
      <View style={styles.accountHeader}>
        <View style={[styles.accountTypeBadge, {backgroundColor: getAccountTypeColor(item.type) + '20'}]}>
          <Text style={[styles.accountTypeText, {color: getAccountTypeColor(item.type)}]}>
            {item.type.toUpperCase()}
          </Text>
        </View>
        <View style={styles.accountCodeContainer}>
          <Text style={styles.accountCode}>{item.code}</Text>
        </View>
      </View>
      <Text style={styles.accountName}>{item.name}</Text>
      {item.description && (
        <Text style={styles.accountDescription}>{item.description}</Text>
      )}
      <View style={styles.balanceContainer}>
        <View style={styles.balanceRow}>
          <Text style={styles.balanceLabel}>Opening Balance:</Text>
          <Text style={styles.balanceValue}>{formatCurrency(item.opening_balance)}</Text>
        </View>
        <View style={styles.balanceRow}>
          <Text style={styles.balanceLabel}>Current Balance:</Text>
          <Text
            style={[
              styles.balanceValue,
              item.current_balance >= 0 ? styles.positiveBalance : styles.negativeBalance,
            ]}>
            {formatCurrency(item.current_balance)}
          </Text>
        </View>
      </View>
      {isAdmin && (
        <View style={styles.editButton}>
          <Icon name="create-outline" size={18} color="#007AFF" />
          <Text style={styles.editButtonText}>Tap to Edit</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading accounts...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Balance Sheet Validation Banner */}
      {balanceValidation && (
        <View
          style={[
            styles.validationBanner,
            balanceValidation.is_balanced
              ? styles.validationBannerSuccess
              : styles.validationBannerWarning,
          ]}>
          <Icon
            name={balanceValidation.is_balanced ? 'checkmark-circle' : 'alert-circle'}
            size={24}
            color={balanceValidation.is_balanced ? '#4CAF50' : '#FF9800'}
          />
          <View style={styles.validationContent}>
            <Text
              style={[
                styles.validationTitle,
                balanceValidation.is_balanced
                  ? styles.validationTitleSuccess
                  : styles.validationTitleWarning,
              ]}>
              {balanceValidation.is_balanced ? 'Balance Sheet Balanced ✓' : 'Balance Sheet Not Balanced'}
            </Text>
            <Text style={styles.validationMessage}>{balanceValidation.message}</Text>
            {!balanceValidation.is_balanced && (
              <View style={styles.validationDetails}>
                <View style={styles.validationRow}>
                  <Text style={styles.validationLabel}>Total Assets:</Text>
                  <Text style={styles.validationValue}>
                    ₹{balanceValidation.total_assets.toLocaleString('en-IN', {
                      minimumFractionDigits: 2,
                    })}
                  </Text>
                </View>
                <View style={styles.validationRow}>
                  <Text style={styles.validationLabel}>Total Liabilities:</Text>
                  <Text style={styles.validationValue}>
                    ₹{balanceValidation.total_liabilities.toLocaleString('en-IN', {
                      minimumFractionDigits: 2,
                    })}
                  </Text>
                </View>
                <View style={styles.validationRow}>
                  <Text style={styles.validationLabel}>Total Equity:</Text>
                  <Text style={styles.validationValue}>
                    ₹{balanceValidation.total_equity.toLocaleString('en-IN', {
                      minimumFractionDigits: 2,
                    })}
                  </Text>
                </View>
                <View style={styles.validationRow}>
                  <Text style={styles.validationLabel}>Difference:</Text>
                  <Text
                    style={[
                      styles.validationValue,
                      Math.abs(balanceValidation.difference) > 0.01
                        ? styles.validationDifference
                        : null,
                    ]}>
                    ₹{Math.abs(balanceValidation.difference).toLocaleString('en-IN', {
                      minimumFractionDigits: 2,
                    })}
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.quickSetButton}
                  onPress={handleQuickSetEquity}
                  disabled={saving}>
                  <Icon name="calculator" size={18} color="#FFF" />
                  <Text style={styles.quickSetButtonText}>
                    Auto-Set Owner's Equity ({balanceValidation.equity_account_code})
                  </Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>
      )}

      {/* Filter Buttons */}
      <View style={styles.filterContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {[
            {key: 'all', label: 'All'},
            {key: 'cash', label: 'Cash'},
            {key: 'bank', label: 'Bank'},
            {key: 'asset', label: 'Assets'},
            {key: 'liability', label: 'Liabilities'},
          ].map(({key, label}) => (
            <TouchableOpacity
              key={key}
              style={[styles.filterButton, filter === key && styles.filterButtonActive]}
              onPress={() => setFilter(key as AccountTypeFilter)}
              activeOpacity={0.7}>
              <Text
                style={[
                  styles.filterButtonText,
                  filter === key && styles.filterButtonTextActive,
                ]}>
                {label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Accounts List */}
      <FlatList
        data={filteredAccounts}
        renderItem={renderAccount}
        keyExtractor={(item, index) => item.id?.toString() || `account-${index}`}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Icon name="wallet-outline" size={64} color="#C7C7CC" />
            <Text style={styles.emptyStateText}>No accounts found</Text>
            <Text style={styles.emptyStateSubtext}>
              {filter === 'all'
                ? 'No accounts available'
                : `No ${filter} accounts found`}
            </Text>
          </View>
        }
      />

      {/* Edit Modal */}
      <Modal
        visible={editingAccount !== null}
        animationType="slide"
        transparent={true}
        onRequestClose={() => {
          setEditingAccount(null);
          setOpeningBalance('');
        }}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Update Opening Balance</Text>
              <TouchableOpacity
                onPress={() => {
                  setEditingAccount(null);
                  setOpeningBalance('');
                }}
                style={styles.closeButton}>
                <Icon name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            {editingAccount && (
              <View style={styles.modalBody}>
                <View style={styles.modalAccountInfo}>
                  <Text style={styles.modalAccountCode}>{editingAccount.code}</Text>
                  <Text style={styles.modalAccountName}>{editingAccount.name}</Text>
                  <Text style={styles.modalAccountType}>{editingAccount.type.toUpperCase()}</Text>
                </View>

                <View style={styles.inputSection}>
                  <Text style={styles.inputLabel}>Opening Balance *</Text>
                  <View style={styles.inputContainer}>
                    <Text style={styles.currencySymbol}>₹</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="0.00"
                      placeholderTextColor="#999"
                      value={openingBalance}
                      onChangeText={setOpeningBalance}
                      keyboardType="decimal-pad"
                      autoFocus
                    />
                  </View>
                  <Text style={styles.hintText}>
                    Current: {formatCurrency(editingAccount.opening_balance)}
                  </Text>
                </View>

                <TouchableOpacity
                  style={[styles.saveButton, saving && styles.saveButtonDisabled]}
                  onPress={handleSave}
                  disabled={saving}>
                  {saving ? (
                    <ActivityIndicator size="small" color="#FFF" />
                  ) : (
                    <>
                      <Icon name="checkmark-circle" size={20} color="#FFF" />
                      <Text style={styles.saveButtonText}>Save Changes</Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  validationBanner: {
    flexDirection: 'row',
    padding: 16,
    margin: 16,
    borderRadius: 12,
    borderWidth: 2,
  },
  validationBannerSuccess: {
    backgroundColor: '#E8F5E9',
    borderColor: '#4CAF50',
  },
  validationBannerWarning: {
    backgroundColor: '#FFF3E0',
    borderColor: '#FF9800',
  },
  validationContent: {
    flex: 1,
    marginLeft: 12,
  },
  validationTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  validationTitleSuccess: {
    color: '#4CAF50',
  },
  validationTitleWarning: {
    color: '#FF9800',
  },
  validationMessage: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    lineHeight: 20,
  },
  validationDetails: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  validationRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  validationLabel: {
    fontSize: 13,
    color: '#666',
    fontWeight: '500',
  },
  validationValue: {
    fontSize: 13,
    color: '#1D1D1F',
    fontWeight: '600',
  },
  validationDifference: {
    color: '#F44336',
    fontWeight: '700',
  },
  quickSetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
    gap: 8,
  },
  quickSetButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  filterContainer: {
    backgroundColor: '#FFF',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  filterButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    marginRight: 8,
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
  },
  filterButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  filterButtonTextActive: {
    color: '#FFF',
  },
  listContainer: {
    padding: 16,
  },
  accountCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  accountHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  accountTypeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  accountTypeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  accountCodeContainer: {
    backgroundColor: '#F5F5F5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  accountCode: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    fontFamily: 'monospace',
  },
  accountName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  accountDescription: {
    fontSize: 13,
    color: '#666',
    marginBottom: 12,
    fontStyle: 'italic',
  },
  balanceContainer: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  balanceLabel: {
    fontSize: 14,
    color: '#666',
  },
  balanceValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  positiveBalance: {
    color: '#4CAF50',
  },
  negativeBalance: {
    color: '#F44336',
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    gap: 6,
  },
  editButtonText: {
    fontSize: 13,
    color: '#007AFF',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 60,
  },
  emptyStateText: {
    fontSize: 18,
    color: '#999',
    marginTop: 15,
    fontWeight: '600',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#BBB',
    marginTop: 8,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  closeButton: {
    padding: 4,
  },
  modalBody: {
    padding: 20,
  },
  modalAccountInfo: {
    alignItems: 'center',
    marginBottom: 24,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalAccountCode: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  modalAccountName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
    textAlign: 'center',
  },
  modalAccountType: {
    fontSize: 12,
    color: '#666',
    textTransform: 'uppercase',
  },
  inputSection: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5E5EA',
    paddingHorizontal: 16,
    height: 56,
  },
  currencySymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 18,
    color: '#1D1D1F',
    fontWeight: '600',
  },
  hintText: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
    fontStyle: 'italic',
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 12,
    height: 56,
    gap: 8,
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});

export default OpeningBalanceScreen;


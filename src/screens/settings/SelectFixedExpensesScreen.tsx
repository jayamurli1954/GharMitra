import React, {useEffect, useState} from 'react';
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
import {accountingService, AccountCode} from '../../services/accountingService';

const SelectFixedExpensesScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expenseAccounts, setExpenseAccounts] = useState<AccountCode[]>([]);
  const [selectedAccounts, setSelectedAccounts] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadExpenseAccounts();
  }, []);

  const loadExpenseAccounts = async () => {
    setLoading(true);
    try {
      const accounts = await accountingService.getAccountCodes('expense');
      setExpenseAccounts(accounts);
      
      // Initialize selected accounts from is_fixed_expense flag
      const selected = new Set<string>();
      accounts.forEach(account => {
        if (account.is_fixed_expense) {
          selected.add(account.code);
        }
      });
      setSelectedAccounts(selected);
    } catch (error: any) {
      console.error('Error loading expense accounts:', error);
      Alert.alert('Error', 'Failed to load expense accounts');
    } finally {
      setLoading(false);
    }
  };

  const toggleAccount = async (accountCode: string, currentValue: boolean) => {
    if (saving) return;
    
    setSaving(true);
    try {
      const newValue = !currentValue;
      await accountingService.toggleFixedExpense(accountCode, newValue);
      
      // Update local state
      const updated = new Set(selectedAccounts);
      if (newValue) {
        updated.add(accountCode);
      } else {
        updated.delete(accountCode);
      }
      setSelectedAccounts(updated);
      
      // Update the account in the list
      setExpenseAccounts(prev =>
        prev.map(acc =>
          acc.code === accountCode
            ? {...acc, is_fixed_expense: newValue}
            : acc
        )
      );
    } catch (error: any) {
      console.error('Error toggling fixed expense:', error);
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to update fixed expense setting'
      );
    } finally {
      setSaving(false);
    }
  };

  const selectAll = async () => {
    if (saving) return;
    
    // Get all non-water-charge accounts
    const nonWaterAccounts = expenseAccounts.filter(
      acc => acc.code !== '5110' && acc.code !== '5120'
    );
    const accountsToSelect = nonWaterAccounts.filter(
      acc => !selectedAccounts.has(acc.code)
    );
    
    if (accountsToSelect.length === 0) {
      Alert.alert('Info', 'All eligible expenses are already selected');
      return;
    }
    
    setSaving(true);
    try {
      // Update all accounts in parallel
      await Promise.all(
        accountsToSelect.map(acc =>
          accountingService.toggleFixedExpense(acc.code, true)
        )
      );
      
      // Update local state
      const updated = new Set(selectedAccounts);
      accountsToSelect.forEach(acc => updated.add(acc.code));
      setSelectedAccounts(updated);
      
      // Update the accounts in the list
      setExpenseAccounts(prev =>
        prev.map(acc =>
          accountsToSelect.some(a => a.code === acc.code)
            ? {...acc, is_fixed_expense: true}
            : acc
        )
      );
      
      Alert.alert('Success', `Selected ${accountsToSelect.length} expense account(s)`);
    } catch (error: any) {
      console.error('Error selecting all:', error);
      Alert.alert('Error', 'Failed to select all expenses. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const deselectAll = async () => {
    if (saving) return;
    
    if (selectedAccounts.size === 0) {
      Alert.alert('Info', 'No expenses are currently selected');
      return;
    }
    
    const confirm = await new Promise<boolean>(resolve => {
      Alert.alert(
        'Deselect All',
        `Are you sure you want to deselect all ${selectedAccounts.size} selected expense account(s)?`,
        [
          {text: 'Cancel', style: 'cancel', onPress: () => resolve(false)},
          {text: 'Deselect All', style: 'destructive', onPress: () => resolve(true)},
        ]
      );
    });
    
    if (!confirm) return;
    
    setSaving(true);
    try {
      const accountsToDeselect = Array.from(selectedAccounts);
      
      // Update all accounts in parallel
      await Promise.all(
        accountsToDeselect.map(code =>
          accountingService.toggleFixedExpense(code, false)
        )
      );
      
      // Update local state
      setSelectedAccounts(new Set());
      
      // Update the accounts in the list
      setExpenseAccounts(prev =>
        prev.map(acc =>
          accountsToDeselect.includes(acc.code)
            ? {...acc, is_fixed_expense: false}
            : acc
        )
      );
      
      Alert.alert('Success', `Deselected ${accountsToDeselect.length} expense account(s)`);
    } catch (error: any) {
      console.error('Error deselecting all:', error);
      Alert.alert('Error', 'Failed to deselect all expenses. Please try again.');
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

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading expense accounts...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          activeOpacity={0.7}>
          <Icon name="arrow-back" size={24} color="#FFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Select Fixed Expenses</Text>
      </View>

      <View style={styles.infoBox}>
        <Icon name="information-circle" size={24} color="#007AFF" />
        <View style={styles.infoContent}>
          <Text style={styles.infoTitle}>Fixed Expenses</Text>
          <Text style={styles.infoText}>
            Select expense account codes that should be included in fixed expenses calculation.
            These expenses will be divided equally among all flats (including vacant flats).
            {'\n\n'}
            Water charges (5110, 5120) are automatically calculated per occupant and should NOT be selected here.
          </Text>
        </View>
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="list" size={20} color="#007AFF" />
          <Text style={styles.sectionTitle}>Expense Account Codes</Text>
        </View>
        <Text style={styles.sectionDescription}>
          Select which expenses should be considered as fixed expenses for billing
        </Text>

        {/* Select All / Deselect All Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionButton, styles.selectAllButton]}
            onPress={selectAll}
            disabled={saving}
            activeOpacity={0.7}>
            <Icon name="checkmark-circle" size={20} color="#FFF" />
            <Text style={styles.actionButtonText}>Select All</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionButton, styles.deselectAllButton]}
            onPress={deselectAll}
            disabled={saving}
            activeOpacity={0.7}>
            <Icon name="close-circle" size={20} color="#FFF" />
            <Text style={styles.actionButtonText}>Deselect All</Text>
          </TouchableOpacity>
        </View>

        {expenseAccounts.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Icon name="document-outline" size={48} color="#C7C7CC" />
            <Text style={styles.emptyText}>No expense accounts found</Text>
            <Text style={styles.emptySubtext}>
              Please initialize chart of accounts first
            </Text>
          </View>
        ) : (
          expenseAccounts.map(account => {
            const isSelected = selectedAccounts.has(account.code);
            const isWaterCharge = account.code === '5110' || account.code === '5120';
            
            return (
              <TouchableOpacity
                key={account.code}
                style={[
                  styles.accountCard,
                  isSelected && styles.accountCardSelected,
                  isWaterCharge && styles.accountCardDisabled,
                ]}
                onPress={() => !isWaterCharge && toggleAccount(account.code, isSelected)}
                disabled={isWaterCharge || saving}
                activeOpacity={0.7}>
                <View style={styles.accountRow}>
                  <View style={styles.accountInfo}>
                    <View style={styles.accountHeader}>
                      <Text style={styles.accountCode}>{account.code}</Text>
                      <View style={styles.checkbox}>
                        {isSelected ? (
                          <Icon name="checkbox" size={24} color="#007AFF" />
                        ) : (
                          <Icon name="square-outline" size={24} color="#C7C7CC" />
                        )}
                      </View>
                    </View>
                    <Text style={styles.accountName}>{account.name}</Text>
                    {account.description && (
                      <Text style={styles.accountDescription}>
                        {account.description}
                      </Text>
                    )}
                    {isWaterCharge && (
                      <View style={styles.warningBadge}>
                        <Icon name="warning" size={14} color="#FF9800" />
                        <Text style={styles.warningText}>
                          Water charges are calculated per occupant
                        </Text>
                      </View>
                    )}
                  </View>
                </View>
              </TouchableOpacity>
            );
          })
        )}
      </View>

      <View style={styles.summaryBox}>
        <Text style={styles.summaryTitle}>Summary</Text>
        <Text style={styles.summaryText}>
          {selectedAccounts.size} expense account{selectedAccounts.size !== 1 ? 's' : ''} selected
        </Text>
        <Text style={styles.summaryHint}>
          These expenses will be divided equally among all flats when generating bills
        </Text>
      </View>
    </ScrollView>
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
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  backButton: {
    marginRight: 12,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFF',
  },
  infoBox: {
    flexDirection: 'row',
    margin: 16,
    padding: 16,
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
    lineHeight: 18,
  },
  section: {
    margin: 16,
    padding: 20,
    backgroundColor: '#FFF',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  sectionDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 16,
    lineHeight: 20,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginTop: 12,
    fontWeight: '600',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 4,
  },
  accountCard: {
    borderWidth: 2,
    borderColor: '#E5E5EA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    backgroundColor: '#FAFAFA',
  },
  accountCardSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD',
  },
  accountCardDisabled: {
    opacity: 0.6,
    borderColor: '#FFE5E5',
    backgroundColor: '#FFF5F5',
  },
  accountRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  accountInfo: {
    flex: 1,
  },
  accountHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  accountCode: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  checkbox: {
    marginLeft: 'auto',
  },
  accountName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  accountDescription: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  warningBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    padding: 6,
    backgroundColor: '#FFF3E0',
    borderRadius: 6,
    gap: 4,
  },
  warningText: {
    fontSize: 12,
    color: '#FF9800',
    fontWeight: '500',
  },
  summaryBox: {
    margin: 16,
    padding: 20,
    backgroundColor: '#F0F8FF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#007AFF',
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 15,
    color: '#1D1D1F',
    fontWeight: '600',
    marginBottom: 4,
  },
  summaryHint: {
    fontSize: 13,
    color: '#666',
    marginTop: 4,
    lineHeight: 18,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 14,
    borderRadius: 12,
    gap: 8,
  },
  selectAllButton: {
    backgroundColor: '#4CAF50',
  },
  deselectAllButton: {
    backgroundColor: '#F44336',
  },
  actionButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFF',
  },
});

export default SelectFixedExpensesScreen;


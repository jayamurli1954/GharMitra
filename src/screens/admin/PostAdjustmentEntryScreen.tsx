import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {useRoute, useNavigation} from '@react-navigation/native';
import {Picker} from '@react-native-picker/picker';
import {
  financialYearService,
  JournalEntryItem,
} from '../../services/financialYearService';
import {accountingService} from '../../services/accountingService';
import {spacing} from '../../constants/spacing';
import {formatCurrency} from '../../utils/formatters';

interface Account {
  id: string;
  name: string;
  code: string;
}

const PostAdjustmentEntryScreen: React.FC = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const {yearId} = route.params as {yearId: string};

  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [effectiveDate, setEffectiveDate] = useState('');
  const [adjustmentType, setAdjustmentType] = useState('expense_correction');
  const [description, setDescription] = useState('');
  const [reason, setReason] = useState('');
  const [auditorReference, setAuditorReference] = useState('');
  const [entries, setEntries] = useState<JournalEntryItem[]>([
    {
      account_head_id: '',
      account_name: '',
      entry_type: 'debit',
      amount: 0,
      description: '',
    },
    {
      account_head_id: '',
      account_name: '',
      entry_type: 'credit',
      amount: 0,
      description: '',
    },
  ]);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const data = await accountingService.getAccountHeads();
      setAccounts(data);
    } catch (error: any) {
      Alert.alert('Error', 'Failed to load accounts');
    }
  };

  const addEntry = () => {
    setEntries([
      ...entries,
      {
        account_head_id: '',
        account_name: '',
        entry_type: 'debit',
        amount: 0,
        description: '',
      },
    ]);
  };

  const removeEntry = (index: number) => {
    if (entries.length <= 2) {
      Alert.alert('Error', 'Minimum 2 entries required (1 debit, 1 credit)');
      return;
    }
    setEntries(entries.filter((_, i) => i !== index));
  };

  const updateEntry = (index: number, field: string, value: any) => {
    const updated = [...entries];
    if (field === 'account_head_id') {
      const account = accounts.find(a => a.id === value);
      updated[index].account_head_id = value;
      updated[index].account_name = account ? account.name : '';
    } else {
      updated[index][field] = value;
    }
    setEntries(updated);
  };

  const calculateTotals = () => {
    const totalDebit = entries
      .filter(e => e.entry_type === 'debit')
      .reduce((sum, e) => sum + parseFloat(e.amount?.toString() || '0'), 0);
    const totalCredit = entries
      .filter(e => e.entry_type === 'credit')
      .reduce((sum, e) => sum + parseFloat(e.amount?.toString() || '0'), 0);
    return {totalDebit, totalCredit, difference: totalDebit - totalCredit};
  };

  const handleSubmit = async () => {
    // Validation
    if (!effectiveDate) {
      Alert.alert('Error', 'Please enter effective date');
      return;
    }
    if (!description) {
      Alert.alert('Error', 'Please enter description');
      return;
    }
    if (!reason) {
      Alert.alert('Error', 'Please enter reason');
      return;
    }

    // Check if all entries have accounts and amounts
    for (const entry of entries) {
      if (!entry.account_head_id) {
        Alert.alert('Error', 'Please select account for all entries');
        return;
      }
      if (!entry.amount || entry.amount <= 0) {
        Alert.alert('Error', 'All amounts must be greater than 0');
        return;
      }
    }

    // Check if balanced
    const {difference} = calculateTotals();
    if (Math.abs(difference) > 0.01) {
      Alert.alert(
        'Error',
        `Entry is not balanced. Difference: ₹${Math.abs(difference).toFixed(2)}`,
      );
      return;
    }

    Alert.alert(
      'Confirm Adjustment',
      `This will post an adjustment entry to the provisionally closed year.\n\nAre you sure?`,
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Post Adjustment',
          style: 'destructive',
          onPress: async () => {
            try {
              setLoading(true);
              const result = await financialYearService.postAdjustmentEntry(
                yearId,
                {
                  effective_date: effectiveDate,
                  adjustment_type: adjustmentType,
                  description,
                  reason,
                  auditor_reference: auditorReference || undefined,
                  entries,
                },
              );

              Alert.alert('Success', result.message, [
                {
                  text: 'OK',
                  onPress: () => navigation.goBack(),
                },
              ]);
            } catch (error: any) {
              Alert.alert('Error', error.message || 'Failed to post adjustment');
            } finally {
              setLoading(false);
            }
          },
        },
      ],
    );
  };

  const {totalDebit, totalCredit, difference} = calculateTotals();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Post Adjustment Entry</Text>
      <Text style={styles.subtitle}>
        Post audit adjustments to provisionally closed year
      </Text>

      {/* Basic Information */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Basic Information</Text>

        <Text style={styles.label}>Effective Date *</Text>
        <TextInput
          style={styles.input}
          placeholder="YYYY-MM-DD"
          value={effectiveDate}
          onChangeText={setEffectiveDate}
        />

        <Text style={styles.label}>Adjustment Type *</Text>
        <View style={styles.pickerContainer}>
          <Picker
            selectedValue={adjustmentType}
            onValueChange={setAdjustmentType}
            style={styles.picker}>
            <Picker.Item label="Expense Correction" value="expense_correction" />
            <Picker.Item label="Income Correction" value="income_correction" />
            <Picker.Item label="Depreciation" value="depreciation" />
            <Picker.Item label="Provision" value="provision" />
            <Picker.Item label="Bad Debt" value="bad_debt" />
            <Picker.Item label="Accrual" value="accrual" />
            <Picker.Item label="Prepayment" value="prepayment" />
            <Picker.Item label="Reclassification" value="reclassification" />
            <Picker.Item label="Other" value="other" />
          </Picker>
        </View>

        <Text style={styles.label}>Description *</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Brief description..."
          value={description}
          onChangeText={setDescription}
          multiline
          numberOfLines={2}
        />

        <Text style={styles.label}>Reason (for audit trail) *</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Detailed reason from auditor..."
          value={reason}
          onChangeText={setReason}
          multiline
          numberOfLines={3}
        />

        <Text style={styles.label}>Auditor Reference</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., Audit Finding #3"
          value={auditorReference}
          onChangeText={setAuditorReference}
        />
      </View>

      {/* Journal Entries */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Journal Entries</Text>
          <TouchableOpacity style={styles.addButton} onPress={addEntry}>
            <Icon name="add-circle" size={24} color="#007AFF" />
          </TouchableOpacity>
        </View>

        {entries.map((entry, index) => (
          <View key={index} style={styles.entryCard}>
            <View style={styles.entryHeader}>
              <Text style={styles.entryNumber}>Entry #{index + 1}</Text>
              {entries.length > 2 && (
                <TouchableOpacity onPress={() => removeEntry(index)}>
                  <Icon name="trash-outline" size={20} color="#FF3B30" />
                </TouchableOpacity>
              )}
            </View>

            <Text style={styles.label}>Account *</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={entry.account_head_id}
                onValueChange={value =>
                  updateEntry(index, 'account_head_id', value)
                }
                style={styles.picker}>
                <Picker.Item label="Select Account..." value="" />
                {accounts.map(account => (
                  <Picker.Item
                    key={account.id}
                    label={`${account.code} - ${account.name}`}
                    value={account.id}
                  />
                ))}
              </Picker>
            </View>

            <Text style={styles.label}>Type *</Text>
            <View style={styles.typeButtons}>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  entry.entry_type === 'debit' && styles.typeButtonActive,
                ]}
                onPress={() => updateEntry(index, 'entry_type', 'debit')}>
                <Text
                  style={[
                    styles.typeButtonText,
                    entry.entry_type === 'debit' && styles.typeButtonTextActive,
                  ]}>
                  Debit
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  entry.entry_type === 'credit' && styles.typeButtonActive,
                ]}
                onPress={() => updateEntry(index, 'entry_type', 'credit')}>
                <Text
                  style={[
                    styles.typeButtonText,
                    entry.entry_type === 'credit' && styles.typeButtonTextActive,
                  ]}>
                  Credit
                </Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.label}>Amount *</Text>
            <TextInput
              style={styles.input}
              placeholder="0.00"
              value={entry.amount?.toString() || ''}
              onChangeText={text => updateEntry(index, 'amount', parseFloat(text) || 0)}
              keyboardType="decimal-pad"
            />

            <Text style={styles.label}>Description (optional)</Text>
            <TextInput
              style={styles.input}
              placeholder="Entry description..."
              value={entry.description}
              onChangeText={text => updateEntry(index, 'description', text)}
            />
          </View>
        ))}
      </View>

      {/* Summary */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>Entry Summary</Text>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Total Debit:</Text>
          <Text style={styles.summaryValue}>{formatCurrency(totalDebit)}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Total Credit:</Text>
          <Text style={styles.summaryValue}>{formatCurrency(totalCredit)}</Text>
        </View>
        <View style={[styles.summaryRow, styles.summaryRowDifference]}>
          <Text style={styles.summaryLabelBold}>Difference:</Text>
          <Text
            style={[
              styles.summaryValueBold,
              {color: Math.abs(difference) < 0.01 ? '#34C759' : '#FF3B30'},
            ]}>
            {formatCurrency(Math.abs(difference))}
          </Text>
        </View>
        {Math.abs(difference) < 0.01 ? (
          <View style={styles.balancedBadge}>
            <Icon name="checkmark-circle" size={16} color="#34C759" />
            <Text style={styles.balancedText}>Entry is balanced</Text>
          </View>
        ) : (
          <View style={styles.unbalancedBadge}>
            <Icon name="alert-circle" size={16} color="#FF3B30" />
            <Text style={styles.unbalancedText}>Entry must be balanced</Text>
          </View>
        )}
      </View>

      {/* Submit Button */}
      <TouchableOpacity
        style={[
          styles.submitButton,
          (loading || Math.abs(difference) >= 0.01) && styles.submitButtonDisabled,
        ]}
        onPress={handleSubmit}
        disabled={loading || Math.abs(difference) >= 0.01}>
        {loading ? (
          <ActivityIndicator color="#FFF" />
        ) : (
          <>
            <Icon name="checkmark-circle-outline" size={20} color="#FFF" />
            <Text style={styles.submitButtonText}>Post Adjustment Entry</Text>
          </>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  content: {
    padding: spacing.lg,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: 15,
    color: '#8E8E93',
    marginBottom: spacing.lg,
  },
  section: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  addButton: {
    padding: spacing.xs,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1D1D1F',
    marginBottom: spacing.xs,
    marginTop: spacing.sm,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    padding: spacing.sm,
    fontSize: 15,
    color: '#1D1D1F',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  entryCard: {
    backgroundColor: '#F9F9F9',
    borderRadius: 8,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  entryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  entryNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  typeButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  typeButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    alignItems: 'center',
  },
  typeButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  typeButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  typeButtonTextActive: {
    color: '#FFF',
  },
  summaryCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.lg,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: spacing.md,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  summaryRowDifference: {
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    marginBottom: spacing.md,
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
  balancedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    padding: spacing.sm,
    borderRadius: 8,
  },
  balancedText: {
    fontSize: 14,
    color: '#34C759',
    marginLeft: spacing.xs,
    fontWeight: '600',
  },
  unbalancedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFEBEA',
    padding: spacing.sm,
    borderRadius: 8,
  },
  unbalancedText: {
    fontSize: 14,
    color: '#FF3B30',
    marginLeft: spacing.xs,
    fontWeight: '600',
  },
  submitButton: {
    flexDirection: 'row',
    backgroundColor: '#007AFF',
    paddingVertical: spacing.md,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
  },
  submitButtonDisabled: {
    backgroundColor: '#8E8E93',
    opacity: 0.5,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});

export default PostAdjustmentEntryScreen;



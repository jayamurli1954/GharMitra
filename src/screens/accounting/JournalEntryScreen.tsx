import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import DateTimePicker from '@react-native-community/datetimepicker';
import {accountingService} from '../../services/accountingService';

interface JournalLine {
  id: string;
  account_code: string;
  account_name: string;
  debit_amount: string;
  credit_amount: string;
  description: string;
}

const JournalEntryScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(false);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [date, setDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [description, setDescription] = useState('');
  const [lines, setLines] = useState<JournalLine[]>([
    {
      id: '1',
      account_code: '',
      account_name: '',
      debit_amount: '',
      credit_amount: '',
      description: '',
    },
    {
      id: '2',
      account_code: '',
      account_name: '',
      debit_amount: '',
      credit_amount: '',
      description: '',
    },
  ]);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    setAccountsLoading(true);
    try {
      const accountsData = await accountingService.getAccountCodes();
      setAccounts(accountsData);
    } catch (error: any) {
      console.error('Error loading accounts:', error);
      Alert.alert('Error', 'Failed to load accounts. Please try again.');
    } finally {
      setAccountsLoading(false);
    }
  };

  const addLine = () => {
    const newId = (lines.length + 1).toString();
    setLines([
      ...lines,
      {
        id: newId,
        account_code: '',
        account_name: '',
        debit_amount: '',
        credit_amount: '',
        description: '',
      },
    ]);
  };

  const removeLine = (id: string) => {
    if (lines.length <= 2) {
      Alert.alert('Error', 'At least 2 lines are required for a journal entry');
      return;
    }
    setLines(lines.filter(line => line.id !== id));
  };

  const updateLine = (id: string, field: keyof JournalLine, value: string) => {
    setLines(
      lines.map(line => {
        if (line.id === id) {
          const updated = {...line, [field]: value};
          
          // If account_code changed, find and set account_name
          if (field === 'account_code') {
            const account = accounts.find(acc => acc.code === value);
            updated.account_name = account ? account.name : '';
            
            // Clear other amount if one is being set
            if (field === 'debit_amount' && value) {
              updated.credit_amount = '';
            } else if (field === 'credit_amount' && value) {
              updated.debit_amount = '';
            }
          }
          
          return updated;
        }
        return line;
      })
    );
  };

  const calculateTotals = () => {
    let totalDebit = 0;
    let totalCredit = 0;
    
    lines.forEach(line => {
      const debit = parseFloat(line.debit_amount) || 0;
      const credit = parseFloat(line.credit_amount) || 0;
      totalDebit += debit;
      totalCredit += credit;
    });
    
    return {totalDebit, totalCredit, difference: totalDebit - totalCredit};
  };

  const validateEntry = (): boolean => {
    if (!description.trim()) {
      Alert.alert('Error', 'Please enter a description for the journal entry');
      return false;
    }
    
    if (lines.length < 2) {
      Alert.alert('Error', 'At least 2 lines are required');
      return false;
    }
    
    // Check each line
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (!line.account_code) {
        Alert.alert('Error', `Line ${i + 1}: Please select an account`);
        return false;
      }
      
      const debit = parseFloat(line.debit_amount) || 0;
      const credit = parseFloat(line.credit_amount) || 0;
      
      if (debit === 0 && credit === 0) {
        Alert.alert('Error', `Line ${i + 1}: Please enter either debit or credit amount`);
        return false;
      }
      
      if (debit > 0 && credit > 0) {
        Alert.alert('Error', `Line ${i + 1}: Cannot have both debit and credit amounts`);
        return false;
      }
    }
    
    // Check balance
    const {totalDebit, totalCredit, difference} = calculateTotals();
    
    if (Math.abs(difference) > 0.01) {
      Alert.alert(
        'Entry Not Balanced',
        `Total Debit: ₹${totalDebit.toFixed(2)}\nTotal Credit: ₹${totalCredit.toFixed(2)}\nDifference: ₹${Math.abs(difference).toFixed(2)}\n\nDebit and Credit must be equal.`
      );
      return false;
    }
    
    if (totalDebit === 0 || totalCredit === 0) {
      Alert.alert('Error', 'Entry must have at least one debit and one credit');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async () => {
    if (!validateEntry()) return;
    
    setLoading(true);
    try {
      const formattedLines = lines.map(line => ({
        account_code: line.account_code,
        debit_amount: parseFloat(line.debit_amount) || 0,
        credit_amount: parseFloat(line.credit_amount) || 0,
        description: line.description || description,
      }));
      
      const entryData = {
        date: date.toISOString().split('T')[0],
        description,
        entries: formattedLines,
      };
      
      await accountingService.createJournalEntry(entryData);
      
      Alert.alert(
        'Success',
        'Journal entry created successfully!',
        [
          {
            text: 'Create Another',
            onPress: () => {
              // Reset form
              setDescription('');
              setDate(new Date());
              setLines([
                {
                  id: '1',
                  account_code: '',
                  account_name: '',
                  debit_amount: '',
                  credit_amount: '',
                  description: '',
                },
                {
                  id: '2',
                  account_code: '',
                  account_name: '',
                  debit_amount: '',
                  credit_amount: '',
                  description: '',
                },
              ]);
            },
          },
          {
            text: 'View Entries',
            onPress: () => navigation.navigate('JournalEntryReport'),
          },
        ]
      );
    } catch (error: any) {
      console.error('Error creating journal entry:', error);
      Alert.alert(
        'Error',
        error?.response?.data?.detail || 'Failed to create journal entry. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: string) => {
    const num = parseFloat(value) || 0;
    return `₹${num.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  };

  const {totalDebit, totalCredit, difference} = calculateTotals();
  const isBalanced = Math.abs(difference) < 0.01;

  if (accountsLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading accounts...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <Text style={styles.headerLabel}>Date:</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowDatePicker(true)}
            activeOpacity={0.7}>
            <Icon name="calendar-outline" size={20} color="#007AFF" />
            <Text style={styles.dateText}>{date.toLocaleDateString('en-IN')}</Text>
          </TouchableOpacity>
        </View>

        <TextInput
          style={styles.descriptionInput}
          placeholder="Journal Entry Description *"
          value={description}
          onChangeText={setDescription}
          placeholderTextColor="#999"
          multiline
        />
      </View>

      {showDatePicker && (
        <DateTimePicker
          value={date}
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowDatePicker(false);
            if (selectedDate) {
              setDate(selectedDate);
            }
          }}
        />
      )}

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Journal Lines */}
        {lines.map((line, index) => (
          <View key={line.id} style={styles.lineCard}>
            <View style={styles.lineHeader}>
              <Text style={styles.lineNumber}>Line {index + 1}</Text>
              {lines.length > 2 && (
                <TouchableOpacity
                  onPress={() => removeLine(line.id)}
                  style={styles.removeButton}
                  activeOpacity={0.7}>
                  <Icon name="trash-outline" size={20} color="#dc3545" />
                </TouchableOpacity>
              )}
            </View>

            {/* Account Selector */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Account *</Text>
              <View style={styles.pickerContainer}>
                <select
                  style={styles.picker}
                  value={line.account_code}
                  onChange={(e: any) => updateLine(line.id, 'account_code', e.target.value)}>
                  <option value="">Select Account</option>
                  {accounts.map(account => (
                    <option key={account.code} value={account.code}>
                      {account.code} - {account.name}
                    </option>
                  ))}
                </select>
              </View>
            </View>

            {/* Amounts */}
            <View style={styles.amountRow}>
              <View style={[styles.inputGroup, {flex: 1, marginRight: 8}]}>
                <Text style={styles.inputLabel}>Debit</Text>
                <TextInput
                  style={[styles.input, styles.amountInput]}
                  placeholder="0.00"
                  value={line.debit_amount}
                  onChangeText={(value) => {
                    updateLine(line.id, 'debit_amount', value);
                    if (value) {
                      updateLine(line.id, 'credit_amount', '');
                    }
                  }}
                  keyboardType="decimal-pad"
                  placeholderTextColor="#999"
                />
              </View>

              <View style={[styles.inputGroup, {flex: 1}]}>
                <Text style={styles.inputLabel}>Credit</Text>
                <TextInput
                  style={[styles.input, styles.amountInput]}
                  placeholder="0.00"
                  value={line.credit_amount}
                  onChangeText={(value) => {
                    updateLine(line.id, 'credit_amount', value);
                    if (value) {
                      updateLine(line.id, 'debit_amount', '');
                    }
                  }}
                  keyboardType="decimal-pad"
                  placeholderTextColor="#999"
                />
              </View>
            </View>

            {/* Line Description */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Line Description (Optional)</Text>
              <TextInput
                style={styles.input}
                placeholder="Additional details for this line"
                value={line.description}
                onChangeText={(value) => updateLine(line.id, 'description', value)}
                placeholderTextColor="#999"
              />
            </View>
          </View>
        ))}

        {/* Add Line Button */}
        <TouchableOpacity style={styles.addLineButton} onPress={addLine} activeOpacity={0.7}>
          <Icon name="add-circle-outline" size={24} color="#007AFF" />
          <Text style={styles.addLineText}>Add Another Line</Text>
        </TouchableOpacity>

        {/* Totals Card */}
        <View style={styles.totalsCard}>
          <Text style={styles.totalsTitle}>Entry Summary</Text>
          
          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Total Debit:</Text>
            <Text style={[styles.totalAmount, {color: '#28a745'}]}>
              {formatCurrency(totalDebit.toString())}
            </Text>
          </View>

          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Total Credit:</Text>
            <Text style={[styles.totalAmount, {color: '#dc3545'}]}>
              {formatCurrency(totalCredit.toString())}
            </Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.totalRow}>
            <Text style={[styles.totalLabel, {fontWeight: 'bold'}]}>Difference:</Text>
            <Text
              style={[
                styles.totalAmount,
                {fontWeight: 'bold', color: isBalanced ? '#28a745' : '#dc3545'},
              ]}>
              {formatCurrency(Math.abs(difference).toString())}
            </Text>
          </View>

          {isBalanced && totalDebit > 0 && (
            <View style={styles.balancedBadge}>
              <Icon name="checkmark-circle" size={20} color="#28a745" />
              <Text style={styles.balancedText}>Entry is balanced ✓</Text>
            </View>
          )}
        </View>

        {/* Submit Button */}
        <TouchableOpacity
          style={[
            styles.submitButton,
            (!isBalanced || totalDebit === 0 || loading) && styles.submitButtonDisabled,
          ]}
          onPress={handleSubmit}
          disabled={!isBalanced || totalDebit === 0 || loading}
          activeOpacity={0.7}>
          {loading ? (
            <ActivityIndicator size="small" color="#FFF" />
          ) : (
            <>
              <Icon name="checkmark-circle" size={24} color="#FFF" />
              <Text style={styles.submitButtonText}>Post Journal Entry</Text>
            </>
          )}
        </TouchableOpacity>

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
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
  header: {
    backgroundColor: '#FFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginRight: 12,
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
  },
  dateText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  descriptionInput: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#333',
    borderWidth: 1,
    borderColor: '#DEE2E6',
    minHeight: 60,
    textAlignVertical: 'top',
  },
  scrollView: {
    flex: 1,
  },
  lineCard: {
    backgroundColor: '#FFF',
    margin: 12,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  lineHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  lineNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  removeButton: {
    padding: 4,
  },
  inputGroup: {
    marginBottom: 12,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#333',
    borderWidth: 1,
    borderColor: '#DEE2E6',
  },
  pickerContainer: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#DEE2E6',
    overflow: 'hidden',
  },
  picker: {
    padding: 12,
    fontSize: 14,
    color: '#333',
    border: 'none',
    outline: 'none',
    backgroundColor: 'transparent',
    width: '100%',
  } as any,
  amountRow: {
    flexDirection: 'row',
  },
  amountInput: {
    textAlign: 'right',
    fontWeight: '600',
  },
  addLineButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFF',
    marginHorizontal: 12,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
  },
  addLineText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  totalsCard: {
    backgroundColor: '#FFF',
    marginHorizontal: 12,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  totalsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  totalLabel: {
    fontSize: 14,
    color: '#666',
  },
  totalAmount: {
    fontSize: 16,
    fontWeight: '600',
  },
  divider: {
    height: 1,
    backgroundColor: '#E0E0E0',
    marginVertical: 8,
  },
  balancedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  balancedText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#28a745',
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#28a745',
    marginHorizontal: 12,
    padding: 16,
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  submitButtonDisabled: {
    backgroundColor: '#CCC',
    opacity: 0.6,
  },
  submitButtonText: {
    marginLeft: 8,
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFF',
  },
  bottomSpacer: {
    height: 20,
  },
});

export default JournalEntryScreen;



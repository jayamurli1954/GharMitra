import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
  FlatList,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {transactionsService} from '../../services/transactionsService';
import {accountingService, AccountCode} from '../../services/accountingService';

type AccountType = 'income' | 'expense' | 'asset' | 'liability';
type PaymentMethod = 'cash' | 'bank';

const AddTransactionScreen = ({navigation}: any) => {
  const [accountType, setAccountType] = useState<AccountType>('expense');
  const [accountCodes, setAccountCodes] = useState<AccountCode[]>([]);
  const [filteredAccountCodes, setFilteredAccountCodes] = useState<AccountCode[]>([]);
  const [selectedAccountCode, setSelectedAccountCode] = useState<AccountCode | null>(null);
  const [showAccountCodeModal, setShowAccountCodeModal] = useState(false);
  const [showAddAccountModal, setShowAddAccountModal] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash');
  const [amount, setAmount] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unitPrice, setUnitPrice] = useState('');
  const [description, setDescription] = useState('');
  // Format date as dd/mm/yyyy
  const formatDateToDDMMYYYY = (dateObj: Date): string => {
    const day = String(dateObj.getDate()).padStart(2, '0');
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const year = dateObj.getFullYear();
    return `${day}/${month}/${year}`;
  };
  
  const [date, setDate] = useState(formatDateToDDMMYYYY(new Date()));
  const [loading, setLoading] = useState(false);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [cashBalance, setCashBalance] = useState<number | null>(null);
  const [bankBalance, setBankBalance] = useState<number | null>(null);

  // New account code form
  const [newAccountCode, setNewAccountCode] = useState('');
  const [newAccountName, setNewAccountName] = useState('');
  const [newAccountDescription, setNewAccountDescription] = useState('');
  const [newAccountOpeningBalance, setNewAccountOpeningBalance] = useState('');
  
  // Chart of accounts autocomplete
  const [chartSuggestions, setChartSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadAccountCodes();
    loadCashAndBankBalances();
    
    // Add header button for Opening Balance
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity
          onPress={() => navigation.navigate('OpeningBalance')}
          style={{marginRight: 16}}
          activeOpacity={0.7}>
          <Icon name="wallet-outline" size={24} color="#fff" />
        </TouchableOpacity>
      ),
    });
  }, [navigation]);

  useEffect(() => {
    // Filter account codes by selected type
    const filtered = accountCodes.filter(ac => {
      // Handle both string and enum types
      const acType = typeof ac.type === 'string' ? ac.type : String(ac.type);
      return acType === accountType;
    });
    
    setFilteredAccountCodes(filtered);
    setSelectedAccountCode(null); // Reset selection when type changes
  }, [accountType, accountCodes]);

  const loadAccountCodes = async () => {
    setLoadingAccounts(true);
    try {
      const codes = await accountingService.getAccountCodes();
      setAccountCodes(codes);
      
      // If no account codes exist, show initialization option
      if (codes.length === 0) {
        Alert.alert(
          'No Account Codes Found',
          'Account codes need to be initialized first. Would you like to initialize the chart of accounts now?',
          [
            {text: 'Cancel', style: 'cancel'},
            {
              text: 'Initialize',
              onPress: handleInitializeAccountCodes,
            },
          ],
        );
      }
    } catch (error: any) {
      console.error('❌ Error loading account codes:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load account codes';
      console.error('Error details:', {
        status: error.response?.status,
        message: errorMessage,
        data: error.response?.data,
      });
      
      // If no account codes loaded, show initialization option
      if (accountCodes.length === 0 || error.response?.status === 404) {
        // Don't show alert here, let the UI handle it - it will show the initialization prompt
      } else {
        Alert.alert(
          'Error Loading Account Codes',
          errorMessage + '\n\nPlease try again or initialize the chart of accounts.',
          [
            {text: 'OK', style: 'cancel'},
            {
              text: 'Initialize',
              onPress: handleInitializeAccountCodes,
            },
          ],
        );
      }
    } finally {
      setLoadingAccounts(false);
    }
  };

  const handleInitializeAccountCodes = async () => {
    setLoading(true);
    try {
      // Check if account codes exist
      const existingCodes = await accountingService.getAccountCodes();
      
      if (existingCodes.length > 0) {
        // Show details about existing codes
        const codeList = existingCodes.slice(0, 5).map(c => `• ${c.code} - ${c.name}`).join('\n');
        const moreText = existingCodes.length > 5 ? `\n... and ${existingCodes.length - 5} more` : '';
        
        // Ask if user wants to delete existing codes first
        Alert.alert(
          'Account Codes Already Exist',
          `Found ${existingCodes.length} existing account code(s):\n${codeList}${moreText}\n\nTo properly initialize the chart of accounts with all 60+ pre-configured codes, you need to delete the existing ones first.\n\n⚠️ Warning: This will delete all existing account codes. Make sure no transactions are using them.`,
          [
            {text: 'Cancel', style: 'cancel'},
            {
              text: 'Delete & Reinitialize',
              style: 'destructive',
              onPress: async () => {
                try {
                  setLoading(true);
                  // Delete all account codes
                  const deleteResult = await accountingService.deleteAllAccountCodes();
                  console.log('✅ Deleted account codes:', deleteResult);
                  
                  // Then initialize
                  const result = await accountingService.initializeChartOfAccounts();
                  Alert.alert(
                    'Success',
                    `Chart of accounts reinitialized!\n\n${result.accounts_created} account codes created, including:\n• Asset codes (1000-1999)\n• Liability codes (2000-2999)\n• Capital codes (3000-3999)\n• Income codes (4000-4999)\n• Expense codes (5000-5999)\n\nYou can now select from the pre-loaded codes when adding transactions.`,
                  );
                  await loadAccountCodes();
                } catch (deleteError: any) {
                  console.error('❌ Error deleting/reinitializing:', deleteError);
                  const errorMessage =
                    deleteError.response?.data?.detail ||
                    deleteError.message ||
                    'Failed to delete or reinitialize account codes';
                  
                  // Check if error is about transactions using account codes
                  if (errorMessage.includes('transactions are using')) {
                    Alert.alert(
                      'Cannot Delete',
                      errorMessage + '\n\nPlease delete or update transactions that use account codes first, then try again.',
                    );
                  } else {
                    Alert.alert('Error', errorMessage);
                  }
                } finally {
                  setLoading(false);
                }
              },
            },
          ],
        );
      } else {
        // No existing codes, just initialize
        const result = await accountingService.initializeChartOfAccounts();
        Alert.alert(
          'Success',
          `Chart of accounts initialized!\n\n${result.accounts_created} account codes created, including:\n• Asset codes (1000-1999)\n• Liability codes (2000-2999)\n• Capital codes (3000-3999)\n• Income codes (4000-4999)\n• Expense codes (5000-5999)\n\nYou can now select from the pre-loaded codes when adding transactions.`,
        );
        await loadAccountCodes();
      }
    } catch (error: any) {
      console.error('Error initializing account codes:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to initialize account codes';
      
      // Check if error is about already initialized
      if (errorMessage.includes('already initialized')) {
        Alert.alert(
          'Already Initialized',
          errorMessage + '\n\nTo reinitialize, you need to delete existing account codes first. Use the "Delete & Reinitialize" option.',
        );
      } else {
        Alert.alert('Error', errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadCashAndBankBalances = async () => {
    try {
      // Get Cash in Hand (code 1010)
      try {
        const cashAccount = await accountingService.getAccountCode('1010');
        setCashBalance(cashAccount.current_balance);
      } catch (error) {
        console.log('Cash account not found');
      }

      // Get Bank Account (code 1000)
      try {
        const bankAccount = await accountingService.getAccountCode('1000');
        setBankBalance(bankAccount.current_balance);
      } catch (error) {
        console.log('Bank account not found');
      }
    } catch (error) {
      console.error('Error loading balances:', error);
    }
  };

  const handleAddNewAccountCode = async () => {
    if (!newAccountCode.trim() || !newAccountName.trim()) {
      Alert.alert('Error', 'Please enter account code and name');
      return;
    }

    if (newAccountCode.length < 4 || newAccountCode.length > 10) {
      Alert.alert('Error', 'Account code must be 4-10 characters');
      return;
    }

    setLoading(true);
    try {
      const newAccount = await accountingService.createAccountCode({
        code: newAccountCode.trim(),
        name: newAccountName.trim(),
        type: accountType,
        description: newAccountDescription.trim() || undefined,
        opening_balance: parseFloat(newAccountOpeningBalance) || 0,
      });

      // Reload account codes
      await loadAccountCodes();
      
      // Select the newly created account
      setSelectedAccountCode(newAccount);
      setShowAddAccountModal(false);
      
      // Reset form
      setNewAccountCode('');
      setNewAccountName('');
      setNewAccountDescription('');
      setNewAccountOpeningBalance('');

      Alert.alert('Success', 'Account code created successfully');
    } catch (error: any) {
      console.error('Error creating account code:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to create account code';
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedAccountCode) {
      Alert.alert('Error', 'Please select an account code');
      return;
    }

    if (!amount || !description.trim()) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }

    const amountNum = parseFloat(amount);
    if (isNaN(amountNum) || amountNum <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    // For assets and liabilities, we need special handling
    // For now, we'll treat them as income/expense based on the account type
    let transactionType: 'income' | 'expense' = 'expense';
    
    if (accountType === 'income') {
      transactionType = 'income';
    } else if (accountType === 'expense') {
      transactionType = 'expense';
    } else if (accountType === 'asset') {
      // Asset increase = income, asset decrease = expense
      // For now, we'll use expense for asset transactions (purchases)
      transactionType = 'expense';
    } else if (accountType === 'liability') {
      // Liability increase = expense, liability decrease = income
      // For now, we'll use expense for liability transactions (payments)
      transactionType = 'expense';
    }

    // Validate cash balance for cash payments
    if (paymentMethod === 'cash' && transactionType === 'expense') {
      if (cashBalance === null) {
        Alert.alert(
          'Warning',
          'Cash balance not found. Please ensure Cash in Hand account (1010) exists.\n\nWould you like to add an opening balance?',
          [
            {
              text: 'Cancel',
              style: 'cancel',
            },
            {
              text: 'Add Opening Balance',
              onPress: () => navigation.navigate('OpeningBalance'),
            },
          ],
        );
        return;
      }
      if (cashBalance < amountNum) {
        Alert.alert(
          'Insufficient Balance',
          `Insufficient cash balance.\nAvailable: ₹${cashBalance.toFixed(2)}\nRequired: ₹${amountNum.toFixed(2)}\nShortfall: ₹${(amountNum - cashBalance).toFixed(2)}\n\nWould you like to add an opening balance?`,
          [
            {
              text: 'Cancel',
              style: 'cancel',
            },
            {
              text: 'Add Opening Balance',
              onPress: () => navigation.navigate('OpeningBalance'),
            },
          ],
        );
        return;
      }
    }

    setLoading(true);
    try {
      // Validate and convert date from DD/MM/YYYY to format backend expects
      let transactionDate = date;
      const dateRegex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
      const dateMatch = date.match(dateRegex);
      
      if (!dateMatch) {
        Alert.alert('Error', 'Please enter a valid date in DD/MM/YYYY format');
        setLoading(false);
        return;
      }
      
      const [, day, month, year] = dateMatch;
      const dayNum = parseInt(day, 10);
      const monthNum = parseInt(month, 10);
      const yearNum = parseInt(year, 10);
      
      // Validate date values
      if (monthNum < 1 || monthNum > 12) {
        Alert.alert('Error', 'Invalid month. Month must be between 01 and 12');
        setLoading(false);
        return;
      }
      
      if (dayNum < 1 || dayNum > 31) {
        Alert.alert('Error', 'Invalid day. Day must be between 01 and 31');
        setLoading(false);
        return;
      }
      
      // Check if date is valid (e.g., not 31/02/2025)
      const dateObj = new Date(yearNum, monthNum - 1, dayNum);
      if (dateObj.getDate() !== dayNum || dateObj.getMonth() !== monthNum - 1 || dateObj.getFullYear() !== yearNum) {
        Alert.alert('Error', 'Invalid date. Please check the day, month, and year');
        setLoading(false);
        return;
      }
      
      // Convert to DD/MM/YYYY format for backend (backend will parse it)
      transactionDate = `${day}/${month}/${year}`;

      const transactionData: any = {
        type: transactionType,
        category: selectedAccountCode.name,
        description: description.trim(),
        date: transactionDate,
      };

      // Add account_code only if it exists
      if (selectedAccountCode.code) {
        transactionData.account_code = selectedAccountCode.code;
      }

      // If quantity and unit_price are provided and valid, send those values
      // Only parse if the strings are not empty
      const hasQuantity = quantity && quantity.trim() !== '';
      const hasUnitPrice = unitPrice && unitPrice.trim() !== '';
      
      if (hasQuantity && hasUnitPrice) {
        const quantityNum = parseFloat(quantity);
        const unitPriceNum = parseFloat(unitPrice);
        
        if (!isNaN(quantityNum) && !isNaN(unitPriceNum) && quantityNum > 0 && unitPriceNum > 0) {
          transactionData.quantity = quantityNum;
          transactionData.unit_price = unitPriceNum;
        } else {
          // Invalid quantity/unit_price, use amount instead
          transactionData.amount = amountNum;
        }
      } else {
        // No quantity/unit_price provided, send direct amount
        transactionData.amount = amountNum;
      }

      // Add payment_method if it's an expense
      if (transactionType === 'expense' && paymentMethod) {
        transactionData.payment_method = paymentMethod;
      }

      console.log('Sending transaction data:', JSON.stringify(transactionData, null, 2));
      await transactionsService.createTransaction(transactionData);

      Alert.alert('Success', 'Transaction added successfully', [
        {
          text: 'OK',
          onPress: () => {
            navigation.goBack();
          },
        },
      ]);
    } catch (error: any) {
      console.error('Error adding transaction:', error);
      console.error('Error response:', error.response?.data);
      
      // Extract detailed error message
      let errorMessage = 'Failed to add transaction. Please try again.';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle Pydantic validation errors
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const validationErrors = errorData.detail.map((err: any) => {
            const field = err.loc?.join('.') || 'field';
            return `${field}: ${err.msg}`;
          }).join('\n');
          errorMessage = `Validation Error:\n${validationErrors}`;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const renderAccountTypeButton = (
    type: AccountType,
    label: string,
    icon: string,
    color: string,
  ) => (
    <TouchableOpacity
      key={type}
      style={[
        styles.typeButton,
        accountType === type && {borderColor: color, backgroundColor: `${color}15`},
      ]}
      onPress={() => setAccountType(type)}
      activeOpacity={0.7}>
      <Icon
        name={icon}
        size={24}
        color={accountType === type ? color : '#999'}
      />
      <Text
        style={[
          styles.typeButtonText,
          accountType === type && {color: color, fontWeight: '700'},
        ]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container}>
      {/* Account Type Selector */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account Type *</Text>
        <View style={styles.typeSelector}>
          {[
            {type: 'income' as AccountType, label: 'Income', icon: 'arrow-down-circle', color: '#4CAF50'},
            {type: 'expense' as AccountType, label: 'Expense', icon: 'arrow-up-circle', color: '#F44336'},
            {type: 'asset' as AccountType, label: 'Asset', icon: 'business', color: '#2196F3'},
            {type: 'liability' as AccountType, label: 'Liability', icon: 'card', color: '#FF9800'},
          ].map(({type, label, icon, color}) => (
            <TouchableOpacity
              key={type}
              style={[
                styles.typeButton,
                accountType === type && {borderColor: color, backgroundColor: `${color}15`},
              ]}
              onPress={() => setAccountType(type)}
              activeOpacity={0.7}>
              <Icon
                name={icon}
                size={24}
                color={accountType === type ? color : '#999'}
              />
              <Text
                style={[
                  styles.typeButtonText,
                  accountType === type && {color: color, fontWeight: '700'},
                ]}>
                {label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Account Code Selection */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Account Code *</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowAddAccountModal(true)}
            activeOpacity={0.7}>
            <Icon name="add" size={20} color="#007AFF" />
            <Text style={styles.addButtonText}>Add New</Text>
          </TouchableOpacity>
        </View>

        {loadingAccounts ? (
          <ActivityIndicator size="small" color="#007AFF" style={styles.loader} />
        ) : accountCodes.length === 0 ? (
          <View style={styles.emptyAccountCodesContainer}>
            <Icon name="alert-circle" size={48} color="#FF9800" />
            <Text style={styles.emptyAccountCodesText}>
              No account codes found. Please initialize chart of accounts first.
            </Text>
            <Text style={styles.emptyAccountCodesSubtext}>
              This will create 60+ pre-configured account codes for your society.
            </Text>
            <TouchableOpacity
              style={styles.initializeButton}
              onPress={handleInitializeAccountCodes}
              disabled={loading}
              activeOpacity={0.7}>
              {loading ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <Icon name="add" size={20} color="#FFF" />
              )}
              <Text style={styles.initializeButtonText}>
                {loading ? 'Initializing...' : 'Initialize Chart of Accounts'}
              </Text>
            </TouchableOpacity>
          </View>
        ) : accountCodes.length < 10 ? (
          <View style={styles.emptyAccountCodesContainer}>
            <Icon name="warning" size={48} color="#FF9800" />
            <Text style={styles.emptyAccountCodesText}>
              Only {accountCodes.length} account code(s) found.
            </Text>
            <Text style={styles.emptyAccountCodesSubtext}>
              The chart of accounts should have 60+ codes. It appears initialization didn't complete properly. You can delete existing codes and reinitialize.
            </Text>
            <TouchableOpacity
              style={styles.initializeButton}
              onPress={handleInitializeAccountCodes}
              disabled={loading}
              activeOpacity={0.7}>
              {loading ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <Icon name="refresh" size={20} color="#FFF" />
              )}
              <Text style={styles.initializeButtonText}>
                {loading ? 'Reinitializing...' : 'Delete & Reinitialize Chart of Accounts'}
              </Text>
            </TouchableOpacity>
          </View>
        ) : filteredAccountCodes.length === 0 ? (
          <View style={styles.emptyAccountCodesContainer}>
            <Icon name="alert-circle" size={24} color="#FF9800" />
            <Text style={styles.emptyAccountCodesText}>
              No {accountType} account codes found.
            </Text>
            <Text style={styles.emptyAccountCodesSubtext}>
              {accountCodes.length > 0
                ? `You have ${accountCodes.length} total account codes, but none are of type "${accountType}".`
                : 'Please initialize chart of accounts or add a new account code.'}
            </Text>
            {accountCodes.length > 0 && (
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => setShowAddAccountModal(true)}
                activeOpacity={0.7}>
                <Icon name="add" size={20} color="#007AFF" />
                <Text style={styles.addButtonText}>Add New {accountType} Code</Text>
              </TouchableOpacity>
            )}
          </View>
        ) : (
          <View>
            <TouchableOpacity
              style={styles.dropdown}
              onPress={() => setShowAccountCodeModal(true)}
              activeOpacity={0.7}>
              <Text
                style={[
                  styles.dropdownText,
                  !selectedAccountCode && styles.dropdownPlaceholder,
                ]}>
                {selectedAccountCode
                  ? `${selectedAccountCode.code} - ${selectedAccountCode.name}`
                  : `Select Account Code (${filteredAccountCodes.length} available)`}
              </Text>
              <Icon name="chevron-down" size={20} color="#666" />
            </TouchableOpacity>
            <Text style={styles.hintText}>
              {filteredAccountCodes.length} {accountType} code{filteredAccountCodes.length !== 1 ? 's' : ''} available
            </Text>
          </View>
        )}

        {selectedAccountCode && selectedAccountCode.description && (
          <Text style={styles.accountDescription}>
            {selectedAccountCode.description}
          </Text>
        )}
      </View>

      {/* Payment Method */}
      {(accountType === 'expense' || accountType === 'liability') && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Payment Method *</Text>
          <View style={styles.paymentMethodContainer}>
            <TouchableOpacity
              key="cash"
              style={[
                styles.paymentMethodButton,
                paymentMethod === 'cash' && styles.paymentMethodButtonActive,
              ]}
              onPress={() => setPaymentMethod('cash')}
              activeOpacity={0.7}>
              <Icon
                name="cash"
                size={24}
                color={paymentMethod === 'cash' ? '#4CAF50' : '#999'}
              />
              <Text
                style={[
                  styles.paymentMethodText,
                  paymentMethod === 'cash' && styles.paymentMethodTextActive,
                ]}>
                Cash
              </Text>
              {cashBalance !== null && (
                <Text style={styles.balanceText}>
                  ₹{cashBalance.toFixed(2)}
                </Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              key="bank"
              style={[
                styles.paymentMethodButton,
                paymentMethod === 'bank' && styles.paymentMethodButtonActive,
              ]}
              onPress={() => setPaymentMethod('bank')}
              activeOpacity={0.7}>
              <Icon
                name="card"
                size={24}
                color={paymentMethod === 'bank' ? '#2196F3' : '#999'}
              />
              <Text
                style={[
                  styles.paymentMethodText,
                  paymentMethod === 'bank' && styles.paymentMethodTextActive,
                ]}>
                Bank
              </Text>
              {bankBalance !== null && (
                <Text style={styles.balanceText}>
                  ₹{bankBalance.toFixed(2)}
                </Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Quantity and Price Fields - Always visible for income and expense */}
      {(accountType === 'income' || accountType === 'expense') && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quantity & Price (Optional)</Text>
          <View style={styles.qtyPriceContainer}>
            <View style={[styles.inputContainer, {flex: 1}]}>
              <Icon name="layers-outline" size={18} color="#666" style={{marginRight: 8}} />
              <TextInput
                style={[styles.input, {flex: 1}]}
                placeholder="Quantity"
                placeholderTextColor="#999"
                value={quantity}
                onChangeText={(text) => {
                  setQuantity(text);
                  // Auto-calculate amount if both qty and price are entered
                  const qty = parseFloat(text);
                  const price = parseFloat(unitPrice);
                  if (!isNaN(qty) && qty > 0 && !isNaN(price) && price > 0) {
                    setAmount((qty * price).toFixed(2));
                  } else if (text === '' || isNaN(qty) || qty <= 0) {
                    // If qty is cleared, don't auto-calculate
                    // Only clear amount if it was calculated from qty×price
                    // Otherwise, keep the manually entered amount
                  }
                }}
                keyboardType="decimal-pad"
              />
            </View>
            <Text style={styles.multiplySymbol}>×</Text>
            <View style={[styles.inputContainer, {flex: 1}]}>
              <Text style={styles.currencySymbol}>₹</Text>
              <TextInput
                style={[styles.input, {flex: 1}]}
                placeholder="Unit Price"
                placeholderTextColor="#999"
                value={unitPrice}
                onChangeText={(text) => {
                  setUnitPrice(text);
                  // Auto-calculate amount if both qty and price are entered
                  const qty = parseFloat(quantity);
                  const price = parseFloat(text);
                  if (!isNaN(qty) && qty > 0 && !isNaN(price) && price > 0) {
                    setAmount((qty * price).toFixed(2));
                  } else if (text === '' || isNaN(price) || price <= 0) {
                    // If price is cleared, don't auto-calculate
                    // Only clear amount if it was calculated from qty×price
                    // Otherwise, keep the manually entered amount
                  }
                }}
                keyboardType="decimal-pad"
              />
            </View>
          </View>
          <Text style={styles.hintText}>
            Optional: Enter quantity and price to auto-calculate amount
          </Text>
        </View>
      )}

      {/* Amount Input */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Amount *</Text>
        <View style={styles.inputContainer}>
          <Text style={styles.currencySymbol}>₹</Text>
          <TextInput
            style={styles.input}
            placeholder="0.00"
            placeholderTextColor="#999"
            value={amount}
            onChangeText={setAmount}
            keyboardType="decimal-pad"
          />
        </View>
        {(accountType === 'income' || accountType === 'expense') && quantity && unitPrice && parseFloat(quantity) > 0 && parseFloat(unitPrice) > 0 && (
          <Text style={styles.hintText}>
            Calculated: {quantity} × ₹{unitPrice} = ₹{amount || '0.00'}
          </Text>
        )}
      </View>

      {/* Date */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Date * (DD/MM/YYYY)</Text>
        <TextInput
          style={styles.input}
          placeholder="DD/MM/YYYY"
          placeholderTextColor="#999"
          value={date}
          onChangeText={(text) => {
            // Allow only digits and slashes, format as user types
            let formatted = text.replace(/[^\d/]/g, '');
            // Auto-format: add slashes at positions 2 and 5
            if (formatted.length > 2 && formatted[2] !== '/') {
              formatted = formatted.slice(0, 2) + '/' + formatted.slice(2);
            }
            if (formatted.length > 5 && formatted[5] !== '/') {
              formatted = formatted.slice(0, 5) + '/' + formatted.slice(5);
            }
            // Limit to 10 characters (DD/MM/YYYY)
            if (formatted.length <= 10) {
              setDate(formatted);
            }
          }}
          keyboardType="numeric"
          maxLength={10}
        />
        <Text style={styles.hintText}>
          Format: DD/MM/YYYY (e.g., 20/11/2025)
        </Text>
      </View>

      {/* Description */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Description *</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Enter transaction description"
          placeholderTextColor="#999"
          value={description}
          onChangeText={setDescription}
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />
      </View>

      {/* Submit Button */}
      <View style={styles.section}>
        <TouchableOpacity
          style={[styles.submitButton, loading && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={loading}
          activeOpacity={0.7}>
          {loading ? (
            <ActivityIndicator size="small" color="#FFF" />
          ) : (
            <Icon name="checkmark-circle" size={24} color="#FFF" />
          )}
          <Text style={styles.submitButtonText}>
            {loading ? 'Adding...' : 'Add Transaction'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Account Code Selection Modal */}
      <Modal
        visible={showAccountCodeModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowAccountCodeModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Account Code</Text>
              <TouchableOpacity
                onPress={() => setShowAccountCodeModal(false)}
                activeOpacity={0.7}>
                <Icon name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            <FlatList
              data={filteredAccountCodes}
              keyExtractor={(item, index) => item.id?.toString() || item.code || `account-${index}`}
              renderItem={({item}) => (
                <TouchableOpacity
                  style={[
                    styles.accountCodeItem,
                    selectedAccountCode?.id === item.id &&
                      styles.accountCodeItemSelected,
                  ]}
                  onPress={() => {
                    setSelectedAccountCode(item);
                    setShowAccountCodeModal(false);
                  }}
                  activeOpacity={0.7}>
                  <View style={styles.accountCodeInfo}>
                    <Text style={styles.accountCodeCode}>{item.code}</Text>
                    <Text style={styles.accountCodeName}>{item.name}</Text>
                  </View>
                  {item.description && (
                    <Text style={styles.accountCodeDesc}>{item.description}</Text>
                  )}
                  <Text style={styles.accountCodeBalance}>
                    Balance: ₹{item.current_balance.toFixed(2)}
                  </Text>
                </TouchableOpacity>
              )}
              ListEmptyComponent={
                <View style={styles.emptyState}>
                  <Text style={styles.emptyStateText}>
                    No account codes found for {accountType}
                  </Text>
                  <TouchableOpacity
                    style={styles.addNewButton}
                    onPress={() => {
                      setShowAccountCodeModal(false);
                      setShowAddAccountModal(true);
                    }}>
                    <Text style={styles.addNewButtonText}>Add New Account Code</Text>
                  </TouchableOpacity>
                </View>
              }
            />
          </View>
        </View>
      </Modal>

      {/* Add New Account Code Modal */}
      <Modal
        visible={showAddAccountModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowAddAccountModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add New Account Code</Text>
              <TouchableOpacity
                onPress={() => setShowAddAccountModal(false)}
                activeOpacity={0.7}>
                <Icon name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalScroll}>
              <Text style={styles.modalLabel}>Account Type</Text>
              <Text style={styles.modalValue}>{accountType.toUpperCase()}</Text>

              <Text style={styles.modalLabel}>Account Code *</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="e.g., 4011, 5111"
                value={newAccountCode}
                onChangeText={setNewAccountCode}
                maxLength={10}
              />
              <Text style={styles.modalHint}>
                4-10 characters (e.g., 4011 for Water Charges Income)
              </Text>

              <Text style={styles.modalLabel}>Account Name *</Text>
              <View style={styles.autocompleteContainer}>
                <TextInput
                  style={styles.modalInput}
                  placeholder="Type 3+ letters to search chart of accounts..."
                  value={newAccountName}
                  onChangeText={(text) => {
                    setNewAccountName(text);
                    // Clear previous timeout
                    if (searchTimeout) {
                      clearTimeout(searchTimeout);
                    }
                    
                    // Search after 500ms delay (debounce)
                    if (text.length >= 3) {
                      const timeout = setTimeout(async () => {
                        try {
                          const suggestions = await accountingService.searchChartOfAccounts(
                            text,
                            accountType
                          );
                          setChartSuggestions(suggestions);
                          setShowSuggestions(suggestions.length > 0);
                        } catch (error) {
                          console.error('Error searching chart of accounts:', error);
                        }
                      }, 500);
                      setSearchTimeout(timeout);
                    } else {
                      setChartSuggestions([]);
                      setShowSuggestions(false);
                    }
                  }}
                  onFocus={() => {
                    if (newAccountName.length >= 3 && chartSuggestions.length > 0) {
                      setShowSuggestions(true);
                    }
                  }}
                  onBlur={() => {
                    // Delay hiding to allow selection
                    setTimeout(() => setShowSuggestions(false), 200);
                  }}
                />
                {showSuggestions && chartSuggestions.length > 0 && (
                  <View style={styles.suggestionsContainer}>
                    <FlatList
                      data={chartSuggestions}
                      keyExtractor={(item, index) => `${item.name}-${index}`}
                      renderItem={({item}) => (
                        <TouchableOpacity
                          style={styles.suggestionItem}
                          onPress={() => {
                            setNewAccountName(item.name);
                            setNewAccountDescription(item.description || '');
                            if (item.suggested_code) {
                              // Generate a code based on suggested code prefix
                              // User can still edit it
                              const codePrefix = item.suggested_code;
                              // Try to find next available code in that range
                              const existingCodes = accountCodes
                                .filter(ac => ac.code.startsWith(codePrefix))
                                .map(ac => parseInt(ac.code))
                                .filter(n => !isNaN(n));
                              const maxCode = existingCodes.length > 0 
                                ? Math.max(...existingCodes) 
                                : parseInt(codePrefix + '000');
                              const suggestedCode = String(maxCode + 1).padStart(4, '0');
                              setNewAccountCode(suggestedCode);
                            }
                            setShowSuggestions(false);
                          }}>
                          <Text style={styles.suggestionName}>{item.name}</Text>
                          <Text style={styles.suggestionDesc} numberOfLines={2}>
                            {item.description}
                          </Text>
                          {item.sub_category && (
                            <Text style={styles.suggestionCategory}>
                              {item.category} → {item.sub_category}
                            </Text>
                          )}
                        </TouchableOpacity>
                      )}
                      style={styles.suggestionsList}
                      nestedScrollEnabled
                    />
                  </View>
                )}
              </View>

              <Text style={styles.modalLabel}>Description (Optional)</Text>
              <TextInput
                style={[styles.modalInput, styles.modalTextArea]}
                placeholder="Brief description of this account"
                value={newAccountDescription}
                onChangeText={setNewAccountDescription}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
              />

              <Text style={styles.modalLabel}>Opening Balance (Optional)</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="0.00"
                value={newAccountOpeningBalance}
                onChangeText={setNewAccountOpeningBalance}
                keyboardType="decimal-pad"
              />
              <Text style={styles.modalHint}>
                Enter opening balance if migrating from legacy system
              </Text>

              <TouchableOpacity
                style={[styles.modalSubmitButton, loading && styles.modalSubmitButtonDisabled]}
                onPress={handleAddNewAccountCode}
                disabled={loading}
                activeOpacity={0.7}>
                {loading ? (
                  <ActivityIndicator size="small" color="#FFF" />
                ) : (
                  <Icon name="checkmark-circle" size={20} color="#FFF" />
                )}
                <Text style={styles.modalSubmitButtonText}>
                  {loading ? 'Creating...' : 'Create Account Code'}
                </Text>
              </TouchableOpacity>
            </ScrollView>
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
  section: {
    backgroundColor: '#FFF',
    padding: 20,
    marginBottom: 1,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 12,
  },
  typeSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  typeButton: {
    flex: 1,
    minWidth: '45%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    padding: 15,
    borderWidth: 2,
    borderColor: '#E5E5EA',
    gap: 8,
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  dropdown: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    padding: 15,
    borderWidth: 1.5,
    borderColor: '#E5E5EA',
  },
  dropdownText: {
    fontSize: 16,
    color: '#1D1D1F',
    flex: 1,
  },
  dropdownPlaceholder: {
    color: '#999',
  },
  accountDescription: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
    fontStyle: 'italic',
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  addButtonText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  paymentMethodContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  paymentMethodButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    padding: 20,
    borderWidth: 2,
    borderColor: '#E5E5EA',
    gap: 8,
  },
  paymentMethodButtonActive: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD',
  },
  paymentMethodText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  paymentMethodTextActive: {
    color: '#007AFF',
  },
  balanceText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5E5EA',
    paddingHorizontal: 16,
  },
  currencySymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginRight: 8,
  },
  input: {
    flex: 1,
    height: 50,
    fontSize: 16,
    color: '#1D1D1F',
  },
  textArea: {
    height: 100,
    paddingTop: 15,
    paddingHorizontal: 15,
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5E5EA',
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 16,
    height: 56,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  submitButtonDisabled: {
    backgroundColor: '#A0C4FF',
  },
  submitButtonText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '700',
  },
  loader: {
    padding: 20,
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
    paddingBottom: 20,
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
  modalScroll: {
    padding: 20,
  },
  modalLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D1D1F',
    marginTop: 16,
    marginBottom: 8,
  },
  modalValue: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
    marginBottom: 8,
  },
  modalInput: {
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    padding: 15,
    borderWidth: 1.5,
    borderColor: '#E5E5EA',
    fontSize: 16,
    color: '#1D1D1F',
  },
  modalTextArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  modalHint: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontStyle: 'italic',
  },
  modalSubmitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 15,
    marginTop: 24,
    gap: 8,
  },
  modalSubmitButtonDisabled: {
    backgroundColor: '#A0C4FF',
  },
  modalSubmitButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '700',
  },
  autocompleteContainer: {
    position: 'relative',
    zIndex: 10,
  },
  suggestionsContainer: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: '#FFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    marginTop: 4,
    maxHeight: 200,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 1000,
  },
  suggestionsList: {
    maxHeight: 200,
  },
  suggestionItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  suggestionName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  suggestionDesc: {
    fontSize: 13,
    color: '#666',
    marginBottom: 4,
  },
  suggestionCategory: {
    fontSize: 11,
    color: '#007AFF',
    fontStyle: 'italic',
  },
  accountCodeItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  accountCodeItemSelected: {
    backgroundColor: '#E3F2FD',
  },
  accountCodeInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 4,
  },
  accountCodeCode: {
    fontSize: 14,
    fontWeight: '700',
    color: '#007AFF',
    minWidth: 60,
  },
  accountCodeName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    flex: 1,
  },
  accountCodeDesc: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  accountCodeBalance: {
    fontSize: 12,
    color: '#4CAF50',
    marginTop: 4,
    fontWeight: '600',
  },
  emptyState: {
    padding: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 20,
    textAlign: 'center',
  },
  addNewButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  addNewButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyAccountCodesContainer: {
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FFB74D',
    gap: 12,
  },
  emptyAccountCodesText: {
    fontSize: 14,
    color: '#E65100',
    textAlign: 'center',
    fontWeight: '500',
    marginTop: 8,
  },
  emptyAccountCodesSubtext: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 12,
  },
  hintText: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
    fontStyle: 'italic',
  },
  initializeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FF9800',
    borderRadius: 8,
    paddingHorizontal: 20,
    paddingVertical: 12,
    marginTop: 8,
    gap: 8,
  },
  initializeButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  qtyPriceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  multiplySymbol: {
    fontSize: 20,
    fontWeight: '700',
    color: '#666',
  },
  calculatedAmountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E7F8EE',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    gap: 8,
  },
  calculatedAmountLabel: {
    fontSize: 14,
    color: '#2E7D32',
    fontWeight: '600',
  },
  calculatedAmount: {
    fontSize: 18,
    color: '#2E7D32',
    fontWeight: '700',
    flex: 1,
    textAlign: 'right',
  },
});

export default AddTransactionScreen;

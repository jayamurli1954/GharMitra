import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {transactionsService, Transaction} from '../../services/transactionsService';
import {authService} from '../../services/authService';

const AccountingListScreen = ({navigation}: any) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'income' | 'expense'>('all');
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    checkAdminStatus();
    loadTransactions();
    // Add header button for Opening Balance
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity
          onPress={() => navigation.navigate('OpeningBalance')}
          style={{marginRight: 16}}
          activeOpacity={0.7}>
          <Icon name="wallet-outline" size={24} color="#FFF" />
        </TouchableOpacity>
      ),
    });
  }, [filter, navigation]);

  const checkAdminStatus = async () => {
    try {
      const user = await authService.getStoredUser();
      setIsAdmin(user?.role === 'admin' || user?.role === 'super_admin');
    } catch (error) {
      console.error('Error checking admin status:', error);
      setIsAdmin(false);
    }
  };

  const loadTransactions = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        limit: 50,
      };

      if (filter !== 'all') {
        params.type = filter;
      }

      const transactionsList = await transactionsService.getTransactions(params);
      setTransactions(transactionsList);
    } catch (error: any) {
      console.error('Error loading transactions:', error);
      setError('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  const renderTransaction = ({item}: {item: Transaction}) => (
    <TouchableOpacity
      style={styles.transactionCard}
      onPress={() =>
        navigation.navigate('TransactionDetail', {transactionId: item.id})
      }
      activeOpacity={0.7}>
      <View
        style={[
          styles.transactionIcon,
          item.type === 'income' ? styles.incomeIcon : styles.expenseIcon,
        ]}>
        <Icon
          name={item.type === 'income' ? 'arrow-down' : 'arrow-up'}
          size={24}
          color="#FFF"
        />
      </View>
      <View style={styles.transactionDetails}>
        <Text style={styles.transactionCategory}>{item.category}</Text>
        <Text style={styles.transactionDescription} numberOfLines={1}>
          {item.description || 'No description'}
        </Text>
        <Text style={styles.transactionDate}>{formatDate(item.date)}</Text>
      </View>
      <Text
        style={[
          styles.transactionAmount,
          item.type === 'income' ? styles.incomeAmount : styles.expenseAmount,
        ]}>
        {item.type === 'income' ? '+' : '-'}
        {formatCurrency(item.amount)}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Opening Balance Card - Visible to all users */}
      <TouchableOpacity
        style={styles.openingBalanceCard}
        onPress={() => navigation.navigate('OpeningBalance')}
        activeOpacity={0.7}>
        <View style={styles.openingBalanceIconContainer}>
          <Icon name="wallet" size={28} color="#007AFF" />
        </View>
        <View style={styles.openingBalanceContent}>
          <Text style={styles.openingBalanceTitle}>Opening Balances</Text>
          <Text style={styles.openingBalanceSubtitle}>
            View and manage account opening balances
          </Text>
        </View>
        <Icon name="chevron-forward" size={24} color="#8E8E93" />
      </TouchableOpacity>

      {loading && transactions.length === 0 ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading transactions...</Text>
        </View>
      ) : (
        <>

      {/* Filter Buttons */}
      <View style={styles.filterContainer}>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'all' && styles.filterButtonActive]}
          onPress={() => setFilter('all')}
          activeOpacity={0.7}>
          <Text
            style={[
              styles.filterButtonText,
              filter === 'all' && styles.filterButtonTextActive,
            ]}>
            All
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'income' && styles.filterButtonActive]}
          onPress={() => setFilter('income')}
          activeOpacity={0.7}>
          <Text
            style={[
              styles.filterButtonText,
              filter === 'income' && styles.filterButtonTextActive,
            ]}>
            Income
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'expense' && styles.filterButtonActive]}
          onPress={() => setFilter('expense')}
          activeOpacity={0.7}>
          <Text
            style={[
              styles.filterButtonText,
              filter === 'expense' && styles.filterButtonTextActive,
            ]}>
            Expenses
          </Text>
        </TouchableOpacity>
      </View>

      {/* Error Message */}
      {error && (
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={24} color="#FF3B30" />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={loadTransactions}
            activeOpacity={0.7}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Transactions List */}
      <FlatList
        data={transactions}
        renderItem={renderTransaction}
        keyExtractor={(item, index) => item.id?.toString() || `transaction-${index}`}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={loadTransactions} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Icon name="document-text-outline" size={60} color="#C7C7CC" />
            <Text style={styles.emptyStateText}>No transactions found</Text>
            <Text style={styles.emptyStateSubtext}>
              {filter !== 'all'
                ? `No ${filter} transactions yet`
                : 'Add your first transaction to get started'}
            </Text>
            {filter === 'all' && (
              <TouchableOpacity
                style={styles.addFirstButton}
                onPress={() => navigation.navigate('AddTransaction')}
                activeOpacity={0.7}>
                <Icon name="add" size={20} color="#FFF" />
                <Text style={styles.addFirstButtonText}>Add Transaction</Text>
              </TouchableOpacity>
            )}
          </View>
        }
      />

      {/* FAB */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('AddTransaction')}
        activeOpacity={0.8}>
        <Icon name="add" size={32} color="#FFF" />
      </TouchableOpacity>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  openingBalanceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  openingBalanceIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  openingBalanceContent: {
    flex: 1,
  },
  openingBalanceTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  openingBalanceSubtitle: {
    fontSize: 13,
    color: '#8E8E93',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 40,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    gap: 12,
  },
  filterButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 10,
    backgroundColor: '#F5F5F7',
    alignItems: 'center',
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
  },
  filterButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#8E8E93',
  },
  filterButtonTextActive: {
    color: '#FFF',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFE5E5',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#FF3B30',
    gap: 12,
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: '#D32F2F',
    fontWeight: '500',
  },
  retryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#FF3B30',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  listContainer: {
    padding: 16,
  },
  transactionCard: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  transactionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  incomeIcon: {
    backgroundColor: '#4CAF50',
  },
  expenseIcon: {
    backgroundColor: '#F44336',
  },
  transactionDetails: {
    flex: 1,
    marginLeft: 12,
  },
  transactionCategory: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  transactionDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  transactionDate: {
    fontSize: 12,
    color: '#C7C7CC',
  },
  transactionAmount: {
    fontSize: 18,
    fontWeight: '700',
  },
  incomeAmount: {
    color: '#4CAF50',
  },
  expenseAmount: {
    color: '#F44336',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 60,
  },
  emptyStateText: {
    fontSize: 18,
    color: '#8E8E93',
    marginTop: 16,
    fontWeight: '600',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#C7C7CC',
    marginTop: 8,
    textAlign: 'center',
  },
  addFirstButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 20,
    gap: 8,
  },
  addFirstButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
});

export default AccountingListScreen;

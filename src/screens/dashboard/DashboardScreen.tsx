import React, { useEffect, useMemo, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Animated,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import MaterialIcon from 'react-native-vector-icons/MaterialCommunityIcons';
import { transactionsService, Transaction, TransactionSummary } from '../../services/transactionsService';
import { getFeatureIcon } from '../../constants/featureIcons';
import { AnimatedIconButton } from '../../components/AnimatedIconButton';
import { SkeletonLoader, SkeletonCard } from '../../components/SkeletonLoader';
import { spacing } from '../../constants/spacing';

// App Icon
const appIcon = require('../../assets/images/app-icon.png');

const DashboardScreen = ({ navigation }: any) => {
  const [totalIncome, setTotalIncome] = useState(0);
  const [totalExpenses, setTotalExpenses] = useState(0);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const quickActions = useMemo(
    () => [
      {
        key: 'generate_bills',
        label: 'Generate Bills',
        featureKey: 'billing',
        onPress: () => navigation.navigate('Maintenance', { screen: 'GenerateBills' }),
      },
      {
        key: 'manage_flats',
        label: 'Manage Flats',
        featureKey: 'flats',
        onPress: () => navigation.navigate('Maintenance', { screen: 'FlatsList' }),
      },
      {
        key: 'add_transaction',
        label: 'Add Transaction',
        featureKey: 'transaction',
        onPress: () => navigation.navigate('Accounting', { screen: 'AddTransaction' }),
      },
      {
        key: 'reports',
        label: 'Financial Reports',
        featureKey: 'reports',
        onPress: () => navigation.navigate('Reports', { screen: 'ReportsDashboard' }),
      },
      {
        key: 'resources',
        label: 'Resources',
        featureKey: 'resources',
        onPress: () => navigation.navigate('ResourceCenter'),
      },
      {
        key: 'settings',
        label: 'Settings',
        featureKey: 'settings',
        onPress: () => navigation.navigate('Maintenance', { screen: 'ApartmentSettings' }),
      },
      {
        key: 'admin_guidelines',
        label: 'Admin Guidelines',
        featureKey: 'admin',
        onPress: () => navigation.navigate('AdminGuidelines' as never),
      },
      {
        key: 'messages',
        label: 'Messages',
        featureKey: 'messages',
        onPress: () => navigation.navigate('Messages'),
      },
      {
        key: 'payments',
        label: 'Payments',
        featureKey: 'payments',
        badgeText: 'Soon',
        onPress: () => navigation.navigate('Payments'),
      },
      {
        key: 'complaints',
        label: 'Complaints',
        featureKey: 'complaints',
        badgeText: 'Soon',
        onPress: () => navigation.navigate('Complaints'),
      },
    ],
    [navigation],
  );

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Calculate date range (last 30 days)
      const toDate = new Date();
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - 30);

      // Format dates as YYYY-MM-DD
      const fromDateStr = fromDate.toISOString().split('T')[0];
      const toDateStr = toDate.toISOString().split('T')[0];

      // Fetch summary statistics
      const summary: TransactionSummary = await transactionsService.getTransactionSummary({
        from_date: fromDateStr,
        to_date: toDateStr,
      });

      setTotalIncome(summary.total_income);
      setTotalExpenses(summary.total_expense);

      // Fetch recent transactions
      const transactions = await transactionsService.getTransactions({
        from_date: fromDateStr,
        to_date: toDateStr,
        limit: 10,
      });

      setRecentTransactions(transactions);
    } catch (error: any) {
      console.error('Error loading dashboard:', error);
      setError('Failed to load dashboard data');
      // Don't show alert, just log error
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  // Skeleton loading state
  if (loading && recentTransactions.length === 0) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.summaryContainer}>
          {/* Skeleton summary cards */}
          {[1, 2, 3].map(i => (
            <View key={i} style={styles.summaryCardSkeleton}>
              <SkeletonLoader width={54} height={54} borderRadius={16} />
              <View style={styles.summarySkeletonContent}>
                <SkeletonLoader width="60%" height={14} style={styles.marginBottom} />
                <SkeletonLoader width="80%" height={28} style={styles.marginBottom} />
                <SkeletonLoader width="40%" height={12} />
              </View>
            </View>
          ))}
        </View>
        <View style={styles.section}>
          <SkeletonLoader width="50%" height={20} style={styles.marginBottom} />
          {[1, 2, 3, 4].map(i => (
            <SkeletonCard key={i} />
          ))}
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={loadDashboardData} />
      }>
      {/* App Header with Icon */}
      <View style={styles.header}>
        <Image source={appIcon} style={styles.appIcon} resizeMode="contain" />
        <Text style={styles.appTitle}>GharMitra</Text>
        <Text style={styles.appSubtitle}>Your Society, Digitally Simplified</Text>
        <Text style={styles.appTagline}>Accounting and Management</Text>
      </View>

      {/* Summary Cards */}
      <View style={styles.summaryContainer}>
        <View style={[styles.summaryCard, styles.incomeCard]}>
          <View style={[styles.summaryIconContainer, styles.summaryIconIncome]}>
            <MaterialIcon name="cash-multiple" size={28} color="#2EAE4E" />
          </View>
          <Text style={styles.summaryLabel}>Total Income</Text>
          <Text style={styles.summaryAmount}>{formatCurrency(totalIncome)}</Text>
          <Text style={styles.summaryPeriod}>Last 30 days</Text>
        </View>

        <View style={[styles.summaryCard, styles.expenseCard]}>
          <View style={[styles.summaryIconContainer, styles.summaryIconExpense]}>
            <MaterialIcon name="credit-card-minus-outline" size={28} color="#E53935" />
          </View>
          <Text style={styles.summaryLabel}>Total Expenses</Text>
          <Text style={styles.summaryAmount}>{formatCurrency(totalExpenses)}</Text>
          <Text style={styles.summaryPeriod}>Last 30 days</Text>
        </View>

        <View style={[styles.summaryCard, styles.balanceCard]}>
          <View style={[styles.summaryIconContainer, styles.summaryIconBalance]}>
            <MaterialIcon name="wallet-outline" size={28} color="#1E88E5" />
          </View>
          <Text style={styles.summaryLabel}>Net Balance</Text>
          <Text
            style={[
              styles.summaryAmount,
              totalIncome - totalExpenses >= 0
                ? styles.positiveBalance
                : styles.negativeBalance,
            ]}>
            {formatCurrency(totalIncome - totalExpenses)}
          </Text>
          <Text style={styles.summaryPeriod}>Current period</Text>
        </View>
      </View>

      {/* Financial Reports Card */}
      <View style={styles.section}>
        <TouchableOpacity
          style={styles.reportsCard}
          onPress={() => navigation.navigate('Reports', { screen: 'ReportsDashboard' })}
          activeOpacity={0.7}>
          <View style={styles.reportsIconContainer}>
            <Icon name="bar-chart" size={32} color="#007AFF" />
          </View>
          <View style={styles.reportsContent}>
            <Text style={styles.reportsTitle}>Financial Reports</Text>
            <Text style={styles.reportsSubtitle}>
              View comprehensive financial reports and analysis
            </Text>
          </View>
          <Icon name="chevron-forward" size={24} color="#8E8E93" />
        </TouchableOpacity>
      </View>

      {/* Recent Transactions */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Transactions</Text>
          <TouchableOpacity
            onPress={() => navigation.navigate('Accounting')}
            activeOpacity={0.7}>
            <Text style={styles.seeAllText}>See All</Text>
          </TouchableOpacity>
        </View>

        {error && (
          <View style={styles.errorContainer}>
            <Icon name="alert-circle-outline" size={24} color="#FF9500" />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={loadDashboardData}
              activeOpacity={0.7}>
              <Text style={styles.retryButtonText}>Retry</Text>
            </TouchableOpacity>
          </View>
        )}

        {!error && recentTransactions.length === 0 ? (
          <View style={styles.emptyState}>
            <View style={styles.emptyStateIconContainer}>
              <MaterialIcon name="file-document-outline" size={64} color="#C7C7CC" />
            </View>
            <Text style={styles.emptyStateText}>No transactions yet</Text>
            <Text style={styles.emptyStateSubtext}>
              Start tracking your income and expenses by adding your first transaction
            </Text>
            <TouchableOpacity
              style={styles.addFirstButton}
              onPress={() =>
                navigation.navigate('Accounting', { screen: 'AddTransaction' })
              }
              activeOpacity={0.8}>
              <MaterialIcon name="plus-circle" size={20} color="#FFF" />
              <Text style={styles.addFirstButtonText}>Add Transaction</Text>
            </TouchableOpacity>
          </View>
        ) : (
          !error &&
          recentTransactions.map((transaction, index) => (
            <TouchableOpacity
              key={transaction.id || `transaction-${index}`}
              style={styles.transactionCard}
              onPress={() =>
                navigation.navigate('Accounting', {
                  screen: 'TransactionDetail',
                  params: { transactionId: transaction.id },
                })
              }
              activeOpacity={0.7}>
              <View
                style={[
                  styles.transactionIcon,
                  transaction.type === 'income'
                    ? styles.incomeIcon
                    : styles.expenseIcon,
                ]}>
                <Icon
                  name={transaction.type === 'income' ? 'arrow-down' : 'arrow-up'}
                  size={20}
                  color="#FFF"
                />
              </View>
              <View style={styles.transactionDetails}>
                <Text style={styles.transactionCategory}>{transaction.category}</Text>
                <Text style={styles.transactionDescription} numberOfLines={1}>
                  {transaction.description || 'No description'}
                </Text>
                <Text style={styles.transactionDate}>
                  {formatDate(transaction.date)}
                </Text>
              </View>
              <Text
                style={[
                  styles.transactionAmount,
                  transaction.type === 'income'
                    ? styles.incomeAmount
                    : styles.expenseAmount,
                ]}>
                {transaction.type === 'income' ? '+' : '-'}
                {formatCurrency(transaction.amount)}
              </Text>
            </TouchableOpacity>
          ))
        )}
      </View>

      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsGrid}>
          {quickActions.map(action => {
            const iconPreset = getFeatureIcon(action.featureKey);
            return (
              <AnimatedIconButton
                key={action.key}
                icon={iconPreset.icon}
                label={action.label}
                iconColor={iconPreset.tint}
                backgroundColor={iconPreset.background}
                onPress={action.onPress}
                badgeText={action.badgeText}
                disabled={!!action.badgeText}
              />
            );
          })}
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  header: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: spacing.xl,
    paddingBottom: spacing.lg,
    paddingHorizontal: spacing.lg,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  appIcon: {
    width: 100, // Increased from 80 to 100
    height: 100, // Increased from 80 to 100
    marginBottom: spacing.md,
    borderRadius: 16, // Rounded corners for modern look
  },
  appTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: spacing.xs,
  },
  appSubtitle: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '700', // Bold
    marginBottom: spacing.xs,
  },
  appTagline: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '400', // Normal text
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  loadingText: {
    marginTop: spacing.md,
    fontSize: 16,
    color: '#666',
  },
  summaryContainer: {
    padding: spacing.lg,
    gap: spacing.md,
  },
  summaryCard: {
    backgroundColor: '#FFF',
    borderRadius: 16, // 16px rounded corners for modern look
    padding: spacing.xl, // Consistent spacing (24px)
    // Enhanced shadows: subtle on iOS, elevation on Android
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 }, // Increased for better depth
    shadowOpacity: 0.1, // Subtle shadow
    shadowRadius: 12, // Softer shadow
    elevation: 4, // Android elevation
  },
  summaryCardSkeleton: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: spacing.xl,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  summarySkeletonContent: {
    flex: 1,
    marginLeft: spacing.md,
  },
  marginBottom: {
    marginBottom: spacing.sm,
  },
  incomeCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  expenseCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#F44336',
  },
  balanceCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#2196F3',
  },
  summaryIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  summaryIconIncome: {
    backgroundColor: '#E8F5E9',
  },
  summaryIconExpense: {
    backgroundColor: '#FDECEA',
  },
  summaryIconBalance: {
    backgroundColor: '#E8F1FD',
  },
  summaryLabel: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500',
    marginBottom: 6,
  },
  summaryAmount: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  positiveBalance: {
    color: '#4CAF50',
  },
  negativeBalance: {
    color: '#F44336',
  },
  summaryPeriod: {
    fontSize: 12,
    color: '#8E8E93',
  },
  section: {
    padding: spacing.lg,
  },
  reportsCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  reportsIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  reportsContent: {
    flex: 1,
  },
  reportsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 6,
  },
  reportsSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  seeAllText: {
    color: '#007AFF',
    fontSize: 15,
    fontWeight: '500',
  },
  errorContainer: {
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: '#E65100',
  },
  retryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#FF9500',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  transactionCard: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    borderRadius: 12, // 12px rounded corners
    padding: spacing.lg, // Consistent spacing (16px)
    marginBottom: spacing.md, // Consistent spacing (12px)
    alignItems: 'center',
    // Enhanced shadows: subtle on iOS, elevation on Android
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8, // Softer shadow
    elevation: 3, // Android elevation
  },
  transactionIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
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
    fontSize: 16,
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
    padding: spacing.xxxl, // Consistent spacing (48px)
    backgroundColor: '#FFF',
    borderRadius: 16, // 16px rounded corners
    // Enhanced shadows: subtle on iOS, elevation on Android
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  emptyStateIconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#F5F5F7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  emptyStateText: {
    fontSize: 18,
    color: '#1D1D1F',
    marginTop: spacing.lg,
    fontWeight: '600',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: spacing.sm,
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: spacing.xl,
  },
  addFirstButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: spacing.xl, // Consistent spacing (24px)
    paddingVertical: spacing.md, // Consistent spacing (12px)
    borderRadius: 12, // 12px rounded corners
    marginTop: spacing.xl, // Consistent spacing (24px)
    gap: spacing.sm, // Consistent spacing (8px)
    // Enhanced shadows with color matching button
    shadowColor: '#007AFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  addFirstButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  quickActions: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginTop: spacing.lg,
    gap: spacing.md,
  },
});

export default DashboardScreen;

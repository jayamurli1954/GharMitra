import React, {useEffect, useState, useCallback} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {useRoute} from '@react-navigation/native';
import {
  financialYearService,
  OpeningBalanceListResponse,
} from '../../services/financialYearService';
import {spacing} from '../../constants/spacing';
import {formatCurrency} from '../../utils/formatters';

const OpeningBalancesScreen: React.FC = () => {
  const route = useRoute();
  const {yearId} = route.params as {yearId: string};

  const [data, setData] = useState<OpeningBalanceListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const result = await financialYearService.getOpeningBalances(yearId);
      setData(result);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to load opening balances');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [yearId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, [loadData]);

  if (loading && !data) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (!data) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>No data available</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Opening Balances</Text>
        <Text style={styles.subtitle}>{data.financial_year_name}</Text>
      </View>

      {/* Status Card */}
      <View
        style={[
          styles.statusCard,
          {
            backgroundColor:
              data.opening_balances_status === 'finalized'
                ? '#E8F5E9'
                : '#FFF3E0',
          },
        ]}>
        <View style={styles.statusHeader}>
          <Icon
            name={
              data.opening_balances_status === 'finalized'
                ? 'shield-checkmark'
                : 'time'
            }
            size={24}
            color={
              data.opening_balances_status === 'finalized' ? '#34C759' : '#FF9500'
            }
          />
          <Text
            style={[
              styles.statusText,
              {
                color:
                  data.opening_balances_status === 'finalized'
                    ? '#34C759'
                    : '#FF9500',
              },
            ]}>
            {data.opening_balances_status === 'finalized'
              ? 'Finalized'
              : 'Provisional'}
          </Text>
        </View>
        <Text style={styles.statusDescription}>
          {data.opening_balances_status === 'finalized'
            ? 'These opening balances are permanently locked after audit completion.'
            : 'These opening balances are provisional and may change if adjustments are made to the previous year.'}
        </Text>
      </View>

      {/* Summary Card */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>Summary</Text>
        <View style={styles.summaryGrid}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Total Accounts</Text>
            <Text style={styles.summaryValue}>{data.summary.total_accounts}</Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Total Debit</Text>
            <Text style={[styles.summaryValue, {color: '#34C759'}]}>
              {formatCurrency(data.summary.total_debit)}
            </Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Total Credit</Text>
            <Text style={[styles.summaryValue, {color: '#FF3B30'}]}>
              {formatCurrency(data.summary.total_credit)}
            </Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Difference</Text>
            <Text
              style={[
                styles.summaryValue,
                {
                  color: data.summary.is_balanced ? '#34C759' : '#FF9500',
                },
              ]}>
              {formatCurrency(data.summary.difference)}
            </Text>
          </View>
        </View>
        {data.summary.is_balanced ? (
          <View style={styles.balancedBadge}>
            <Icon name="checkmark-circle" size={16} color="#34C759" />
            <Text style={styles.balancedText}>Opening balances are balanced</Text>
          </View>
        ) : (
          <View style={styles.warningBadge}>
            <Icon name="alert-circle" size={16} color="#FF9500" />
            <Text style={styles.warningText}>
              Warning: Opening balances have a difference
            </Text>
          </View>
        )}
      </View>

      {/* Balances List */}
      <View style={styles.listSection}>
        <Text style={styles.sectionTitle}>Account-wise Balances</Text>

        {/* Debit Balances */}
        <View style={styles.balanceCategory}>
          <View style={styles.categoryHeader}>
            <Text style={styles.categoryTitle}>Debit Balances</Text>
            <Text style={styles.categoryTotal}>
              {formatCurrency(data.summary.total_debit)}
            </Text>
          </View>
          {data.balances
            .filter(b => b.balance_type === 'debit')
            .map(balance => (
              <View key={balance.id} style={styles.balanceRow}>
                <View style={styles.balanceInfo}>
                  <Text style={styles.accountName}>{balance.account_name}</Text>
                  {balance.manual_entry && (
                    <View style={styles.manualBadge}>
                      <Icon name="create-outline" size={12} color="#007AFF" />
                      <Text style={styles.manualText}>Manual</Text>
                    </View>
                  )}
                </View>
                <Text style={[styles.balanceAmount, {color: '#34C759'}]}>
                  {formatCurrency(balance.opening_balance)}
                </Text>
              </View>
            ))}
        </View>

        {/* Credit Balances */}
        <View style={styles.balanceCategory}>
          <View style={styles.categoryHeader}>
            <Text style={styles.categoryTitle}>Credit Balances</Text>
            <Text style={styles.categoryTotal}>
              {formatCurrency(data.summary.total_credit)}
            </Text>
          </View>
          {data.balances
            .filter(b => b.balance_type === 'credit')
            .map(balance => (
              <View key={balance.id} style={styles.balanceRow}>
                <View style={styles.balanceInfo}>
                  <Text style={styles.accountName}>{balance.account_name}</Text>
                  {balance.manual_entry && (
                    <View style={styles.manualBadge}>
                      <Icon name="create-outline" size={12} color="#007AFF" />
                      <Text style={styles.manualText}>Manual</Text>
                    </View>
                  )}
                </View>
                <Text style={[styles.balanceAmount, {color: '#FF3B30'}]}>
                  {formatCurrency(balance.opening_balance)}
                </Text>
              </View>
            ))}
        </View>
      </View>

      {/* Info */}
      <View style={styles.infoCard}>
        <Icon name="information-circle-outline" size={20} color="#007AFF" />
        <Text style={styles.infoText}>
          Opening balances are automatically calculated from the previous year's
          closing balances. Manual entries are marked separately.
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
  content: {
    padding: spacing.lg,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  errorText: {
    fontSize: 16,
    color: '#8E8E93',
  },
  header: {
    marginBottom: spacing.lg,
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
  },
  statusCard: {
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  statusText: {
    fontSize: 18,
    fontWeight: '700',
    marginLeft: spacing.xs,
  },
  statusDescription: {
    fontSize: 14,
    color: '#1D1D1F',
    lineHeight: 20,
  },
  summaryCard: {
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
  summaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: spacing.md,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  summaryItem: {
    flex: 1,
    minWidth: '45%',
  },
  summaryLabel: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: spacing.xs / 2,
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D1D1F',
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
  warningBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3E0',
    padding: spacing.sm,
    borderRadius: 8,
  },
  warningText: {
    fontSize: 14,
    color: '#FF9500',
    marginLeft: spacing.xs,
    fontWeight: '600',
  },
  listSection: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: spacing.md,
  },
  balanceCategory: {
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
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
    paddingBottom: spacing.sm,
    borderBottomWidth: 2,
    borderBottomColor: '#E5E5EA',
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  categoryTotal: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F7',
  },
  balanceInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  accountName: {
    fontSize: 15,
    color: '#1D1D1F',
    flex: 1,
  },
  manualBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F7FF',
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: spacing.xs,
  },
  manualText: {
    fontSize: 11,
    color: '#007AFF',
    marginLeft: spacing.xs / 2,
    fontWeight: '600',
  },
  balanceAmount: {
    fontSize: 16,
    fontWeight: '700',
    marginLeft: spacing.sm,
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: '#F0F7FF',
    borderRadius: 12,
    padding: spacing.md,
    borderColor: '#007AFF',
    borderWidth: 1,
  },
  infoText: {
    fontSize: 14,
    color: '#007AFF',
    marginLeft: spacing.sm,
    flex: 1,
    lineHeight: 20,
  },
});

export default OpeningBalancesScreen;



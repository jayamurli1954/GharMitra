import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { dashboardService, DashboardSummary } from '../../services/dashboardService';
import { StatCard } from '../../components/dashboard/StatCard';
import { PendingPaymentCard } from '../../components/dashboard/PendingPaymentCard';
import { ActivityItem } from '../../components/dashboard/ActivityItem';

const appIcon = require('../../assets/images/app-icon.png');

const EnhancedDashboardScreen = ({ navigation }: any) => {
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dashboardService.getDashboardSummary();
      setDashboardData(data);
    } catch (err: any) {
      console.error('Error loading dashboard:', err);
      setError(err?.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`;
  };

  if (loading && !dashboardData) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  if (error && !dashboardData) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="alert-circle-outline" size={64} color="#FF9500" />
        <Text style={styles.errorTitle}>Unable to Load Dashboard</Text>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadDashboardData}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const financialSummary = dashboardData?.financial_summary;
  const quickStats = dashboardData?.quick_stats || [];
  const pendingPayments = dashboardData?.pending_payments || [];
  const recentActivities = dashboardData?.recent_activities || [];

  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }>
      {/* Header with App Branding */}
      <View style={styles.header}>
        <Image source={appIcon} style={styles.appIcon} />
        <Text style={styles.appTitle}>GharMitra</Text>
        <Text style={styles.appSubtitle}>Society Management</Text>
      </View>

      {/* Quick Stats Cards */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Financial Overview</Text>
        {quickStats.map((stat, index) => (
          <StatCard
            key={index}
            label={stat.label}
            value={stat.value}
            change={stat.change}
            trend={stat.trend}
            icon={stat.icon}
            color={stat.color}
          />
        ))}
      </View>

      {/* Bank & Cash Balance */}
      {financialSummary && (
        <View style={styles.section}>
          <View style={styles.balanceContainer}>
            <View style={styles.balanceCard}>
              <Icon name="business" size={24} color="#2196F3" />
              <Text style={styles.balanceLabel}>Bank Balance</Text>
              <Text style={styles.balanceValue}>
                {formatCurrency(financialSummary.bank_balance || 0)}
              </Text>
            </View>
            <View style={styles.balanceCard}>
              <Icon name="cash" size={24} color="#4CAF50" />
              <Text style={styles.balanceLabel}>Cash in Hand</Text>
              <Text style={styles.balanceValue}>
                {formatCurrency(financialSummary.cash_balance || 0)}
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Pending Payments Widget */}
      {pendingPayments.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionHeaderLeft}>
              <Icon name="alert-circle" size={20} color="#FF9800" />
              <Text style={styles.sectionTitle}>Pending Payments</Text>
            </View>
            <TouchableOpacity
              onPress={() =>
                navigation.navigate('Reports', { screen: 'MemberDuesReport' })
              }>
              <Text style={styles.seeAllText}>See All</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.pendingPaymentsContainer}>
            {pendingPayments.slice(0, 5).map((payment, index) => (
              <PendingPaymentCard
                key={index}
                flatNumber={payment.flat_number}
                memberName={payment.member_name}
                amountDue={payment.amount_due}
                billMonth={payment.bill_month}
                daysOverdue={payment.days_overdue}
                onPress={() => {
                  // Navigate to bill details or member ledger
                  Alert.alert(
                    'Pending Payment',
                    `${payment.member_name} (${payment.flat_number})\nAmount: ₹${payment.amount_due}\nMonth: ${payment.bill_month}`,
                  );
                }}
              />
            ))}
          </View>
          {pendingPayments.length > 5 && (
            <TouchableOpacity
              style={styles.showMoreButton}
              onPress={() =>
                navigation.navigate('Reports', { screen: 'MemberDuesReport' })
              }>
              <Text style={styles.showMoreText}>
                Show {pendingPayments.length - 5} more
              </Text>
              <Icon name="chevron-forward" size={16} color="#007AFF" />
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Recent Activities Timeline */}
      {recentActivities.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionHeaderLeft}>
              <Icon name="time" size={20} color="#007AFF" />
              <Text style={styles.sectionTitle}>Recent Activities</Text>
            </View>
            <TouchableOpacity
              onPress={() => navigation.navigate('Accounting')}>
              <Text style={styles.seeAllText}>See All</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.activitiesContainer}>
            {recentActivities.slice(0, 8).map((activity, index) => (
              <ActivityItem
                key={activity.id}
                type={activity.type}
                title={activity.title}
                description={activity.description}
                amount={activity.amount}
                timestamp={activity.timestamp}
                icon={activity.icon}
                color={activity.color}
              />
            ))}
          </View>
          {recentActivities.length > 8 && (
            <TouchableOpacity
              style={styles.showMoreButton}
              onPress={() => navigation.navigate('Accounting')}>
              <Text style={styles.showMoreText}>
                View all transactions
              </Text>
              <Icon name="chevron-forward" size={16} color="#007AFF" />
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Quick Actions Grid */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActionsGrid}>
          <TouchableOpacity
            style={styles.quickActionCard}
            onPress={() =>
              navigation.navigate('Maintenance', { screen: 'GenerateBills' })
            }>
            <View style={[styles.quickActionIcon, { backgroundColor: '#E3F2FD' }]}>
              <Icon name="document-text" size={28} color="#2196F3" />
            </View>
            <Text style={styles.quickActionLabel}>Generate Bills</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickActionCard}
            onPress={() =>
              navigation.navigate('Accounting', { screen: 'AddTransaction' })
            }>
            <View style={[styles.quickActionIcon, { backgroundColor: '#E8F5E9' }]}>
              <Icon name="add-circle" size={28} color="#4CAF50" />
            </View>
            <Text style={styles.quickActionLabel}>Add Payment</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickActionCard}
            onPress={() =>
              navigation.navigate('Reports', { screen: 'ReportsDashboard' })
            }>
            <View style={[styles.quickActionIcon, { backgroundColor: '#F3E5F5' }]}>
              <Icon name="bar-chart" size={28} color="#9C27B0" />
            </View>
            <Text style={styles.quickActionLabel}>Reports</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickActionCard}
            onPress={() => navigation.navigate('Members')}>
            <View style={[styles.quickActionIcon, { backgroundColor: '#FFF3E0' }]}>
              <Icon name="people" size={28} color="#FF9800" />
            </View>
            <Text style={styles.quickActionLabel}>Members</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Financial Reports Banner */}
      <View style={styles.section}>
        <TouchableOpacity
          style={styles.reportsBanner}
          onPress={() =>
            navigation.navigate('Reports', { screen: 'ReportsDashboard' })
          }>
          <View style={styles.reportsIconContainer}>
            <Icon name="analytics" size={32} color="#007AFF" />
          </View>
          <View style={styles.reportsContent}>
            <Text style={styles.reportsTitle}>View Financial Reports</Text>
            <Text style={styles.reportsSubtitle}>
              Access comprehensive financial analysis and statements
            </Text>
          </View>
          <Icon name="chevron-forward" size={24} color="#8E8E93" />
        </TouchableOpacity>
      </View>

      <View style={styles.bottomSpacer} />
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
    marginTop: 16,
    fontSize: 16,
    color: '#8E8E93',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
    padding: 24,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1D1D1F',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 24,
  },
  retryButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    alignItems: 'center',
    paddingTop: 24,
    paddingBottom: 20,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  appIcon: {
    width: 80,
    height: 80,
    borderRadius: 16,
    marginBottom: 12,
  },
  appTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  appSubtitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1D1D1F',
    marginLeft: 8,
    marginBottom: 12,
  },
  seeAllText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  balanceContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  balanceCard: {
    flex: 1,
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 4,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  balanceLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 8,
    marginBottom: 4,
  },
  balanceValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1D1D1F',
  },
  pendingPaymentsContainer: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 12,
  },
  activitiesContainer: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  showMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    marginTop: 12,
  },
  showMoreText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
    marginRight: 4,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickActionCard: {
    width: '48%',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  quickActionIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  quickActionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1D1D1F',
    textAlign: 'center',
  },
  reportsBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
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
    fontSize: 16,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  reportsSubtitle: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  bottomSpacer: {
    height: 24,
  },
});

export default EnhancedDashboardScreen;



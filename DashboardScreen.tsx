/**
 * GharKhata - Dashboard Screen with Material Community Icons
 * This is a COMPLETE, WORKING version - just copy and replace your existing file
 * 
 * File location: src/screens/dashboard/DashboardScreen.tsx
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  StatusBar,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface QuickAction {
  id: string;
  title: string;
  icon: string;
  color: string;
  backgroundColor: string;
  route: string;
  badge?: string;
}

interface DashboardScreenProps {
  navigation: any;
}

const DashboardScreen: React.FC<DashboardScreenProps> = ({ navigation }) => {
  const [refreshing, setRefreshing] = useState(false);

  // Quick Actions Configuration
  const quickActions: QuickAction[] = [
    {
      id: 'generate-bills',
      title: 'Generate\nBills',
      icon: 'file-document-multiple',
      color: '#2196F3',
      backgroundColor: '#E3F2FD',
      route: 'GenerateBills',
    },
    {
      id: 'manage-flats',
      title: 'Manage\nFlats',
      icon: 'office-building',
      color: '#9C27B0',
      backgroundColor: '#F3E5F5',
      route: 'FlatsList',
    },
    {
      id: 'add-transaction',
      title: 'Add\nTransaction',
      icon: 'plus-circle',
      color: '#4CAF50',
      backgroundColor: '#E8F5E9',
      route: 'AddTransaction',
    },
    {
      id: 'reports',
      title: 'Reports',
      icon: 'chart-bar',
      color: '#FF9800',
      backgroundColor: '#FFF3E0',
      route: 'ReportsDashboard',
    },
    {
      id: 'resources',
      title: 'Resources',
      icon: 'folder-multiple',
      color: '#FFC107',
      backgroundColor: '#FFFDE7',
      route: 'ResourceCenter',
      badge: 'New',
    },
    {
      id: 'settings',
      title: 'Settings',
      icon: 'cog',
      color: '#607D8B',
      backgroundColor: '#ECEFF1',
      route: 'Settings',
    },
    {
      id: 'messages',
      title: 'Messages',
      icon: 'message-text',
      color: '#009688',
      backgroundColor: '#E0F2F1',
      route: 'Messages',
    },
    {
      id: 'payments',
      title: 'Payments',
      icon: 'cash-multiple',
      color: '#4CAF50',
      backgroundColor: '#E8F5E9',
      route: 'Payments',
      badge: 'New',
    },
    {
      id: 'complaints',
      title: 'Complaints',
      icon: 'alert-circle',
      color: '#F44336',
      backgroundColor: '#FFEBEE',
      route: 'Complaints',
      badge: 'New',
    },
  ];

  const onRefresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  };

  const handleActionPress = (route: string) => {
    try {
      navigation.navigate(route);
    } catch (error) {
      Alert.alert(
        'Navigation Error',
        `Screen "${route}" not found. Please configure navigation.`
      );
      console.error(`Navigation error to ${route}:`, error);
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar backgroundColor="#2196F3" barStyle="light-content" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <Text style={styles.headerSubtitle}>GharKhata Management</Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={['#2196F3']}
          />
        }
      >
        {/* Empty State Card */}
        <View style={styles.emptyState}>
          <View style={styles.emptyIconContainer}>
            <Icon name="cash-register" size={48} color="#2196F3" />
          </View>
          <Text style={styles.emptyStateTitle}>Welcome to GharKhata!</Text>
          <Text style={styles.emptyStateText}>
            Add your first transaction to get started with society management
          </Text>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => handleActionPress('AddTransaction')}
            activeOpacity={0.7}
          >
            <Icon name="plus" size={20} color="#FFFFFF" />
            <Text style={styles.primaryButtonText}>Add Transaction</Text>
          </TouchableOpacity>
        </View>

        {/* Quick Actions Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Quick Actions</Text>
            <Icon name="flash" size={20} color="#FF9800" />
          </View>
          
          <View style={styles.actionsGrid}>
            {quickActions.map((action) => (
              <TouchableOpacity
                key={action.id}
                style={styles.actionCard}
                onPress={() => handleActionPress(action.route)}
                activeOpacity={0.7}
              >
                {action.badge && (
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>{action.badge}</Text>
                  </View>
                )}
                
                <View
                  style={[
                    styles.iconContainer,
                    { backgroundColor: action.backgroundColor },
                  ]}
                >
                  <Icon name={action.icon} size={32} color={action.color} />
                </View>
                
                <Text style={styles.actionTitle}>{action.title}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Stats Preview */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Overview</Text>
          <View style={styles.statsContainer}>
            <View style={styles.statCard}>
              <Icon name="home-city" size={24} color="#2196F3" />
              <Text style={styles.statValue}>0</Text>
              <Text style={styles.statLabel}>Total Flats</Text>
            </View>
            
            <View style={styles.statCard}>
              <Icon name="receipt" size={24} color="#4CAF50" />
              <Text style={styles.statValue}>0</Text>
              <Text style={styles.statLabel}>Bills Generated</Text>
            </View>
            
            <View style={styles.statCard}>
              <Icon name="cash" size={24} color="#FF9800" />
              <Text style={styles.statValue}>₹0</Text>
              <Text style={styles.statLabel}>Total Collection</Text>
            </View>
          </View>
        </View>

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
  header: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 20,
    paddingTop: 40,
    paddingBottom: 20,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#E3F2FD',
    opacity: 0.9,
  },
  scrollView: {
    flex: 1,
  },
  emptyState: {
    backgroundColor: '#FFFFFF',
    margin: 16,
    padding: 24,
    borderRadius: 16,
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  emptyIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#212121',
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 14,
    color: '#757575',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  primaryButton: {
    flexDirection: 'row',
    backgroundColor: '#2196F3',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    elevation: 2,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212121',
    flex: 1,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '31%',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    position: 'relative',
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionTitle: {
    fontSize: 11,
    color: '#424242',
    textAlign: 'center',
    fontWeight: '500',
    lineHeight: 14,
  },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#FF9800',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    elevation: 2,
  },
  badgeText: {
    fontSize: 9,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 4,
    alignItems: 'center',
    elevation: 2,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#212121',
    marginTop: 8,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 11,
    color: '#757575',
    textAlign: 'center',
  },
  bottomSpacer: {
    height: 20,
  },
});

export default DashboardScreen;

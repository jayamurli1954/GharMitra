import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { authService, User } from '../../services/authService';
import { useNavigation, CommonActions } from '@react-navigation/native';

const ProfileScreen = () => {
  const [profile, setProfile] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const navigation = useNavigation();

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      // Try to get from backend first, fallback to stored user
      try {
        const user = await authService.getCurrentUser();
        setProfile(user);
      } catch (error) {
        // If backend fails, try stored user
        const storedUser = await authService.getStoredUser();
        if (storedUser) {
          setProfile(storedUser);
        } else {
          Alert.alert('Error', 'Failed to load profile. Please login again.');
        }
      }
    } catch (error) {
      console.error('Error loading profile:', error);
      Alert.alert('Error', 'Failed to load profile');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadProfile();
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: async () => {
          try {
            // Clear auth data first
            await authService.logout();

            // Navigate to Login immediately (before setting profile to null)
            // This prevents showing the error screen
            const rootNavigator = navigation.getParent()?.getParent();
            if (rootNavigator) {
              rootNavigator.dispatch(
                CommonActions.reset({
                  index: 0,
                  routes: [{ name: 'Login' as never }],
                })
              );
            } else {
              // Fallback: try direct navigation reset
              navigation.dispatch(
                CommonActions.reset({
                  index: 0,
                  routes: [{ name: 'Login' as never }],
                })
              );
            }
          } catch (error) {
            console.error('Error logging out:', error);
            Alert.alert('Error', 'Failed to logout. Please try again.');
          }
        },
      },
    ]);
  };

  if (loading && !profile) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading profile...</Text>
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="alert-circle-outline" size={48} color="#999" />
        <Text style={styles.errorText}>Failed to load profile</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadProfile}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const isAdmin = profile.role === 'admin' || profile.role === 'super_admin';

  const menuItems = [
    ...(isAdmin
      ? [
        {
          icon: 'shield-checkmark-outline',
          label: 'Admin Guidelines',
          onPress: () => navigation.navigate('AdminGuidelines' as never),
          color: '#FF3B30',
        },
        {
          icon: 'calendar',
          label: 'Financial Years',
          onPress: () => navigation.navigate('FinancialYear' as never),
          color: '#9C27B0',
        },
      ]
      : []),
    {
      icon: 'person-outline',
      label: 'Edit Profile',
      onPress: () => Alert.alert('Coming Soon', 'Profile editing coming soon!'),
      color: '#007AFF',
    },
    {
      icon: 'notifications-outline',
      label: 'Notifications',
      onPress: () =>
        Alert.alert('Coming Soon', 'Notification settings coming soon!'),
      color: '#FF9500',
    },
    {
      icon: 'lock-closed-outline',
      label: 'Change Password',
      onPress: () =>
        Alert.alert('Coming Soon', 'Password change coming soon!'),
      color: '#34C759',
    },
    {
      icon: 'help-circle-outline',
      label: 'Help & Support',
      onPress: () => Alert.alert('Coming Soon', 'Help section coming soon!'),
      color: '#5856D6',
    },
    {
      icon: 'information-circle-outline',
      label: 'About',
      onPress: () =>
        Alert.alert(
          'GharMitra',
          'Your Society, Digitally Simplified\n\nAccounting and Management\n\nVersion 1.0.0',
        ),
      color: '#8E8E93',
    },
  ];

  const legalMenuItems = [
    {
      icon: 'document-text-outline',
      label: 'Terms of Service',
      onPress: () => navigation.navigate('TermsOfService' as never),
      color: '#007AFF',
    },
    {
      icon: 'shield-checkmark-outline',
      label: 'Privacy Policy',
      onPress: () => navigation.navigate('PrivacyPolicy' as never),
      color: '#34C759',
    },
  ];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      {/* Header with gradient effect */}
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {profile.name
                .split(' ')
                .map(n => n[0])
                .join('')
                .toUpperCase()
                .substring(0, 2)}
            </Text>
          </View>
          <View style={styles.avatarBadge}>
            <Icon name="checkmark" size={16} color="#FFF" />
          </View>
        </View>
        <Text style={styles.name}>{profile.name}</Text>
        <Text style={styles.email}>{profile.email}</Text>
        <View style={styles.roleBadge}>
          <Icon
            name={profile.role === 'admin' ? 'shield-checkmark' : 'person'}
            size={14}
            color="#FFF"
          />
          <Text style={styles.roleText}>{profile.role.toUpperCase()}</Text>
        </View>
      </View>

      {/* Account Information Card */}
      <View style={styles.infoSection}>
        <Text style={styles.sectionTitle}>Account Information</Text>
        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <View style={[styles.iconContainer, { backgroundColor: '#E3F2FD' }]}>
              <Icon name="home" size={20} color="#007AFF" />
            </View>
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Apartment Number</Text>
              <Text style={styles.infoValue}>{profile.apartment_number}</Text>
            </View>
          </View>

          {profile.phone_number && (
            <View style={[styles.infoRow, styles.infoRowBorder]}>
              <View style={[styles.iconContainer, { backgroundColor: '#E8F5E9' }]}>
                <Icon name="call" size={20} color="#34C759" />
              </View>
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Phone Number</Text>
                <Text style={styles.infoValue}>{profile.phone_number}</Text>
              </View>
            </View>
          )}

          <View style={[styles.infoRow, styles.infoRowBorder]}>
            <View style={[styles.iconContainer, { backgroundColor: '#FFF3E0' }]}>
              <Icon name="mail" size={20} color="#FF9500" />
            </View>
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Email</Text>
              <Text style={styles.infoValue}>{profile.email}</Text>
            </View>
          </View>
        </View>
      </View>

      {/* Menu Items */}
      <View style={styles.menuSection}>
        {menuItems.map((item, index) => (
          <TouchableOpacity
            key={index}
            style={styles.menuItem}
            onPress={item.onPress}
            activeOpacity={0.7}>
            <View style={[styles.menuIconContainer, { backgroundColor: `${item.color}15` }]}>
              <Icon name={item.icon} size={24} color={item.color} />
            </View>
            <Text style={styles.menuLabel}>{item.label}</Text>
            <Icon name="chevron-forward" size={20} color="#C7C7CC" />
          </TouchableOpacity>
        ))}
      </View>

      {/* Legal Section */}
      <View style={styles.menuSection}>
        <Text style={styles.sectionTitle}>Legal</Text>
        {legalMenuItems.map((item, index) => (
          <TouchableOpacity
            key={index}
            style={styles.menuItem}
            onPress={item.onPress}
            activeOpacity={0.7}>
            <View style={[styles.menuIconContainer, { backgroundColor: `${item.color}15` }]}>
              <Icon name={item.icon} size={24} color={item.color} />
            </View>
            <Text style={styles.menuLabel}>{item.label}</Text>
            <Icon name="chevron-forward" size={20} color="#C7C7CC" />
          </TouchableOpacity>
        ))}
      </View>

      {/* Logout Button */}
      <TouchableOpacity
        style={styles.logoutButton}
        onPress={handleLogout}
        activeOpacity={0.7}>
        <View style={styles.logoutIconContainer}>
          <Icon name="log-out-outline" size={24} color="#FF3B30" />
        </View>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>GharMitra</Text>
        <Text style={styles.footerSubtitle}>Your Society, Digitally Simplified</Text>
        <Text style={styles.footerSubtext}>Accounting and Management</Text>
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
    padding: 20,
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingTop: 50,
    paddingBottom: 40,
    alignItems: 'center',
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  avatarContainer: {
    marginBottom: 15,
    position: 'relative',
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#FFF',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  avatarText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  avatarBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#FFF',
  },
  name: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#FFF',
    marginTop: 10,
  },
  email: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.9)',
    marginTop: 6,
  },
  roleBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    marginTop: 12,
    gap: 6,
  },
  roleText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  infoSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 16,
  },
  infoCard: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
  },
  infoRowBorder: {
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoContent: {
    flex: 1,
    marginLeft: 12,
  },
  infoLabel: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 4,
    fontWeight: '500',
  },
  infoValue: {
    fontSize: 16,
    color: '#1D1D1F',
    fontWeight: '600',
  },
  menuSection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  menuIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  menuLabel: {
    flex: 1,
    fontSize: 16,
    color: '#1D1D1F',
    fontWeight: '500',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFF',
    marginHorizontal: 20,
    padding: 16,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: '#FFE5E5',
    marginBottom: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  logoutIconContainer: {
    marginRight: 8,
  },
  logoutText: {
    fontSize: 17,
    color: '#FF3B30',
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
    paddingBottom: 40,
  },
  footerText: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500',
  },
  footerSubtitle: {
    fontSize: 13,
    color: '#007AFF',
    fontWeight: '700', // Bold
    marginTop: 4,
  },
  footerSubtext: {
    fontSize: 12,
    color: '#C7C7CC',
    marginTop: 4,
  },
});

export default ProfileScreen;

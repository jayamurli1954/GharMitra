import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {memberOnboardingService, Member} from '../../services/memberOnboardingService';

const MembersScreen = ({navigation}: any) => {
  const [members, setMembers] = useState<Member[]>([]);
  const [filteredMembers, setFilteredMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadMembers();
  }, []);

  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = members.filter(
        member =>
          member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          member.flat_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
          member.email.toLowerCase().includes(searchQuery.toLowerCase()),
      );
      setFilteredMembers(filtered);
    } else {
      setFilteredMembers(members);
    }
  }, [searchQuery, members]);

  const loadMembers = async () => {
    setLoading(true);
    setError(null);
    try {
      const membersList = await memberOnboardingService.listMembers();
      setMembers(membersList);
      setFilteredMembers(membersList);
    } catch (error: any) {
      console.error('Error loading members:', error);
      setError('Failed to load members');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string, memberType: string) => {
    if (status === 'active') {
      return memberType === 'owner' ? '#007AFF' : '#34C759';
    }
    return '#8E8E93';
  };

  const getStatusIcon = (memberType: string) => {
    return memberType === 'owner' ? 'home' : 'person';
  };

  const renderMember = ({item}: {item: Member}) => (
    <TouchableOpacity
      style={styles.memberCard}
      onPress={() =>
        navigation.navigate('PhysicalDocuments', {
          memberId: item.id?.toString() || '',
          memberName: item.name,
        })
      }
      activeOpacity={0.7}>
      <View style={styles.memberAvatar}>
        <Text style={styles.memberInitials}>
          {item.name
            .split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .substring(0, 2)}
        </Text>
      </View>
      <View style={styles.memberDetails}>
        <View style={styles.memberHeader}>
          <Text style={styles.memberName}>{item.name}</Text>
          <View
            style={[
              styles.roleBadge,
              {backgroundColor: getStatusColor(item.status, item.member_type) + '20'},
            ]}>
            <Icon
              name={getStatusIcon(item.member_type)}
              size={14}
              color={getStatusColor(item.status, item.member_type)}
            />
            <Text
              style={[styles.roleText, {color: getStatusColor(item.status, item.member_type)}]}>
              {item.member_type.toUpperCase()}
            </Text>
          </View>
        </View>
        <View style={styles.memberInfo}>
          <Icon name="home" size={14} color="#8E8E93" />
          <Text style={styles.memberInfoText}>Flat {item.flat_number}</Text>
        </View>
        <View style={styles.memberInfo}>
          <Icon name="mail" size={14} color="#8E8E93" />
          <Text style={styles.memberInfoText}>{item.email || 'N/A'}</Text>
        </View>
        {item.phone_number && item.phone_number !== 'Private' && (
          <View style={styles.memberInfo}>
            <Icon name="call" size={14} color="#8E8E93" />
            <Text style={styles.memberInfoText}>{item.phone_number}</Text>
          </View>
        )}
        <View style={styles.memberInfo}>
          <Icon name="people" size={14} color="#8E8E93" />
          <Text style={styles.memberInfoText}>{item.total_occupants} occupant{item.total_occupants !== 1 ? 's' : ''}</Text>
        </View>
        <View style={styles.memberAction}>
          <Icon name="document-text" size={16} color="#007AFF" />
          <Text style={styles.memberActionText}>View Documents</Text>
          <Icon name="chevron-forward" size={16} color="#8E8E93" />
        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading && members.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading members...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>

      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={styles.quickActionButton}
          onPress={() => navigation.navigate('AddMember')}
          activeOpacity={0.7}>
          <Icon name="person-add" size={24} color="#007AFF" />
          <Text style={styles.quickActionText}>Add Member</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.quickActionButton}
          onPress={() => navigation.navigate('BulkImport')}
          activeOpacity={0.7}>
          <Icon name="cloud-upload" size={24} color="#28a745" />
          <Text style={styles.quickActionText}>Bulk Import</Text>
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#8E8E93" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search members..."
          placeholderTextColor="#999"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')} activeOpacity={0.7}>
            <Icon name="close-circle" size={20} color="#8E8E93" />
          </TouchableOpacity>
        )}
      </View>

      {/* Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{members.length}</Text>
          <Text style={styles.statLabel}>Total Members</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statNumber, {color: '#007AFF'}]}>
            {members.filter(m => m.member_type === 'owner').length}
          </Text>
          <Text style={styles.statLabel}>Owners</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statNumber, {color: '#34C759'}]}>
            {members.filter(m => m.member_type === 'tenant').length}
          </Text>
          <Text style={styles.statLabel}>Tenants</Text>
        </View>
      </View>

      {/* Error Message */}
      {error && (
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={24} color="#FF3B30" />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={loadMembers}
            activeOpacity={0.7}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Members List */}
      <FlatList
        data={filteredMembers}
        renderItem={renderMember}
        keyExtractor={(item, index) => item.id?.toString() || `member-${index}`}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={loadMembers} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Icon name="people-outline" size={60} color="#C7C7CC" />
            <Text style={styles.emptyStateText}>
              {searchQuery ? 'No members found' : 'No members yet'}
            </Text>
            {!searchQuery && (
              <Text style={styles.emptyStateSubtext}>
                Members will appear here once they register
              </Text>
            )}
          </View>
        }
      />
    </View>
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
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    margin: 16,
    marginBottom: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    height: 48,
    fontSize: 16,
    color: '#1D1D1F',
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 12,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: '700',
    color: '#007AFF',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '500',
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
  memberCard: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  memberAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  memberInitials: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFF',
  },
  memberDetails: {
    flex: 1,
    marginLeft: 16,
  },
  memberHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  memberName: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1D1D1F',
    flex: 1,
  },
  roleBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  roleText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  memberInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 8,
  },
  memberInfoText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  memberAction: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    gap: 6,
  },
  memberActionText: {
    flex: 1,
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
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
  devBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E3F2FD',
    padding: 12,
    margin: 16,
    marginBottom: 12,
    borderRadius: 12,
    gap: 10,
  },
  devBannerText: {
    flex: 1,
    fontSize: 13,
    color: '#1976D2',
    lineHeight: 18,
  },
  quickActions: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 12,
    gap: 12,
  },
  quickActionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFF',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#FFE0B2',
    gap: 8,
    position: 'relative',
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FF9800',
  },
  comingSoonBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: '#FF9800',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  comingSoonText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});

export default MembersScreen;

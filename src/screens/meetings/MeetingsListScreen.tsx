import React, {useState, useEffect, useCallback} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import {meetingService, Meeting, MeetingType} from '../../services/meetingService';
import {authService} from '../../services/authService';

const MeetingsListScreen = ({navigation}: any) => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterType, setFilterType] = useState<MeetingType | 'all'>('all');
  const [userRole, setUserRole] = useState<string>('member');

  useEffect(() => {
    loadUserRole();
  }, []);

  const loadUserRole = async () => {
    try {
      const user = await authService.getStoredUser();
      if (user) {
        setUserRole(user.role);
      }
    } catch (error) {
      console.error('Error loading user role:', error);
    }
  };

  const loadMeetings = useCallback(async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filterType !== 'all') {
        params.meeting_type = filterType;
      }
      const meetingsList = await meetingService.getMeetings(params);
      // Sort by date descending (most recent first)
      meetingsList.sort((a, b) => {
        const dateA = new Date(a.meeting_date).getTime();
        const dateB = new Date(b.meeting_date).getTime();
        return dateB - dateA;
      });
      setMeetings(meetingsList);
    } catch (error: any) {
      console.error('Error loading meetings:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to load meetings. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filterType]);

  useFocusEffect(
    useCallback(() => {
      loadMeetings();
    }, [loadMeetings])
  );

  const handleRefresh = () => {
    setRefreshing(true);
    loadMeetings();
  };

  const handleMeetingPress = (meeting: Meeting) => {
    navigation.navigate('MeetingDetails', {meetingId: meeting.id});
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getMeetingTypeIcon = (type: string) => {
    switch (type) {
      case 'MC':
        return 'people';
      case 'AGM':
        return 'calendar';
      case 'EGM':
        return 'flash';
      case 'SGM':
        return 'star';
      case 'committee':
        return 'people-circle';
      case 'general_body':
        return 'people-outline';
      default:
        return 'calendar-outline';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled':
        return '#007AFF';
      case 'completed':
        return '#34C759';
      case 'cancelled':
        return '#FF3B30';
      default:
        return '#8E8E93';
    }
  };

  const filterTypes: Array<{value: MeetingType | 'all'; label: string}> = [
    {value: 'all', label: 'All'},
    {value: 'MC', label: 'MC'},
    {value: 'AGM', label: 'AGM'},
    {value: 'EGM', label: 'EGM'},
    {value: 'SGM', label: 'SGM'},
    {value: 'committee', label: 'Committee'},
    {value: 'general_body', label: 'General Body'},
  ];

  const renderMeetingItem = ({item}: {item: Meeting}) => (
    <TouchableOpacity
      style={styles.meetingCard}
      onPress={() => handleMeetingPress(item)}
      activeOpacity={0.7}>
      <View style={styles.meetingHeader}>
        <View style={styles.meetingTypeContainer}>
          <Icon
            name={getMeetingTypeIcon(item.meeting_type)}
            size={24}
            color="#007AFF"
            style={styles.meetingIcon}
          />
          <View style={styles.meetingTitleContainer}>
            <Text style={styles.meetingTitle}>{item.meeting_title}</Text>
            {item.meeting_number && (
              <Text style={styles.meetingNumber}>{item.meeting_number}</Text>
            )}
          </View>
        </View>
        <View
          style={[styles.statusBadge, {backgroundColor: getStatusColor(item.status)}]}>
          <Text style={styles.statusText}>{item.status.toUpperCase()}</Text>
        </View>
      </View>

      <View style={styles.meetingDetails}>
        <View style={styles.detailRow}>
          <Icon name="calendar-outline" size={16} color="#8E8E93" />
          <Text style={styles.detailText}>
            {formatDate(item.meeting_date)}
            {item.meeting_time && ` • ${item.meeting_time}`}
          </Text>
        </View>
        {item.venue && (
          <View style={styles.detailRow}>
            <Icon name="location-outline" size={16} color="#8E8E93" />
            <Text style={styles.detailText}>{item.venue}</Text>
          </View>
        )}
        {item.total_members_present > 0 && (
          <View style={styles.detailRow}>
            <Icon name="people-outline" size={16} color="#8E8E93" />
            <Text style={styles.detailText}>
              {item.total_members_present} members present
            </Text>
          </View>
        )}
      </View>

      {item.notice_sent && (
        <View style={styles.noticeBadge}>
          <Icon name="checkmark-circle" size={14} color="#34C759" />
          <Text style={styles.noticeText}>Notice sent</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  if (loading && meetings.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading meetings...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Filter Buttons */}
      <View style={styles.filterContainer}>
        <FlatList
          horizontal
          data={filterTypes}
          keyExtractor={item => item.value}
          showsHorizontalScrollIndicator={false}
          renderItem={({item}) => (
            <TouchableOpacity
              style={[
                styles.filterButton,
                filterType === item.value && styles.filterButtonActive,
              ]}
              onPress={() => setFilterType(item.value)}>
              <Text
                style={[
                  styles.filterButtonText,
                  filterType === item.value && styles.filterButtonTextActive,
                ]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Meetings List */}
      <FlatList
        data={meetings}
        keyExtractor={item => String(item.id)}
        renderItem={renderMeetingItem}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="calendar-outline" size={64} color="#C7C7CC" />
            <Text style={styles.emptyText}>No meetings found</Text>
            <Text style={styles.emptySubtext}>
              {filterType !== 'all'
                ? `No ${filterTypes.find(f => f.value === filterType)?.label} meetings`
                : 'Create a meeting to get started'}
            </Text>
          </View>
        }
      />

      {/* Add Button (Admin only) */}
      {(userRole === 'admin' || userRole === 'super_admin') && (
        <TouchableOpacity
          style={styles.fab}
          onPress={() => navigation.navigate('CreateMeeting')}
          activeOpacity={0.8}>
          <Icon name="add" size={28} color="#FFF" />
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
  },
  loadingText: {
    marginTop: 12,
    color: '#8E8E93',
    fontSize: 14,
  },
  filterContainer: {
    backgroundColor: '#FFF',
    paddingVertical: 12,
    paddingHorizontal: 4,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginHorizontal: 4,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
  },
  filterButtonText: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500',
  },
  filterButtonTextActive: {
    color: '#FFF',
  },
  listContent: {
    padding: 16,
  },
  meetingCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  meetingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  meetingTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  meetingIcon: {
    marginRight: 12,
  },
  meetingTitleContainer: {
    flex: 1,
  },
  meetingTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  meetingNumber: {
    fontSize: 12,
    color: '#8E8E93',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 10,
    color: '#FFF',
    fontWeight: '600',
  },
  meetingDetails: {
    marginTop: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  detailText: {
    fontSize: 14,
    color: '#8E8E93',
    marginLeft: 8,
  },
  noticeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  noticeText: {
    fontSize: 12,
    color: '#34C759',
    marginLeft: 6,
    fontWeight: '500',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 64,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#8E8E93',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#C7C7CC',
    marginTop: 8,
    textAlign: 'center',
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 8,
  },
});

export default MeetingsListScreen;






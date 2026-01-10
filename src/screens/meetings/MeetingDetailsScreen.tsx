import React, {useState, useEffect} from 'react';
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
import {
  meetingService,
  MeetingDetails,
  Meeting,
  AgendaItem,
  Attendance,
  Resolution,
} from '../../services/meetingService';
import {authService} from '../../services/authService';

const MeetingDetailsScreen = ({route, navigation}: any) => {
  const {meetingId} = route.params;
  const [meetingDetails, setMeetingDetails] = useState<MeetingDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [userRole, setUserRole] = useState<string>('member');

  useEffect(() => {
    loadUserRole();
    loadMeetingDetails();
  }, [meetingId]);

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

  const loadMeetingDetails = async () => {
    try {
      setLoading(true);
      const details = await meetingService.getMeetingDetails(meetingId);
      setMeetingDetails(details);
    } catch (error: any) {
      console.error('Error loading meeting details:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to load meeting details. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadMeetingDetails();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const isAdmin = userRole === 'admin' || userRole === 'super_admin';

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading meeting details...</Text>
      </View>
    );
  }

  if (!meetingDetails) {
    return (
      <View style={styles.centerContainer}>
        <Icon name="alert-circle-outline" size={64} color="#FF3B30" />
        <Text style={styles.errorText}>Meeting not found</Text>
        <TouchableOpacity
          style={styles.retryButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.retryButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const {meeting, agenda_items, attendance, resolutions} = meetingDetails;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }>
      {/* Meeting Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.title}>{meeting.meeting_title}</Text>
          {meeting.meeting_number && (
            <Text style={styles.meetingNumber}>{meeting.meeting_number}</Text>
          )}
          <View style={styles.statusContainer}>
            <View
              style={[
                styles.statusBadge,
                {
                  backgroundColor:
                    meeting.status === 'completed'
                      ? '#34C759'
                      : meeting.status === 'cancelled'
                      ? '#FF3B30'
                      : '#007AFF',
                },
              ]}>
              <Text style={styles.statusText}>{meeting.status.toUpperCase()}</Text>
            </View>
          </View>
        </View>
      </View>

      {/* Meeting Info */}
      <View style={styles.section}>
        <View style={styles.infoRow}>
          <Icon name="calendar-outline" size={20} color="#007AFF" />
          <Text style={styles.infoText}>
            {formatDate(meeting.meeting_date)}
            {meeting.meeting_time && ` • ${meeting.meeting_time}`}
          </Text>
        </View>
        {meeting.venue && (
          <View style={styles.infoRow}>
            <Icon name="location-outline" size={20} color="#007AFF" />
            <Text style={styles.infoText}>{meeting.venue}</Text>
          </View>
        )}
        <View style={styles.infoRow}>
          <Icon name="people-outline" size={20} color="#007AFF" />
          <Text style={styles.infoText}>
            {meeting.total_members_present || 0} members present
            {meeting.total_members_eligible &&
              ` of ${meeting.total_members_eligible} eligible`}
          </Text>
        </View>
        {meeting.quorum_required && (
          <View style={styles.infoRow}>
            <Icon
              name={meeting.quorum_met ? 'checkmark-circle' : 'close-circle'}
              size={20}
              color={meeting.quorum_met ? '#34C759' : '#FF3B30'}
            />
            <Text style={styles.infoText}>
              Quorum: {meeting.quorum_met ? 'Met' : 'Not Met'} ({meeting.quorum_required}{' '}
              required)
            </Text>
          </View>
        )}
      </View>

      {/* Admin Actions */}
      {isAdmin && (
        <View style={styles.actionsSection}>
          {meeting.status === 'scheduled' && (
            <>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() =>
                  navigation.navigate('MarkAttendance', {meetingId: meeting.id})
                }>
                <Icon name="people" size={20} color="#FFF" />
                <Text style={styles.actionButtonText}>Mark Attendance</Text>
              </TouchableOpacity>
            </>
          )}
          {meeting.status === 'completed' && !meeting.minutes_text && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() =>
                navigation.navigate('RecordMinutes', {meetingId: meeting.id})
              }>
              <Icon name="document-text" size={20} color="#FFF" />
              <Text style={styles.actionButtonText}>Record Minutes</Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Agenda Items */}
      {agenda_items.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Agenda Items</Text>
          {agenda_items.map((item: AgendaItem) => (
            <View key={item.id} style={styles.agendaItem}>
              <View style={styles.agendaItemHeader}>
                <Text style={styles.agendaItemNumber}>{item.item_number}.</Text>
                <Text style={styles.agendaItemTitle}>{item.item_title}</Text>
              </View>
              {item.item_description && (
                <Text style={styles.agendaItemDescription}>{item.item_description}</Text>
              )}
              {item.discussion_summary && (
                <View style={styles.discussionBox}>
                  <Text style={styles.discussionLabel}>Discussion:</Text>
                  <Text style={styles.discussionText}>{item.discussion_summary}</Text>
                </View>
              )}
              <View style={styles.agendaStatus}>
                <Text
                  style={[
                    styles.agendaStatusText,
                    {
                      color:
                        item.status === 'resolved'
                          ? '#34C759'
                          : item.status === 'deferred'
                          ? '#FF9500'
                          : '#8E8E93',
                    },
                  ]}>
                  {item.status.toUpperCase()}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Attendance */}
      {attendance.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Attendance ({attendance.length} members)
          </Text>
          {attendance.map((att: Attendance) => (
            <View key={att.id} style={styles.attendanceItem}>
              <View style={styles.attendanceHeader}>
                <Text style={styles.attendanceName}>{att.member_name}</Text>
                <View
                  style={[
                    styles.attendanceStatusBadge,
                    {
                      backgroundColor:
                        att.status === 'present'
                          ? '#34C759'
                          : att.status === 'proxy'
                          ? '#007AFF'
                          : '#FF3B30',
                    },
                  ]}>
                  <Text style={styles.attendanceStatusText}>
                    {att.status.toUpperCase()}
                  </Text>
                </View>
              </View>
              {att.member_flat && (
                <Text style={styles.attendanceFlat}>Flat: {att.member_flat}</Text>
              )}
              {att.proxy_holder_name && (
                <Text style={styles.proxyText}>
                  Proxy: {att.proxy_holder_name}
                </Text>
              )}
              {att.arrival_time && (
                <Text style={styles.timeText}>Arrived: {att.arrival_time}</Text>
              )}
            </View>
          ))}
        </View>
      )}

      {/* Minutes */}
      {meeting.minutes_text && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Meeting Minutes</Text>
          <View style={styles.minutesBox}>
            <Text style={styles.minutesText}>{meeting.minutes_text}</Text>
          </View>
          {meeting.recorded_by && (
            <Text style={styles.recordedBy}>
              Recorded by: {meeting.recorded_by}
              {meeting.recorded_at &&
                ` on ${formatDate(meeting.recorded_at)}`}
            </Text>
          )}
          {meeting.minutes_approved && (
            <View style={styles.approvedBadge}>
              <Icon name="checkmark-circle" size={16} color="#34C759" />
              <Text style={styles.approvedText}>Minutes Approved</Text>
            </View>
          )}
        </View>
      )}

      {/* Resolutions */}
      {resolutions.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Resolutions ({resolutions.length})</Text>
          {resolutions.map((res: Resolution) => (
            <View key={res.id} style={styles.resolutionItem}>
              <View style={styles.resolutionHeader}>
                <Text style={styles.resolutionNumber}>{res.resolution_number}</Text>
                <View
                  style={[
                    styles.resolutionResultBadge,
                    {
                      backgroundColor:
                        res.result === 'passed'
                          ? '#34C759'
                          : res.result === 'rejected'
                          ? '#FF3B30'
                          : '#8E8E93',
                    },
                  ]}>
                  <Text style={styles.resolutionResultText}>
                    {res.result.toUpperCase()}
                  </Text>
                </View>
              </View>
              <Text style={styles.resolutionTitle}>{res.resolution_title}</Text>
              <Text style={styles.resolutionText}>{res.resolution_text}</Text>
              <View style={styles.resolutionVotes}>
                <Text style={styles.voteText}>
                  For: {res.votes_for} | Against: {res.votes_against} | Abstain:{' '}
                  {res.votes_abstain}
                </Text>
              </View>
              <Text style={styles.resolutionProposed}>
                Proposed by: {res.proposed_by_name} | Seconded by: {res.seconded_by_name}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Empty States */}
      {agenda_items.length === 0 && attendance.length === 0 && !meeting.minutes_text && (
        <View style={styles.emptySection}>
          <Icon name="document-outline" size={48} color="#C7C7CC" />
          <Text style={styles.emptyText}>No additional details available</Text>
        </View>
      )}
    </ScrollView>
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
  errorText: {
    fontSize: 18,
    color: '#FF3B30',
    marginTop: 16,
  },
  retryButton: {
    marginTop: 16,
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
    backgroundColor: '#FFF',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerContent: {
    alignItems: 'center',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#000',
    textAlign: 'center',
    marginBottom: 8,
  },
  meetingNumber: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 12,
  },
  statusContainer: {
    marginTop: 8,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  statusText: {
    fontSize: 12,
    color: '#FFF',
    fontWeight: '600',
  },
  section: {
    backgroundColor: '#FFF',
    marginTop: 12,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 16,
    color: '#000',
    marginLeft: 12,
  },
  actionsSection: {
    backgroundColor: '#FFF',
    marginTop: 12,
    padding: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginBottom: 12,
  },
  actionButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  agendaItem: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  agendaItemHeader: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  agendaItemNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginRight: 8,
  },
  agendaItemTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    flex: 1,
  },
  agendaItemDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 4,
    marginBottom: 8,
  },
  discussionBox: {
    backgroundColor: '#F5F5F5',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  discussionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E93',
    marginBottom: 4,
  },
  discussionText: {
    fontSize: 14,
    color: '#000',
  },
  agendaStatus: {
    marginTop: 8,
  },
  agendaStatusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  attendanceItem: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  attendanceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  attendanceName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    flex: 1,
  },
  attendanceStatusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  attendanceStatusText: {
    fontSize: 10,
    color: '#FFF',
    fontWeight: '600',
  },
  attendanceFlat: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 4,
  },
  proxyText: {
    fontSize: 14,
    color: '#007AFF',
    marginTop: 4,
  },
  timeText: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
  },
  minutesBox: {
    backgroundColor: '#F5F5F5',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
  },
  minutesText: {
    fontSize: 14,
    color: '#000',
    lineHeight: 22,
  },
  recordedBy: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 8,
  },
  approvedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
  },
  approvedText: {
    fontSize: 14,
    color: '#34C759',
    marginLeft: 6,
    fontWeight: '600',
  },
  resolutionItem: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  resolutionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  resolutionNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  resolutionResultBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  resolutionResultText: {
    fontSize: 10,
    color: '#FFF',
    fontWeight: '600',
  },
  resolutionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  resolutionText: {
    fontSize: 14,
    color: '#000',
    lineHeight: 20,
    marginBottom: 8,
  },
  resolutionVotes: {
    marginTop: 8,
  },
  voteText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  resolutionProposed: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 8,
  },
  emptySection: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 16,
  },
});

export default MeetingDetailsScreen;






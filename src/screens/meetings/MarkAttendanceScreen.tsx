import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  TextInput,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {
  meetingService,
  AttendanceRecord,
  MarkAttendanceRequest,
  Meeting,
  Member,
} from '../../services/meetingService';
import {usersService} from '../../services/usersService';

const MarkAttendanceScreen = ({route, navigation}: any) => {
  const {meetingId} = route.params;
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [attendance, setAttendance] = useState<Map<number, AttendanceRecord>>(new Map());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [meetingData, membersList] = await Promise.all([
        meetingService.getMeeting(meetingId),
        loadMembers(),
      ]);
      setMeeting(meetingData);
      setMembers(membersList);

      // Initialize attendance map with all members as absent
      const initialAttendance = new Map<number, AttendanceRecord>();
      membersList.forEach(member => {
        initialAttendance.set(parseInt(member.id), {
          member_id: parseInt(member.id),
          status: 'absent',
        });
      });
      setAttendance(initialAttendance);
    } catch (error: any) {
      console.error('Error loading data:', error);
      Alert.alert('Error', 'Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadMembers = async (): Promise<Member[]> => {
    try {
      // Try to get members from users service
      const users = await usersService.getUsers();
      return users.map(user => ({
        id: user.id,
        name: user.name,
        flat_number: user.apartment_number,
        email: user.email,
        phone_number: user.phone_number,
      }));
    } catch (error) {
      console.error('Error loading members:', error);
      return [];
    }
  };

  const handleStatusChange = (memberId: number, status: 'present' | 'proxy' | 'absent') => {
    const current = attendance.get(memberId);
    const updated = new Map(attendance);
    updated.set(memberId, {
      ...current!,
      member_id: memberId,
      status,
      proxy_holder_id: status === 'proxy' ? current?.proxy_holder_id : undefined,
    });
    setAttendance(updated);
  };

  const handleProxyChange = (memberId: number, proxyHolderId: number | undefined) => {
    const current = attendance.get(memberId);
    const updated = new Map(attendance);
    updated.set(memberId, {
      ...current!,
      member_id: memberId,
      status: 'proxy',
      proxy_holder_id: proxyHolderId,
    });
    setAttendance(updated);
  };

  const handleTimeChange = (
    memberId: number,
    field: 'arrival_time' | 'departure_time',
    value: string,
  ) => {
    const current = attendance.get(memberId);
    const updated = new Map(attendance);
    updated.set(memberId, {
      ...current!,
      member_id: memberId,
      [field]: value,
    });
    setAttendance(updated);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const attendanceList: AttendanceRecord[] = Array.from(attendance.values());
      const request: MarkAttendanceRequest = {
        attendees: attendanceList,
      };

      await meetingService.markAttendance(meetingId, request);
      Alert.alert('Success', 'Attendance marked successfully', [
        {
          text: 'OK',
          onPress: () => navigation.goBack(),
        },
      ]);
    } catch (error: any) {
      console.error('Error marking attendance:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to mark attendance. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'present':
        return '#34C759';
      case 'proxy':
        return '#007AFF';
      case 'absent':
        return '#FF3B30';
      default:
        return '#8E8E93';
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading members...</Text>
      </View>
    );
  }

  const presentCount = Array.from(attendance.values()).filter(
    a => a.status === 'present' || a.status === 'proxy',
  ).length;
  const absentCount = Array.from(attendance.values()).filter(a => a.status === 'absent').length;

  return (
    <View style={styles.container}>
      {/* Summary */}
      <View style={styles.summaryContainer}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>Present</Text>
          <Text style={[styles.summaryValue, {color: '#34C759'}]}>{presentCount}</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>Absent</Text>
          <Text style={[styles.summaryValue, {color: '#FF3B30'}]}>{absentCount}</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>Total</Text>
          <Text style={styles.summaryValue}>{members.length}</Text>
        </View>
      </View>

      <ScrollView style={styles.scrollView}>
        {members.map(member => {
          const memberId = parseInt(member.id);
          const memberAttendance = attendance.get(memberId) || {
            member_id: memberId,
            status: 'absent' as const,
          };

          return (
            <View key={member.id} style={styles.memberCard}>
              <View style={styles.memberHeader}>
                <View style={styles.memberInfo}>
                  <Text style={styles.memberName}>{member.name}</Text>
                  {member.flat_number && (
                    <Text style={styles.memberFlat}>Flat: {member.flat_number}</Text>
                  )}
                </View>
                <View
                  style={[
                    styles.statusIndicator,
                    {backgroundColor: getStatusColor(memberAttendance.status)},
                  ]}
                />
              </View>

              {/* Status Buttons */}
              <View style={styles.statusButtons}>
                <TouchableOpacity
                  style={[
                    styles.statusButton,
                    memberAttendance.status === 'present' && styles.statusButtonActive,
                    {borderColor: '#34C759'},
                  ]}
                  onPress={() => handleStatusChange(memberId, 'present')}>
                  <Text
                    style={[
                      styles.statusButtonText,
                      memberAttendance.status === 'present' && styles.statusButtonTextActive,
                      {color: memberAttendance.status === 'present' ? '#FFF' : '#34C759'},
                    ]}>
                    Present
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.statusButton,
                    memberAttendance.status === 'proxy' && styles.statusButtonActive,
                    {borderColor: '#007AFF'},
                  ]}
                  onPress={() => handleStatusChange(memberId, 'proxy')}>
                  <Text
                    style={[
                      styles.statusButtonText,
                      memberAttendance.status === 'proxy' && styles.statusButtonTextActive,
                      {color: memberAttendance.status === 'proxy' ? '#FFF' : '#007AFF'},
                    ]}>
                    Proxy
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.statusButton,
                    memberAttendance.status === 'absent' && styles.statusButtonActive,
                    {borderColor: '#FF3B30'},
                  ]}
                  onPress={() => handleStatusChange(memberId, 'absent')}>
                  <Text
                    style={[
                      styles.statusButtonText,
                      memberAttendance.status === 'absent' && styles.statusButtonTextActive,
                      {color: memberAttendance.status === 'absent' ? '#FFF' : '#FF3B30'},
                    ]}>
                    Absent
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Proxy Holder Selection */}
              {memberAttendance.status === 'proxy' && (
                <View style={styles.proxySection}>
                  <Text style={styles.proxyLabel}>Proxy Holder:</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    {members
                      .filter(m => parseInt(m.id) !== memberId)
                      .map(proxyMember => (
                        <TouchableOpacity
                          key={proxyMember.id}
                          style={[
                            styles.proxyButton,
                            memberAttendance.proxy_holder_id === parseInt(proxyMember.id) &&
                              styles.proxyButtonActive,
                          ]}
                          onPress={() =>
                            handleProxyChange(
                              memberId,
                              memberAttendance.proxy_holder_id === parseInt(proxyMember.id)
                                ? undefined
                                : parseInt(proxyMember.id),
                            )
                          }>
                          <Text
                            style={[
                              styles.proxyButtonText,
                              memberAttendance.proxy_holder_id === parseInt(proxyMember.id) &&
                                styles.proxyButtonTextActive,
                            ]}>
                            {proxyMember.name}
                          </Text>
                        </TouchableOpacity>
                      ))}
                  </ScrollView>
                </View>
              )}

              {/* Time Tracking */}
              {(memberAttendance.status === 'present' || memberAttendance.status === 'proxy') && (
                <View style={styles.timeSection}>
                  <View style={styles.timeInputContainer}>
                    <Text style={styles.timeLabel}>Arrival Time:</Text>
                    <TextInput
                      style={styles.timeInput}
                      value={memberAttendance.arrival_time || ''}
                      onChangeText={text => handleTimeChange(memberId, 'arrival_time', text)}
                      placeholder="e.g., 10:15 AM"
                      placeholderTextColor="#8E8E93"
                    />
                  </View>
                  <View style={styles.timeInputContainer}>
                    <Text style={styles.timeLabel}>Departure Time:</Text>
                    <TextInput
                      style={styles.timeInput}
                      value={memberAttendance.departure_time || ''}
                      onChangeText={text => handleTimeChange(memberId, 'departure_time', text)}
                      placeholder="e.g., 12:30 PM"
                      placeholderTextColor="#8E8E93"
                    />
                  </View>
                </View>
              )}
            </View>
          );
        })}
      </ScrollView>

      {/* Save Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={saving}>
          {saving ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Icon name="checkmark-circle" size={20} color="#FFF" />
              <Text style={styles.saveButtonText}>Save Attendance</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
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
  },
  loadingText: {
    marginTop: 12,
    color: '#8E8E93',
    fontSize: 14,
  },
  summaryContainer: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000',
  },
  scrollView: {
    flex: 1,
  },
  memberCard: {
    backgroundColor: '#FFF',
    margin: 12,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  memberHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  memberInfo: {
    flex: 1,
  },
  memberName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  memberFlat: {
    fontSize: 14,
    color: '#8E8E93',
  },
  statusIndicator: {
    width: 16,
    height: 16,
    borderRadius: 8,
  },
  statusButtons: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  statusButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  statusButtonActive: {
    backgroundColor: '#007AFF',
  },
  statusButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  statusButtonTextActive: {
    color: '#FFF',
  },
  proxySection: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  proxyLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  proxyButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    marginRight: 8,
    backgroundColor: '#F5F5F5',
  },
  proxyButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  proxyButtonText: {
    fontSize: 14,
    color: '#000',
  },
  proxyButtonTextActive: {
    color: '#FFF',
  },
  timeSection: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  timeInputContainer: {
    marginBottom: 12,
  },
  timeLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    marginBottom: 6,
  },
  timeInput: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#000',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  footer: {
    backgroundColor: '#FFF',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 8,
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 8,
  },
});

export default MarkAttendanceScreen;






import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {
  meetingService,
  RecordMinutesRequest,
  MeetingDetails,
  AgendaItem,
} from '../../services/meetingService';

const RecordMinutesScreen = ({route, navigation}: any) => {
  const {meetingId} = route.params;
  const [meetingDetails, setMeetingDetails] = useState<MeetingDetails | null>(null);
  const [minutesText, setMinutesText] = useState('');
  const [agendaUpdates, setAgendaUpdates] = useState<Map<number, {discussion_summary?: string; status?: string}>>(
    new Map(),
  );
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadMeetingDetails();
  }, []);

  const loadMeetingDetails = async () => {
    try {
      setLoading(true);
      const details = await meetingService.getMeetingDetails(meetingId);
      setMeetingDetails(details);
      setMinutesText(details.meeting.minutes_text || '');

      // Initialize agenda updates
      const updates = new Map<number, {discussion_summary?: string; status?: string}>();
      details.agenda_items.forEach(item => {
        updates.set(item.id, {
          discussion_summary: item.discussion_summary || '',
          status: item.status,
        });
      });
      setAgendaUpdates(updates);
    } catch (error: any) {
      console.error('Error loading meeting details:', error);
      Alert.alert('Error', 'Failed to load meeting details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAgendaUpdate = (
    agendaItemId: number,
    field: 'discussion_summary' | 'status',
    value: string,
  ) => {
    const updated = new Map(agendaUpdates);
    const current = updated.get(agendaItemId) || {};
    updated.set(agendaItemId, {
      ...current,
      [field]: value,
    });
    setAgendaUpdates(updated);
  };

  const handleSave = async () => {
    if (!minutesText.trim()) {
      Alert.alert('Error', 'Please enter meeting minutes');
      return;
    }

    try {
      setSaving(true);
      const updates = Array.from(agendaUpdates.entries())
        .map(([agenda_item_id, update]) => ({
          agenda_item_id,
          ...update,
        }))
        .filter(update => update.discussion_summary || update.status);

      const request: RecordMinutesRequest = {
        minutes_text: minutesText.trim(),
        agenda_updates: updates.length > 0 ? updates : undefined,
      };

      await meetingService.recordMinutes(meetingId, request);
      Alert.alert('Success', 'Minutes recorded successfully', [
        {
          text: 'OK',
          onPress: () => navigation.goBack(),
        },
      ]);
    } catch (error: any) {
      console.error('Error recording minutes:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to record minutes. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved':
        return '#34C759';
      case 'discussed':
        return '#007AFF';
      case 'deferred':
        return '#FF9500';
      case 'withdrawn':
        return '#FF3B30';
      default:
        return '#8E8E93';
    }
  };

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
      </View>
    );
  }

  const statusOptions = [
    {value: 'pending', label: 'Pending'},
    {value: 'discussed', label: 'Discussed'},
    {value: 'resolved', label: 'Resolved'},
    {value: 'deferred', label: 'Deferred'},
    {value: 'withdrawn', label: 'Withdrawn'},
  ];

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Meeting Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{meetingDetails.meeting.meeting_title}</Text>
          <Text style={styles.sectionSubtitle}>
            {new Date(meetingDetails.meeting.meeting_date).toLocaleDateString()}
          </Text>
        </View>

        {/* Agenda Items */}
        {meetingDetails.agenda_items.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Agenda Items Discussion</Text>
            {meetingDetails.agenda_items.map((item: AgendaItem) => {
              const update = agendaUpdates.get(item.id) || {};
              return (
                <View key={item.id} style={styles.agendaItemCard}>
                  <View style={styles.agendaItemHeader}>
                    <Text style={styles.agendaItemNumber}>{item.item_number}.</Text>
                    <Text style={styles.agendaItemTitle}>{item.item_title}</Text>
                  </View>
                  {item.item_description && (
                    <Text style={styles.agendaItemDescription}>{item.item_description}</Text>
                  )}

                  <View style={styles.agendaUpdateSection}>
                    <Text style={styles.updateLabel}>Discussion Summary:</Text>
                    <TextInput
                      style={styles.updateInput}
                      value={update.discussion_summary || ''}
                      onChangeText={text =>
                        handleAgendaUpdate(item.id, 'discussion_summary', text)
                      }
                      placeholder="Enter discussion summary for this agenda item..."
                      placeholderTextColor="#8E8E93"
                      multiline
                      numberOfLines={4}
                    />
                  </View>

                  <View style={styles.agendaUpdateSection}>
                    <Text style={styles.updateLabel}>Status:</Text>
                    <View style={styles.statusButtons}>
                      {statusOptions.map(option => (
                        <TouchableOpacity
                          key={option.value}
                          style={[
                            styles.statusButton,
                            update.status === option.value && styles.statusButtonActive,
                            {
                              borderColor: getStatusColor(option.value),
                              backgroundColor:
                                update.status === option.value
                                  ? getStatusColor(option.value)
                                  : '#FFF',
                            },
                          ]}
                          onPress={() => handleAgendaUpdate(item.id, 'status', option.value)}>
                          <Text
                            style={[
                              styles.statusButtonText,
                              {
                                color:
                                  update.status === option.value
                                    ? '#FFF'
                                    : getStatusColor(option.value),
                              },
                            ]}>
                            {option.label}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* Minutes Text */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Meeting Minutes *</Text>
          <TextInput
            style={styles.minutesInput}
            value={minutesText}
            onChangeText={setMinutesText}
            placeholder="Enter the full meeting minutes here..."
            placeholderTextColor="#8E8E93"
            multiline
            numberOfLines={20}
            textAlignVertical="top"
          />
        </View>
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
              <Text style={styles.saveButtonText}>Save Minutes</Text>
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
  errorText: {
    fontSize: 18,
    color: '#FF3B30',
    marginTop: 16,
  },
  scrollView: {
    flex: 1,
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
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 16,
  },
  agendaItemCard: {
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
    marginBottom: 12,
  },
  agendaUpdateSection: {
    marginTop: 12,
  },
  updateLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  updateInput: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#000',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    minHeight: 100,
    textAlignVertical: 'top',
  },
  statusButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  statusButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
  },
  statusButtonActive: {
    // backgroundColor set dynamically
  },
  statusButtonText: {
    fontSize: 12,
    fontWeight: '600',
  },
  minutesInput: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#000',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    minHeight: 300,
    textAlignVertical: 'top',
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

export default RecordMinutesScreen;






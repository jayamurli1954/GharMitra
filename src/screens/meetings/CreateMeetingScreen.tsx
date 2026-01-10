import React, {useState} from 'react';
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
  MeetingCreate,
  AgendaItemCreate,
  MeetingType,
} from '../../services/meetingService';

const CreateMeetingScreen = ({navigation}: any) => {
  const [meetingType, setMeetingType] = useState<MeetingType>('MC');
  const [meetingDate, setMeetingDate] = useState('');
  const [meetingTime, setMeetingTime] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('');
  const [venue, setVenue] = useState('');
  const [noticeSentTo, setNoticeSentTo] = useState<'all_members' | 'mc_only'>('all_members');
  const [agendaItems, setAgendaItems] = useState<AgendaItemCreate[]>([]);
  const [newAgendaItem, setNewAgendaItem] = useState({item_number: 1, item_title: '', item_description: ''});
  const [saving, setSaving] = useState(false);

  const meetingTypes: Array<{value: MeetingType; label: string}> = [
    {value: 'MC', label: 'Management Committee (MC)'},
    {value: 'AGM', label: 'Annual General Meeting (AGM)'},
    {value: 'EGM', label: 'Extraordinary General Meeting (EGM)'},
    {value: 'SGM', label: 'Special General Meeting (SGM)'},
    {value: 'committee', label: 'Committee Meeting'},
    {value: 'general_body', label: 'General Body Meeting'},
  ];

  const handleAddAgendaItem = () => {
    if (!newAgendaItem.item_title.trim()) {
      Alert.alert('Error', 'Please enter agenda item title');
      return;
    }

    const itemNumber = agendaItems.length + 1;
    setAgendaItems([
      ...agendaItems,
      {
        item_number: itemNumber,
        item_title: newAgendaItem.item_title.trim(),
        item_description: newAgendaItem.item_description.trim() || undefined,
      },
    ]);
    setNewAgendaItem({
      item_number: itemNumber + 1,
      item_title: '',
      item_description: '',
    });
  };

  const handleRemoveAgendaItem = (index: number) => {
    const updated = agendaItems.filter((_, i) => i !== index);
    // Renumber items
    const renumbered = updated.map((item, i) => ({
      ...item,
      item_number: i + 1,
    }));
    setAgendaItems(renumbered);
    setNewAgendaItem({
      item_number: renumbered.length + 1,
      item_title: '',
      item_description: '',
    });
  };

  const handleSave = async () => {
    if (!meetingTitle.trim()) {
      Alert.alert('Error', 'Please enter meeting title');
      return;
    }

    if (!meetingDate.trim()) {
      Alert.alert('Error', 'Please enter meeting date');
      return;
    }

    // Validate date format
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(meetingDate)) {
      Alert.alert('Error', 'Please enter date in YYYY-MM-DD format');
      return;
    }

    try {
      setSaving(true);
      const meetingData: MeetingCreate = {
        meeting_type: meetingType,
        meeting_date: meetingDate,
        meeting_title: meetingTitle.trim(),
        meeting_time: meetingTime.trim() || undefined,
        venue: venue.trim() || undefined,
        notice_sent_to: noticeSentTo,
        agenda_items: agendaItems.length > 0 ? agendaItems : undefined,
      };

      await meetingService.createMeeting(meetingData);
      Alert.alert('Success', 'Meeting created successfully', [
        {
          text: 'OK',
          onPress: () => navigation.goBack(),
        },
      ]);
    } catch (error: any) {
      console.error('Error creating meeting:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to create meeting. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // Get today's date in YYYY-MM-DD format
  const getTodayDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.form}>
        {/* Meeting Type */}
        <View style={styles.section}>
          <Text style={styles.label}>Meeting Type *</Text>
          <View style={styles.typeContainer}>
            {meetingTypes.map(type => (
              <TouchableOpacity
                key={type.value}
                style={[
                  styles.typeButton,
                  meetingType === type.value && styles.typeButtonActive,
                ]}
                onPress={() => setMeetingType(type.value)}>
                <Text
                  style={[
                    styles.typeButtonText,
                    meetingType === type.value && styles.typeButtonTextActive,
                  ]}>
                  {type.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Meeting Title */}
        <View style={styles.section}>
          <Text style={styles.label}>Meeting Title *</Text>
          <TextInput
            style={styles.input}
            value={meetingTitle}
            onChangeText={setMeetingTitle}
            placeholder="e.g., Monthly Committee Meeting - November 2025"
            placeholderTextColor="#8E8E93"
          />
        </View>

        {/* Meeting Date */}
        <View style={styles.section}>
          <Text style={styles.label}>Meeting Date *</Text>
          <TextInput
            style={styles.input}
            value={meetingDate}
            onChangeText={setMeetingDate}
            placeholder={`YYYY-MM-DD (e.g., ${getTodayDate()})`}
            placeholderTextColor="#8E8E93"
          />
        </View>

        {/* Meeting Time */}
        <View style={styles.section}>
          <Text style={styles.label}>Meeting Time</Text>
          <TextInput
            style={styles.input}
            value={meetingTime}
            onChangeText={setMeetingTime}
            placeholder="e.g., 10:00 AM"
            placeholderTextColor="#8E8E93"
          />
        </View>

        {/* Venue */}
        <View style={styles.section}>
          <Text style={styles.label}>Venue</Text>
          <TextInput
            style={styles.input}
            value={venue}
            onChangeText={setVenue}
            placeholder="Meeting venue/location"
            placeholderTextColor="#8E8E93"
          />
        </View>

        {/* Notice Sent To */}
        <View style={styles.section}>
          <Text style={styles.label}>Send Notice To</Text>
          <View style={styles.radioContainer}>
            <TouchableOpacity
              style={styles.radioButton}
              onPress={() => setNoticeSentTo('all_members')}>
              <View style={styles.radioCircle}>
                {noticeSentTo === 'all_members' && <View style={styles.radioInner} />}
              </View>
              <Text style={styles.radioLabel}>All Members</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.radioButton}
              onPress={() => setNoticeSentTo('mc_only')}>
              <View style={styles.radioCircle}>
                {noticeSentTo === 'mc_only' && <View style={styles.radioInner} />}
              </View>
              <Text style={styles.radioLabel}>MC Only</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Agenda Items */}
        <View style={styles.section}>
          <Text style={styles.label}>Agenda Items</Text>
          {agendaItems.map((item, index) => (
            <View key={index} style={styles.agendaItemCard}>
              <View style={styles.agendaItemHeader}>
                <Text style={styles.agendaItemNumber}>{item.item_number}.</Text>
                <TouchableOpacity
                  onPress={() => handleRemoveAgendaItem(index)}
                  style={styles.removeButton}>
                  <Icon name="close-circle" size={20} color="#FF3B30" />
                </TouchableOpacity>
              </View>
              <Text style={styles.agendaItemTitle}>{item.item_title}</Text>
              {item.item_description && (
                <Text style={styles.agendaItemDescription}>{item.item_description}</Text>
              )}
            </View>
          ))}

          <View style={styles.addAgendaContainer}>
            <TextInput
              style={[styles.input, styles.agendaTitleInput]}
              value={newAgendaItem.item_title}
              onChangeText={text => setNewAgendaItem({...newAgendaItem, item_title: text})}
              placeholder="Agenda item title"
              placeholderTextColor="#8E8E93"
            />
            <TextInput
              style={[styles.input, styles.agendaDescInput]}
              value={newAgendaItem.item_description}
              onChangeText={text =>
                setNewAgendaItem({...newAgendaItem, item_description: text})
              }
              placeholder="Description (optional)"
              placeholderTextColor="#8E8E93"
              multiline
            />
            <TouchableOpacity
              style={styles.addAgendaButton}
              onPress={handleAddAgendaItem}>
              <Icon name="add-circle" size={20} color="#007AFF" />
              <Text style={styles.addAgendaButtonText}>Add Agenda Item</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Save Button */}
        <TouchableOpacity
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={saving}>
          {saving ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Icon name="checkmark-circle" size={20} color="#FFF" />
              <Text style={styles.saveButtonText}>Create Meeting</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  form: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#FFF',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#000',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  typeContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    marginBottom: 8,
  },
  typeButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  typeButtonText: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500',
  },
  typeButtonTextActive: {
    color: '#FFF',
  },
  radioContainer: {
    flexDirection: 'row',
    gap: 24,
  },
  radioButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#007AFF',
    marginRight: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#007AFF',
  },
  radioLabel: {
    fontSize: 16,
    color: '#000',
  },
  agendaItemCard: {
    backgroundColor: '#FFF',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  agendaItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  agendaItemNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  removeButton: {
    padding: 4,
  },
  agendaItemTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  agendaItemDescription: {
    fontSize: 14,
    color: '#8E8E93',
  },
  addAgendaContainer: {
    marginTop: 12,
  },
  agendaTitleInput: {
    marginBottom: 8,
  },
  agendaDescInput: {
    minHeight: 60,
    marginBottom: 8,
  },
  addAgendaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
  },
  addAgendaButtonText: {
    fontSize: 16,
    color: '#007AFF',
    marginLeft: 6,
    fontWeight: '500',
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 8,
    marginTop: 8,
    marginBottom: 32,
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

export default CreateMeetingScreen;






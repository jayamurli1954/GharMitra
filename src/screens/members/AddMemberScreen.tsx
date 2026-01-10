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
  Modal,
  FlatList,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {flatsService, Flat} from '../../services/flatsService';
import {memberOnboardingService, MemberCreate} from '../../services/memberOnboardingService';

const AddMemberScreen = ({navigation}: any) => {
  const [flats, setFlats] = useState<Flat[]>([]);
  const [loadingFlats, setLoadingFlats] = useState(true);
  const [showFlatPicker, setShowFlatPicker] = useState(false);
  const [selectedFlat, setSelectedFlat] = useState<Flat | null>(null);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [name, setName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [memberType, setMemberType] = useState<'owner' | 'tenant'>('owner');
  const [moveInDate, setMoveInDate] = useState('');
  const [totalOccupants, setTotalOccupants] = useState('1');
  const [occupation, setOccupation] = useState('');
  const [isMobilePublic, setIsMobilePublic] = useState(false);

  useEffect(() => {
    loadFlats();
  }, []);

  const loadFlats = async () => {
    setLoadingFlats(true);
    try {
      const flatsList = await flatsService.getFlats();
      setFlats(flatsList);
    } catch (error: any) {
      console.error('Error loading flats:', error);
      Alert.alert('Error', 'Failed to load flats. Please try again.');
    } finally {
      setLoadingFlats(false);
    }
  };

  const handleSave = async () => {
    // Validation
    if (!selectedFlat) {
      Alert.alert('Validation Error', 'Please select a flat');
      return;
    }
    if (!name.trim()) {
      Alert.alert('Validation Error', 'Please enter member name');
      return;
    }
    if (!phoneNumber.trim() || phoneNumber.length < 10) {
      Alert.alert('Validation Error', 'Please enter a valid phone number');
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      Alert.alert('Validation Error', 'Please enter a valid email address');
      return;
    }
    if (!moveInDate) {
      Alert.alert('Validation Error', 'Please enter move-in date');
      return;
    }
    if (!totalOccupants || parseInt(totalOccupants) < 1) {
      Alert.alert('Validation Error', 'Please enter valid number of occupants');
      return;
    }

    setSaving(true);
    try {
      const memberData: MemberCreate = {
        flat_number: selectedFlat.flat_number,
        name: name.trim(),
        phone_number: phoneNumber.trim(),
        email: email.trim(),
        member_type: memberType,
        move_in_date: moveInDate,
        total_occupants: parseInt(totalOccupants),
        is_primary: true,
        occupation: occupation.trim() || undefined,
        is_mobile_public: isMobilePublic,
      };

      await memberOnboardingService.createMember(memberData);
      Alert.alert('Success', 'Member onboarded successfully!', [
        {
          text: 'OK',
          onPress: () => navigation.goBack(),
        },
      ]);
    } catch (error: any) {
      console.error('Error creating member:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to onboard member. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const renderFlatItem = ({item}: {item: Flat}) => (
    <TouchableOpacity
      style={styles.flatItem}
      onPress={() => {
        setSelectedFlat(item);
        setShowFlatPicker(false);
      }}
      activeOpacity={0.7}>
      <View style={styles.flatItemContent}>
        <View style={styles.flatItemHeader}>
          <Text style={styles.flatItemNumber}>Flat {item.flat_number}</Text>
          {selectedFlat?.id === item.id && (
            <Icon name="checkmark-circle" size={24} color="#007AFF" />
          )}
        </View>
        <View style={styles.flatItemDetails}>
          <View style={styles.flatDetailRow}>
            <Icon name="expand-outline" size={16} color="#8E8E93" />
            <Text style={styles.flatDetailText}>
              {item.area_sqft} sq ft
            </Text>
          </View>
          {item.bedrooms && (
            <View style={styles.flatDetailRow}>
              <Icon name="bed-outline" size={16} color="#8E8E93" />
              <Text style={styles.flatDetailText}>
                {item.bedrooms} BR
              </Text>
            </View>
          )}
          {item.owner_name && (
            <View style={styles.flatDetailRow}>
              <Icon name="person-outline" size={16} color="#8E8E93" />
              <Text style={styles.flatDetailText}>{item.owner_name}</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Flat Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Select Flat *</Text>
          <TouchableOpacity
            style={styles.flatSelector}
            onPress={() => setShowFlatPicker(true)}
            activeOpacity={0.7}>
            {selectedFlat ? (
              <View style={styles.selectedFlatInfo}>
                <View style={styles.selectedFlatHeader}>
                  <Text style={styles.selectedFlatNumber}>
                    Flat {selectedFlat.flat_number}
                  </Text>
                  <Icon name="chevron-down" size={20} color="#8E8E93" />
                </View>
                <View style={styles.selectedFlatDetails}>
                  <Text style={styles.selectedFlatDetail}>
                    {selectedFlat.area_sqft} sq ft
                  </Text>
                  {selectedFlat.bedrooms && (
                    <Text style={styles.selectedFlatDetail}>
                      • {selectedFlat.bedrooms} BR
                    </Text>
                  )}
                </View>
              </View>
            ) : (
              <View style={styles.flatSelectorPlaceholder}>
                <Text style={styles.flatSelectorPlaceholderText}>
                  Tap to select a flat
                </Text>
                <Icon name="chevron-down" size={20} color="#8E8E93" />
              </View>
            )}
          </TouchableOpacity>
        </View>

        {/* Member Details */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Member Details</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Full Name *</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter member name"
              value={name}
              onChangeText={setName}
              autoCapitalize="words"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Phone Number *</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter phone number"
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              keyboardType="phone-pad"
              maxLength={15}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Email Address *</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter email address"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Member Type *</Text>
            <View style={styles.radioGroup}>
              <TouchableOpacity
                style={[
                  styles.radioOption,
                  memberType === 'owner' && styles.radioOptionSelected,
                ]}
                onPress={() => setMemberType('owner')}
                activeOpacity={0.7}>
                <Icon
                  name={memberType === 'owner' ? 'radio-button-on' : 'radio-button-off'}
                  size={20}
                  color={memberType === 'owner' ? '#007AFF' : '#8E8E93'}
                />
                <Text
                  style={[
                    styles.radioOptionText,
                    memberType === 'owner' && styles.radioOptionTextSelected,
                  ]}>
                  Owner
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.radioOption,
                  memberType === 'tenant' && styles.radioOptionSelected,
                ]}
                onPress={() => setMemberType('tenant')}
                activeOpacity={0.7}>
                <Icon
                  name={memberType === 'tenant' ? 'radio-button-on' : 'radio-button-off'}
                  size={20}
                  color={memberType === 'tenant' ? '#007AFF' : '#8E8E93'}
                />
                <Text
                  style={[
                    styles.radioOptionText,
                    memberType === 'tenant' && styles.radioOptionTextSelected,
                  ]}>
                  Tenant
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Occupation (Optional)</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g., Employed, Business, Professional"
              value={occupation}
              onChangeText={setOccupation}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Move-In Date *</Text>
            <TextInput
              style={styles.input}
              placeholder="YYYY-MM-DD (e.g., 2024-01-15)"
              value={moveInDate}
              onChangeText={setMoveInDate}
            />
            <Text style={styles.helperText}>
              Format: YYYY-MM-DD
            </Text>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Total Occupants *</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter number of occupants"
              value={totalOccupants}
              onChangeText={setTotalOccupants}
              keyboardType="number-pad"
            />
          </View>

          <View style={styles.inputGroup}>
            <TouchableOpacity
              style={styles.checkbox}
              onPress={() => setIsMobilePublic(!isMobilePublic)}
              activeOpacity={0.7}>
              <Icon
                name={isMobilePublic ? 'checkbox' : 'square-outline'}
                size={24}
                color={isMobilePublic ? '#007AFF' : '#8E8E93'}
              />
              <Text style={styles.checkboxLabel}>
                Make mobile number visible to other members
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Save Button */}
        <TouchableOpacity
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={saving}
          activeOpacity={0.7}>
          {saving ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Icon name="checkmark-circle" size={20} color="#FFF" />
              <Text style={styles.saveButtonText}>Onboard Member</Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>

      {/* Flat Picker Modal */}
      <Modal
        visible={showFlatPicker}
        animationType="slide"
        transparent={false}
        onRequestClose={() => setShowFlatPicker(false)}>
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Select Flat</Text>
            <TouchableOpacity
              onPress={() => setShowFlatPicker(false)}
              activeOpacity={0.7}>
              <Icon name="close" size={28} color="#1D1D1F" />
            </TouchableOpacity>
          </View>
          {loadingFlats ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007AFF" />
              <Text style={styles.loadingText}>Loading flats...</Text>
            </View>
          ) : (
            <FlatList
              data={flats}
              renderItem={renderFlatItem}
              keyExtractor={(item) => item.id}
              contentContainerStyle={styles.flatList}
              ListEmptyComponent={
                <View style={styles.emptyState}>
                  <Icon name="home-outline" size={60} color="#C7C7CC" />
                  <Text style={styles.emptyStateText}>No flats available</Text>
                  <Text style={styles.emptyStateSubtext}>
                    Please add flats first
                  </Text>
                </View>
              }
            />
          )}
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 12,
  },
  flatSelector: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  selectedFlatInfo: {
    flexDirection: 'column',
  },
  selectedFlatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  selectedFlatNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  selectedFlatDetails: {
    flexDirection: 'row',
    gap: 12,
  },
  selectedFlatDetail: {
    fontSize: 14,
    color: '#8E8E93',
  },
  flatSelectorPlaceholder: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  flatSelectorPlaceholderText: {
    fontSize: 16,
    color: '#8E8E93',
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#1D1D1F',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  helperText: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
    marginLeft: 4,
  },
  radioGroup: {
    flexDirection: 'row',
    gap: 16,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    backgroundColor: '#FFF',
    gap: 8,
    flex: 1,
  },
  radioOptionSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD',
  },
  radioOptionText: {
    fontSize: 16,
    color: '#8E8E93',
  },
  radioOptionTextSelected: {
    color: '#007AFF',
    fontWeight: '600',
  },
  checkbox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 12,
    backgroundColor: '#FFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  checkboxLabel: {
    fontSize: 14,
    color: '#1D1D1F',
    flex: 1,
  },
  saveButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 8,
    marginBottom: 32,
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#8E8E93',
  },
  flatList: {
    padding: 16,
  },
  flatItem: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  flatItemContent: {
    flexDirection: 'column',
  },
  flatItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  flatItemNumber: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  flatItemDetails: {
    flexDirection: 'row',
    gap: 16,
    flexWrap: 'wrap',
  },
  flatDetailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  flatDetailText: {
    fontSize: 14,
    color: '#8E8E93',
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
});

export default AddMemberScreen;


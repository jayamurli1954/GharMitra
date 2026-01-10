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
import {flatsService, Flat, FlatCreate, FlatUpdate} from '../../services/flatsService';
import ENV from '../../config/env';

const AddEditFlatScreen = ({route, navigation}: any) => {
  // Debug: Log route params to see what we're receiving
  console.log('AddEditFlatScreen - Route params:', {
    hasParams: !!route.params,
    hasFlat: !!route.params?.flat,
    flatId: route.params?.flat?.id,
    flatNumber: route.params?.flat?.flat_number,
    fullParams: route.params,
  });

  const existingFlat: Flat | undefined = route.params?.flat;
  const isEdit = !!existingFlat;
  const [currentFlat, setCurrentFlat] = useState<Flat | undefined>(existingFlat);
  const [loadingFlat, setLoadingFlat] = useState(false);

  const [flatNumber, setFlatNumber] = useState(existingFlat?.flat_number || '');
  const [area, setArea] = useState(existingFlat?.area_sqft ? String(existingFlat.area_sqft) : '');
  const [numberOfOccupants, setNumberOfOccupants] = useState(
    existingFlat?.occupants ? String(existingFlat.occupants) : '',
  );
  const [ownerName, setOwnerName] = useState(existingFlat?.owner_name || '');
  const [ownerEmail, setOwnerEmail] = useState(existingFlat?.owner_email || '');
  const [ownerPhone, setOwnerPhone] = useState(existingFlat?.owner_phone || '');
  const [saving, setSaving] = useState(false);

  // Load flat data when in edit mode
  useEffect(() => {
    const loadFlatData = async () => {
      if (!isEdit) {
        return;
      }

      const flatFromRoute = route.params?.flat;
      
      console.log('Edit mode - Initial flat data:', {
        hasRouteFlat: !!flatFromRoute,
        routeFlatId: flatFromRoute?.id,
        routeFlatIdType: typeof flatFromRoute?.id,
        routeFlatNumber: flatFromRoute?.flat_number,
        routeFlatKeys: flatFromRoute ? Object.keys(flatFromRoute) : [],
      });

      // Strategy: Always try to reload from API if we have an ID
      // This ensures we have the most up-to-date and complete data
      if (flatFromRoute?.id) {
        const flatIdStr = String(flatFromRoute.id).trim();
        
        // Validate ID is not empty or invalid
        if (flatIdStr && flatIdStr !== 'undefined' && flatIdStr !== 'null' && flatIdStr !== '') {
          console.log('Loading flat from API with ID:', flatIdStr);
          setLoadingFlat(true);
          try {
            const flat = await flatsService.getFlat(flatIdStr);
            console.log('✅ Successfully loaded flat:', {
              id: flat.id,
              flatNumber: flat.flat_number,
              ownerName: flat.owner_name,
            });
            setCurrentFlat(flat);
            // Update form fields
            setFlatNumber(flat.flat_number);
            setArea(String(flat.area_sqft));
            setNumberOfOccupants(String(flat.occupants));
            setOwnerName(flat.owner_name);
            setOwnerEmail(flat.owner_email || '');
            setOwnerPhone(flat.owner_phone || '');
            setLoadingFlat(false);
            return;
          } catch (error: any) {
            console.error('❌ Error loading flat by ID:', error);
            console.error('Error details:', {
              message: error.message,
              status: error.response?.status,
              data: error.response?.data,
            });
            
            // If API call fails, try fallback: find by flat_number
            if (flatFromRoute.flat_number) {
              console.log('Trying fallback: finding flat by flat_number:', flatFromRoute.flat_number);
              try {
                const allFlats = await flatsService.getFlats();
                const foundFlat = allFlats.find(f => f.flat_number === flatFromRoute.flat_number);
                if (foundFlat) {
                  console.log('✅ Found flat by flat_number:', {
                    id: foundFlat.id,
                    flatNumber: foundFlat.flat_number,
                  });
                  setCurrentFlat(foundFlat);
                  setFlatNumber(foundFlat.flat_number);
                  setArea(String(foundFlat.area_sqft));
                  setNumberOfOccupants(String(foundFlat.occupants));
                  setOwnerName(foundFlat.owner_name);
                  setOwnerEmail(foundFlat.owner_email || '');
                  setOwnerPhone(foundFlat.owner_phone || '');
                  setLoadingFlat(false);
                  return;
                }
              } catch (fallbackError) {
                console.error('❌ Fallback also failed:', fallbackError);
              }
            }
            
            setLoadingFlat(false);
            Alert.alert(
              'Error',
              `Failed to load flat data. Please go back and try again.\n\nError: ${error.response?.data?.detail || error.message}`,
            );
            return;
          }
        }
      }
      
      // Fallback: If we have flat_number but no valid ID, try to find by flat_number
      if (flatFromRoute?.flat_number && (!flatFromRoute.id || String(flatFromRoute.id).trim() === '')) {
        console.log('No valid ID, trying to find flat by flat_number:', flatFromRoute.flat_number);
        setLoadingFlat(true);
        try {
          const allFlats = await flatsService.getFlats();
          const foundFlat = allFlats.find(f => f.flat_number === flatFromRoute.flat_number);
          if (foundFlat) {
            console.log('✅ Found flat by flat_number:', {
              id: foundFlat.id,
              flatNumber: foundFlat.flat_number,
            });
            setCurrentFlat(foundFlat);
            setFlatNumber(foundFlat.flat_number);
            setArea(String(foundFlat.area_sqft));
            setNumberOfOccupants(String(foundFlat.occupants));
            setOwnerName(foundFlat.owner_name);
            setOwnerEmail(foundFlat.owner_email || '');
            setOwnerPhone(foundFlat.owner_phone || '');
            setLoadingFlat(false);
            return;
          } else {
            console.error('❌ Flat not found with flat_number:', flatFromRoute.flat_number);
            setLoadingFlat(false);
            Alert.alert(
              'Error',
              `Flat ${flatFromRoute.flat_number} not found. Please go back and try again.`,
            );
            return;
          }
        } catch (error: any) {
          console.error('❌ Error finding flat by number:', error);
          setLoadingFlat(false);
          Alert.alert(
            'Error',
            `Failed to find flat. Please go back and try again.\n\nError: ${error.message}`,
          );
          return;
        }
      }
      
      // Last resort: If we have some flat data from route, use it (but warn)
      if (flatFromRoute && flatFromRoute.flat_number) {
        console.warn('⚠️ Using incomplete flat data from route params');
        setCurrentFlat(flatFromRoute as Flat);
        setFlatNumber(flatFromRoute.flat_number);
        setArea(String(flatFromRoute.area_sqft || ''));
        setNumberOfOccupants(String(flatFromRoute.occupants || ''));
        setOwnerName(flatFromRoute.owner_name || '');
        setOwnerEmail(flatFromRoute.owner_email || '');
        setOwnerPhone(flatFromRoute.owner_phone || '');
      } else {
        console.error('❌ No flat data available');
        Alert.alert(
          'Error',
          'Flat data is missing. Please go back to the flat list and try editing again.',
        );
      }
    };
    
    loadFlatData();
  }, [isEdit, route.params]);

  useEffect(() => {
    navigation.setOptions({
      title: isEdit ? 'Edit Flat' : 'Add Flat',
    });
    
    // Debug: Log flat data when editing
    if (isEdit && currentFlat) {
      console.log('Edit Flat - Flat data:', {
        id: currentFlat.id,
        idType: typeof currentFlat.id,
        flatNumber: currentFlat.flat_number,
        hasAllFields: !!(currentFlat.id && currentFlat.flat_number && currentFlat.owner_name),
      });
    }
  }, [isEdit, currentFlat]);

  const handleSave = async () => {
    if (!flatNumber || !area || !numberOfOccupants || !ownerName) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }

    const areaNum = parseFloat(area);
    const occupantsNum = parseInt(numberOfOccupants);

    if (isNaN(areaNum) || areaNum <= 0) {
      Alert.alert('Error', 'Please enter a valid area');
      return;
    }

    if (isNaN(occupantsNum) || occupantsNum < 0) {
      Alert.alert('Error', 'Please enter a valid number of occupants');
      return;
    }

    setSaving(true);
    try {
      if (isEdit) {
        // Priority: currentFlat (loaded from API) > route params > existingFlat
        const flatToUpdate = currentFlat || route.params?.flat || existingFlat;
        
        console.log('💾 Saving flat - Data check:', {
          hasCurrentFlat: !!currentFlat,
          currentFlatId: currentFlat?.id,
          hasRouteFlat: !!route.params?.flat,
          routeFlatId: route.params?.flat?.id,
          hasExistingFlat: !!existingFlat,
          existingFlatId: existingFlat?.id,
          usingFlat: flatToUpdate ? {
            id: flatToUpdate.id,
            idType: typeof flatToUpdate.id,
            flatNumber: flatToUpdate.flat_number,
          } : null,
        });
        
        if (!flatToUpdate) {
          console.error('❌ No flat data available for update');
          Alert.alert(
            'Error',
            'Flat data is missing. Please go back and try again.',
          );
          setSaving(false);
          return;
        }

        // Validate flat ID exists and is valid
        let flatIdStr: string | null = null;
        
        if (flatToUpdate.id) {
          flatIdStr = String(flatToUpdate.id).trim();
          
          // Check if ID is valid (not empty, undefined, null, etc.)
          if (!flatIdStr || flatIdStr === 'undefined' || flatIdStr === 'null' || flatIdStr === '') {
            console.error('❌ Invalid flat ID string:', {
              originalId: flatToUpdate.id,
              idType: typeof flatToUpdate.id,
              idString: flatIdStr,
            });
            flatIdStr = null;
          }
        }
        
        // If ID is still missing, try to find flat by flat_number as last resort
        if (!flatIdStr && flatNumber) {
          console.warn('⚠️ Flat ID missing, trying to find by flat_number:', flatNumber);
          try {
            const allFlats = await flatsService.getFlats();
            const foundFlat = allFlats.find(f => f.flat_number === flatNumber.trim());
            if (foundFlat && foundFlat.id) {
              flatIdStr = String(foundFlat.id).trim();
              console.log('✅ Found flat ID by flat_number:', flatIdStr);
            }
          } catch (error) {
            console.error('❌ Error finding flat by number:', error);
          }
        }
        
        // Final validation
        if (!flatIdStr) {
          console.error('❌ Flat ID is missing. Cannot update flat.');
          console.error('Flat object:', flatToUpdate);
          console.error('Route params:', route.params);
          Alert.alert(
            'Error',
            `Flat ID is missing. Please go back to the flat list and try editing flat ${flatNumber || 'this flat'} again.`,
          );
          setSaving(false);
          return;
        }

        // Update existing flat
        const updateData: FlatUpdate = {
          area_sqft: areaNum,
          occupants: occupantsNum,
          owner_name: ownerName.trim(),
          owner_email: ownerEmail.trim() || undefined,
          owner_phone: ownerPhone.trim() || undefined,
        };

        console.log('💾 Updating flat:', {
          id: flatIdStr,
          flatIdType: typeof flatIdStr,
          flatNumber: flatNumber,
          data: updateData,
          fullUrl: `${ENV.API_URL}/flats/${flatIdStr}`,
        });
        
        // Double-check the ID is valid before making the request
        if (!flatIdStr || flatIdStr.trim() === '') {
          throw new Error('Flat ID is empty or invalid');
        }
        
        await flatsService.updateFlat(flatIdStr, updateData);
        
        console.log('✅ Flat updated successfully');
        
        // Navigate back immediately - this triggers useFocusEffect in FlatsListScreen
        navigation.goBack();
        
        // Show success message after a short delay to allow navigation to complete
        setTimeout(() => {
          Alert.alert('Success', 'Flat updated successfully');
        }, 500);
      } else {
        // Create new flat
        const flatData: FlatCreate = {
          flat_number: flatNumber.trim(),
          area_sqft: areaNum,
          occupants: occupantsNum,
          owner_name: ownerName.trim(),
          owner_email: ownerEmail.trim() || undefined,
          owner_phone: ownerPhone.trim() || undefined,
        };

        await flatsService.createFlat(flatData);
        
        // Navigate back immediately - this triggers useFocusEffect in FlatsListScreen
        navigation.goBack();
        
        // Show success message after a short delay to allow navigation to complete
        setTimeout(() => {
          Alert.alert('Success', 'Flat added successfully');
        }, 500);
      }
    } catch (error: any) {
      console.error('❌ Error saving flat:', error);
      console.error('Error details:', {
        message: error.message,
        code: error.code,
        status: error.status || error.response?.status,
        response: error.response?.data,
        flatId: isEdit ? (currentFlat?.id || existingFlat?.id) : 'N/A',
        requestUrl: isEdit ? `${ENV.API_URL}/flats/${flatIdStr}` : `${ENV.API_URL}/flats`,
        requestMethod: isEdit ? 'PUT' : 'POST',
      });
      
      let errorMessage = 'Failed to save flat. Please try again.';
      let errorDetails = '';
      
      // Handle specific error types
      if (error.code === 'FORBIDDEN' || error.status === 403) {
        errorMessage = 'Admin access required. You must be logged in as an administrator to edit flats.';
      } else if (error.code === 'NOT_FOUND' || error.status === 404) {
        errorMessage = 'Flat not found. The flat may have been deleted. Please refresh the list.';
        errorDetails = `Flat ID: ${flatIdStr}`;
      } else if (error.code === 'CONNECTION_ERROR') {
        errorMessage = error.message || 'Cannot connect to server. Please check your connection.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
        errorDetails = `Status: ${error.response.status}`;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Provide more helpful error messages
      const flatId = currentFlat?.id || existingFlat?.id;
      if (errorMessage.includes('Invalid flat ID')) {
        errorMessage = `Invalid flat ID: "${flatId}". Please go back and try editing again.`;
      } else if (errorMessage.includes('Flat not found')) {
        errorMessage = `Flat not found. The flat may have been deleted. Please refresh the list.`;
      }
      
      // Show detailed error for debugging
      const fullErrorMessage = errorDetails 
        ? `${errorMessage}\n\n${errorDetails}\n\nCheck console for more details.`
        : `${errorMessage}\n\nCheck console for more details.`;
      
      Alert.alert('Error', fullErrorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loadingFlat) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading flat data...</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Icon name="home" size={50} color="#007AFF" />
        <Text style={styles.headerTitle}>
          {isEdit ? 'Edit Flat Details' : 'Add New Flat'}
        </Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.sectionTitle}>Flat Information</Text>

        <Text style={styles.label}>Flat Number *</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., 101, A-201"
          value={flatNumber}
          onChangeText={setFlatNumber}
          editable={!isEdit}
        />
        {isEdit && (
          <Text style={styles.hint}>Flat number cannot be changed</Text>
        )}

        <Text style={styles.label}>Area (sq ft) *</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter area in square feet"
          value={area}
          onChangeText={setArea}
          keyboardType="decimal-pad"
        />

        <Text style={styles.label}>Number of Occupants *</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter number of people"
          value={numberOfOccupants}
          onChangeText={setNumberOfOccupants}
          keyboardType="number-pad"
        />
        <Text style={styles.hint}>
          Required for calculating water charges in variable method
        </Text>

        <Text style={styles.sectionTitle}>Owner Information</Text>

        <Text style={styles.label}>Owner Name *</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter owner's full name"
          value={ownerName}
          onChangeText={setOwnerName}
          autoCapitalize="words"
        />

        <Text style={styles.label}>Email (Optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter email address"
          value={ownerEmail}
          onChangeText={setOwnerEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />

        <Text style={styles.label}>Phone Number (Optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter phone number"
          value={ownerPhone}
          onChangeText={setOwnerPhone}
          keyboardType="phone-pad"
        />

        <TouchableOpacity
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={saving}>
          {saving ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Icon name="checkmark-circle" size={24} color="#FFF" />
          )}
          <Text style={styles.saveButtonText}>
            {saving ? 'Saving...' : isEdit ? 'Update Flat' : 'Add Flat'}
          </Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 30,
    alignItems: 'center',
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFF',
    marginTop: 15,
  },
  form: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 20,
    marginBottom: 15,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    marginTop: 10,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 10,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#FFF',
  },
  hint: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
    fontStyle: 'italic',
  },
  saveButton: {
    flexDirection: 'row',
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 30,
    marginBottom: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.2,
    shadowRadius: 4,
    gap: 10,
  },
  saveButtonDisabled: {
    backgroundColor: '#A0C4FF',
  },
  saveButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default AddEditFlatScreen;

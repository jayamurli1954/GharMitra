import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {templateService, TemplateDetails} from '../../services/resourceService';
import {useNavigation, useRoute} from '@react-navigation/native';
import {authService, User} from '../../services/authService';

const GenerateDocumentScreen = () => {
  const navigation = useNavigation();
  const route = useRoute();
  // @ts-ignore
  const {template: initialTemplate} = route.params || {};

  const [template, setTemplate] = useState<TemplateDetails | null>(
    initialTemplate || null
  );
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [autoFillData, setAutoFillData] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [loadingTemplate, setLoadingTemplate] = useState(!initialTemplate);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    loadUser();
    if (initialTemplate && !initialTemplate.template_variables) {
      loadTemplateDetails();
    } else {
      // Will be called after user is loaded
    }
  }, []);

  useEffect(() => {
    if (user) {
      loadAutoFillData();
    }
  }, [user]);

  const loadUser = async () => {
    try {
      // Try to get from backend first, fallback to stored user
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        // If backend fails, try stored user
        const storedUser = await authService.getStoredUser();
        if (storedUser) {
          setUser(storedUser);
        }
      }
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  const loadTemplateDetails = async () => {
    if (!initialTemplate) return;
    try {
      setLoadingTemplate(true);
      const details = await templateService.getTemplateDetails(
        initialTemplate.id
      );
      setTemplate(details);
    } catch (error: any) {
      console.error('Error loading template details:', error);
      Alert.alert('Error', 'Failed to load template details');
    } finally {
      setLoadingTemplate(false);
    }
  };

  const loadAutoFillData = () => {
    if (!user) return;
    // Auto-fill data from user profile
    // Note: society_name and society_address will be auto-filled by backend
    setAutoFillData({
      member_name: user.name || '',
      flat_number: user.apartment_number || '',
      member_email: user.email || '',
      member_phone: user.phone_number || '',
      // Society info will be filled by backend from user's society_id
      society_name: '',
      society_address: '',
    });
  };

  const handleGenerate = async () => {
    if (!template) return;

    setLoading(true);

    try {
      const blob = await templateService.generateDocument(
        template.id,
        formData
      );

      // For React Native, show success message
      // The PDF blob is available but needs to be saved using react-native-fs
      // For now, we'll just confirm the generation
      Alert.alert(
        'Document Generated!',
        'PDF has been generated successfully. In production, this will be saved to your device. Please submit physical copy to society office.',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
      setLoading(false);
      
      // TODO: In production, use react-native-fs to save the file:
      // import RNFS from 'react-native-fs';
      // const path = `${RNFS.DocumentDirectoryPath}/${template.template_code}_${Date.now()}.pdf`;
      // await RNFS.writeFile(path, blob, 'base64');
    } catch (error: any) {
      console.error('Error generating document:', error);
      Alert.alert('Error', error.message || 'Failed to generate document');
      setLoading(false);
    }
  };

  if (loadingTemplate || !template) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading template...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Instructions */}
      {template.instructions && (
        <View style={styles.instructionsBox}>
          <Icon name="information-circle" size={20} color="#007AFF" />
          <Text style={styles.instructionsText}>{template.instructions}</Text>
        </View>
      )}

      {/* Auto-filled Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="checkmark-circle" size={20} color="#4CAF50" />
          <Text style={styles.sectionTitle}>Auto-filled Information</Text>
        </View>

        {Object.entries(autoFillData).map(([key, value]) => (
          <View key={key} style={styles.readOnlyField}>
            <Text style={styles.fieldLabel}>
              {key
                .replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase())}
            </Text>
            <Text style={styles.fieldValue}>{value || 'N/A'}</Text>
          </View>
        ))}
      </View>

      {/* User Input Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="create-outline" size={20} color="#FF9800" />
          <Text style={styles.sectionTitle}>Additional Information</Text>
        </View>

        {/* Dynamic fields based on template variables */}
        {template.template_variables
          ?.filter(v => !autoFillData[v])
          .map(variable => (
            <View key={variable} style={styles.inputContainer}>
              <Text style={styles.inputLabel}>
                {variable
                  .replace(/_/g, ' ')
                  .replace(/\b\w/g, l => l.toUpperCase())}
              </Text>
              <TextInput
                style={styles.input}
                placeholder={`Enter ${variable.replace(/_/g, ' ')}`}
                value={formData[variable] || ''}
                onChangeText={text =>
                  setFormData({...formData, [variable]: text})
                }
                multiline={variable.includes('description') || variable.includes('details')}
              />
            </View>
          ))}

        {/* Default fields if no template variables */}
        {(!template.template_variables ||
          template.template_variables.length === 0) && (
          <>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Reason / Purpose</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter reason"
                value={formData.reason || ''}
                onChangeText={text =>
                  setFormData({...formData, reason: text})
                }
                multiline
              />
            </View>

            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Additional Details</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="Any additional information"
                value={formData.details || ''}
                onChangeText={text =>
                  setFormData({...formData, details: text})
                }
                multiline
                numberOfLines={4}
              />
            </View>
          </>
        )}
      </View>

      {/* Generate Button */}
      <TouchableOpacity
        style={[styles.generateButton, loading && styles.buttonDisabled]}
        onPress={handleGenerate}
        disabled={loading}>
        {loading ? (
          <ActivityIndicator color="#FFF" />
        ) : (
          <>
            <Icon name="document-text" size={20} color="#FFF" />
            <Text style={styles.generateButtonText}>Generate PDF</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Info Box */}
      <View style={styles.infoBox}>
        <Icon name="information-circle-outline" size={18} color="#666" />
        <Text style={styles.infoText}>
          The PDF will be saved to your device. Please print and submit to
          society office for records. We do not store filled forms online.
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },
  instructionsBox: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    padding: 16,
    margin: 16,
    borderRadius: 8,
    gap: 12,
  },
  instructionsText: {
    flex: 1,
    fontSize: 14,
    color: '#1976D2',
    lineHeight: 20,
  },
  section: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  readOnlyField: {
    marginBottom: 12,
  },
  fieldLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  fieldValue: {
    fontSize: 14,
    color: '#1D1D1F',
    fontWeight: '500',
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#424242',
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    backgroundColor: '#FAFAFA',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  generateButton: {
    flexDirection: 'row',
    backgroundColor: '#007AFF',
    marginHorizontal: 16,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  generateButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    padding: 16,
    margin: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#666',
    lineHeight: 20,
  },
});

export default GenerateDocumentScreen;


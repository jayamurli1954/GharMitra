import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  Modal,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import {format} from 'date-fns';
import {
  physicalDocumentsService,
  PhysicalDocument,
  CreatePhysicalDocumentRequest,
} from '../../services/physicalDocumentsService';

// ============= TYPES =============

interface DocumentTypeConfig {
  key: string;
  label: string;
  icon: string;
  color: string;
  description: string;
}

// ============= CONSTANTS =============

const DOCUMENT_TYPES: DocumentTypeConfig[] = [
  {
    key: 'aadhaar',
    label: 'Aadhaar Card',
    icon: 'card-account-details',
    color: '#2196F3',
    description: 'Identity proof (submit photocopy only)',
  },
  {
    key: 'pan',
    label: 'PAN Card',
    icon: 'card-text',
    color: '#4CAF50',
    description: 'For GST invoicing (submit photocopy)',
  },
  {
    key: 'passport',
    label: 'Passport',
    icon: 'passport',
    color: '#9C27B0',
    description: 'Optional identity proof',
  },
  {
    key: 'driving_license',
    label: 'Driving License',
    icon: 'car',
    color: '#FF5722',
    description: 'Optional identity proof',
  },
  {
    key: 'rent_agreement',
    label: 'Rent Agreement',
    icon: 'file-document',
    color: '#FF9800',
    description: 'For tenants only',
  },
  {
    key: 'sale_deed',
    label: 'Sale Deed',
    icon: 'file-certificate',
    color: '#F44336',
    description: 'For owners only',
  },
  {
    key: 'electricity_bill',
    label: 'Electricity Bill',
    icon: 'lightning-bolt',
    color: '#FFC107',
    description: 'Recent bill (last 3 months)',
  },
  {
    key: 'water_bill',
    label: 'Water Bill',
    icon: 'water',
    color: '#00BCD4',
    description: 'Recent bill (last 3 months)',
  },
];

// ============= MAIN COMPONENT =============

const PhysicalDocumentsScreen = ({route, navigation}: any) => {
  const {memberId, memberName} = route.params || {};

  const [documents, setDocuments] = useState<PhysicalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedDocType, setSelectedDocType] = useState<DocumentTypeConfig | null>(null);
  const [storageLocation, setStorageLocation] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [verifying, setVerifying] = useState<string | null>(null);

  useEffect(() => {
    if (memberId) {
      loadDocuments();
    }
  }, [memberId]);

  const loadDocuments = async () => {
    if (!memberId) {
      setError('Member ID is required');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const docs = await physicalDocumentsService.getPhysicalDocuments(memberId);
      setDocuments(docs);
    } catch (err: any) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitDocument = (docType: DocumentTypeConfig) => {
    setSelectedDocType(docType);
    setModalVisible(true);
  };

  const confirmSubmit = async () => {
    if (!storageLocation.trim()) {
      Alert.alert('Error', 'Please enter storage location');
      return;
    }

    if (!selectedDocType || !memberId) return;

    setSubmitting(true);
    try {
      const data: CreatePhysicalDocumentRequest = {
        member_id: memberId,
        document_type: selectedDocType.key,
        storage_location: storageLocation.trim(),
      };

      await physicalDocumentsService.createPhysicalDocument(data);
      setModalVisible(false);
      setStorageLocation('');
      setSelectedDocType(null);
      Alert.alert('Success', 'Document marked as submitted');
      loadDocuments();
    } catch (err: any) {
      console.error('Error submitting document:', err);
      Alert.alert('Error', err.message || 'Failed to submit document');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = (doc: PhysicalDocument) => {
    Alert.alert(
      'Verify Document',
      `Have you physically verified the ${doc.document_type.replace('_', ' ')} document in the filing cabinet?`,
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Verify',
          onPress: async () => {
            setVerifying(doc.id);
            try {
              await physicalDocumentsService.verifyPhysicalDocument(doc.id, {
                verification_notes: 'Verified physically in office',
              });
              Alert.alert('Success', 'Document verified successfully');
              loadDocuments();
            } catch (err: any) {
              console.error('Error verifying document:', err);
              Alert.alert('Error', err.message || 'Failed to verify document');
            } finally {
              setVerifying(null);
            }
          },
        },
      ]
    );
  };

  const handleDelete = (doc: PhysicalDocument) => {
    Alert.alert(
      'Delete Entry',
      'This will remove the checklist entry. The physical document will remain in the filing cabinet. Continue?',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await physicalDocumentsService.deletePhysicalDocument(doc.id);
              Alert.alert('Success', 'Document entry deleted');
              loadDocuments();
            } catch (err: any) {
              console.error('Error deleting document:', err);
              Alert.alert('Error', err.message || 'Failed to delete document');
            }
          },
        },
      ]
    );
  };

  // ============= LOADING & ERROR STATES =============

  if (loading && documents.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Loading documents...</Text>
      </View>
    );
  }

  if (error && documents.length === 0) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="alert-circle" size={48} color="#F44336" />
        <Text style={styles.errorText}>Failed to load documents</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadDocuments}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ============= RENDER =============

  return (
    <View style={styles.container}>
      <ScrollView>
        {/* Header */}
        <View style={styles.header}>
          <Icon name="file-cabinet" size={48} color="#2196F3" />
          <Text style={styles.headerTitle}>
            {memberName || 'Member'}'s Documents
          </Text>
          <Text style={styles.headerSubtitle}>Physical Storage Checklist</Text>
        </View>

        {/* Info Banner */}
        <View style={styles.infoBanner}>
          <Icon name="information" size={20} color="#2196F3" />
          <Text style={styles.infoText}>
            <Text style={styles.infoBold}>100% Physical Storage:</Text> All
            documents are stored in your Society office filing cabinet. This
            checklist tracks submission status only. No files uploaded online.
          </Text>
        </View>

        {/* Document Cards */}
        {DOCUMENT_TYPES.map(docType => {
          const doc = documents.find(d => d.document_type === docType.key);
          const submitted = doc?.submitted || false;
          const verified = doc?.verified || false;

          return (
            <View key={docType.key} style={styles.card}>
              {/* Header */}
              <View style={styles.cardHeader}>
                <View
                  style={[
                    styles.iconCircle,
                    {backgroundColor: docType.color + '20'},
                  ]}>
                  <Icon name={docType.icon} size={28} color={docType.color} />
                </View>
                <View style={styles.cardTitleContainer}>
                  <Text style={styles.cardTitle}>{docType.label}</Text>
                  <Text style={styles.cardDescription}>
                    {docType.description}
                  </Text>
                </View>
              </View>

              {/* Status */}
              <View style={styles.statusContainer}>
                {submitted ? (
                  <>
                    <View style={styles.statusBadge}>
                      <Icon name="check-circle" size={16} color="#4CAF50" />
                      <Text style={styles.statusText}>Submitted</Text>
                    </View>
                    {doc?.submission_date && (
                      <Text style={styles.dateText}>
                        on{' '}
                        {format(
                          new Date(doc.submission_date),
                          'dd MMM yyyy'
                        )}
                      </Text>
                    )}
                  </>
                ) : (
                  <View
                    style={[styles.statusBadge, styles.statusBadgePending]}>
                    <Icon name="alert-circle" size={16} color="#FF9800" />
                    <Text
                      style={[styles.statusText, styles.statusTextPending]}>
                      Not Submitted
                    </Text>
                  </View>
                )}
              </View>

              {/* Storage Location */}
              {doc?.storage_location && (
                <View style={styles.locationContainer}>
                  <Icon name="map-marker" size={14} color="#757575" />
                  <Text style={styles.locationText}>
                    {doc.storage_location}
                  </Text>
                </View>
              )}

              {/* Verification */}
              {submitted && (
                <View style={styles.verificationContainer}>
                  {verified ? (
                    <View style={styles.verifiedBadge}>
                      <Icon name="shield-check" size={16} color="#4CAF50" />
                      <Text style={styles.verifiedText}>
                        Verified by {doc?.verified_by_name || 'Admin'}
                      </Text>
                      {doc?.verification_date && (
                        <Text style={styles.verifiedDate}>
                          {' '}
                          on{' '}
                          {format(
                            new Date(doc.verification_date),
                            'dd MMM yyyy'
                          )}
                        </Text>
                      )}
                    </View>
                  ) : (
                    <TouchableOpacity
                      style={styles.verifyButton}
                      onPress={() => doc && handleVerify(doc)}
                      disabled={verifying === doc?.id}>
                      {verifying === doc?.id ? (
                        <ActivityIndicator size="small" color="#2196F3" />
                      ) : (
                        <>
                          <Icon
                            name="shield-check-outline"
                            size={16}
                            color="#2196F3"
                          />
                          <Text style={styles.verifyButtonText}>
                            Verify Document
                          </Text>
                        </>
                      )}
                    </TouchableOpacity>
                  )}
                </View>
              )}

              {/* Actions */}
              <View style={styles.actionsContainer}>
                {!submitted ? (
                  <TouchableOpacity
                    style={styles.submitButton}
                    onPress={() => handleSubmitDocument(docType)}>
                    <Icon name="check" size={16} color="#FFF" />
                    <Text style={styles.submitButtonText}>
                      Mark as Submitted
                    </Text>
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity
                    style={styles.deleteButton}
                    onPress={() => doc && handleDelete(doc)}>
                    <Icon name="delete-outline" size={16} color="#F44336" />
                    <Text style={styles.deleteButtonText}>Remove Entry</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          );
        })}

        {/* Footer Info */}
        <View style={styles.footer}>
          <Icon name="lock" size={20} color="#4CAF50" />
          <Text style={styles.footerText}>
            <Text style={styles.footerBold}>Secure & Private:</Text> No
            document files are stored online. Physical storage reduces data
            breach risk by 99%.
          </Text>
        </View>
      </ScrollView>

      {/* Storage Location Modal */}
      <Modal
        visible={modalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Physical Storage Location</Text>
            <Text style={styles.modalSubtitle}>
              Where will this {selectedDocType?.label} be stored?
            </Text>

            <TextInput
              style={styles.input}
              placeholder="e.g., Filing Cabinet A, Drawer 2, Folder 15"
              value={storageLocation}
              onChangeText={setStorageLocation}
              autoFocus
              multiline
            />

            <Text style={styles.modalHelp}>
              💡 Tip: Be specific so you can find it easily later
            </Text>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => {
                  setModalVisible(false);
                  setStorageLocation('');
                  setSelectedDocType(null);
                }}>
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, styles.confirmButton]}
                onPress={confirmSubmit}
                disabled={submitting}>
                {submitting ? (
                  <ActivityIndicator size="small" color="#FFF" />
                ) : (
                  <Text style={styles.confirmButtonText}>Confirm</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

// ============= STYLES =============

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#757575',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#F5F5F5',
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    color: '#212121',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    backgroundColor: '#2196F3',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  header: {
    backgroundColor: '#FFF',
    padding: 24,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#212121',
    marginTop: 12,
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#757575',
    marginTop: 4,
  },
  infoBanner: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    margin: 16,
    padding: 16,
    borderRadius: 8,
    alignItems: 'flex-start',
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#1976D2',
    marginLeft: 12,
    lineHeight: 18,
  },
  infoBold: {
    fontWeight: 'bold',
  },
  card: {
    backgroundColor: '#FFF',
    margin: 16,
    marginTop: 8,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  cardTitleContainer: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#212121',
  },
  cardDescription: {
    fontSize: 11,
    color: '#757575',
    marginTop: 2,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  statusBadgePending: {
    backgroundColor: '#FFF3E0',
  },
  statusText: {
    fontSize: 12,
    color: '#4CAF50',
    marginLeft: 4,
    fontWeight: '500',
  },
  statusTextPending: {
    color: '#FF9800',
  },
  dateText: {
    fontSize: 11,
    color: '#757575',
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    paddingVertical: 4,
  },
  locationText: {
    fontSize: 11,
    color: '#757575',
    marginLeft: 4,
    flex: 1,
  },
  verificationContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#EEE',
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  verifiedText: {
    fontSize: 12,
    color: '#4CAF50',
    marginLeft: 4,
    fontWeight: '500',
  },
  verifiedDate: {
    fontSize: 11,
    color: '#757575',
  },
  verifyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
  },
  verifyButtonText: {
    fontSize: 13,
    color: '#2196F3',
    marginLeft: 4,
    fontWeight: '500',
  },
  actionsContainer: {
    marginTop: 12,
  },
  submitButton: {
    flexDirection: 'row',
    backgroundColor: '#2196F3',
    paddingVertical: 10,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  deleteButton: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: '#F44336',
    paddingVertical: 10,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteButtonText: {
    color: '#F44336',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  footer: {
    flexDirection: 'row',
    backgroundColor: '#E8F5E9',
    margin: 16,
    marginTop: 8,
    padding: 16,
    borderRadius: 8,
    alignItems: 'flex-start',
  },
  footerText: {
    flex: 1,
    fontSize: 13,
    color: '#2E7D32',
    marginLeft: 12,
    lineHeight: 18,
  },
  footerBold: {
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 24,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212121',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 13,
    color: '#757575',
    marginBottom: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  modalHelp: {
    fontSize: 12,
    color: '#757575',
    marginTop: 8,
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#F5F5F5',
    marginRight: 8,
  },
  confirmButton: {
    backgroundColor: '#2196F3',
    marginLeft: 8,
  },
  cancelButtonText: {
    color: '#757575',
    fontWeight: '600',
  },
  confirmButtonText: {
    color: '#FFF',
    fontWeight: '600',
  },
});

export default PhysicalDocumentsScreen;







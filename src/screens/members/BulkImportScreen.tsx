import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {usersService} from '../../services/usersService';
import ENV from '../../config/env';
import {Linking} from 'react-native';

const BulkImportScreen = ({navigation}: any) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [selectedFile, setSelectedFile] = useState<any>(null);

  const handleDownloadTemplate = async () => {
    try {
      const baseURL = ENV.API_URL || 'http://localhost:8000';
      const url = `${baseURL}/member-onboarding/bulk-import/template`;
      await Linking.openURL(url);
      Alert.alert(
        'Template Download',
        'CSV template download started. Check your downloads folder.',
        [{text: 'OK'}]
      );
    } catch (error) {
      console.error('Error downloading template:', error);
      Alert.alert('Error', 'Failed to download template. Please try again.');
    }
  };

  const handleFileSelect = (event: any) => {
    const file = event.target.files[0];
    if (file) {
      // Check file type
      const validTypes = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      ];
      
      if (!validTypes.includes(file.type) && !file.name.match(/\.(csv|xlsx|xls)$/i)) {
        Alert.alert('Invalid File', 'Please select a CSV or Excel file');
        return;
      }

      setSelectedFile(file);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      Alert.alert('No File Selected', 'Please select a CSV or Excel file first');
      return;
    }

    setUploading(true);
    setProgress(10);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      setProgress(30);

      const response = await usersService.bulkImportMembers(formData);

      setProgress(100);
      setResult(response);

      if (response.successful > 0) {
        Alert.alert(
          'Import Complete',
          `Successfully imported ${response.successful} out of ${response.total_rows} members.${
            response.failed > 0 ? `\n\n${response.failed} rows failed.` : ''
          }`,
          [{text: 'OK'}]
        );
      } else {
        Alert.alert(
          'Import Failed',
          'No members were imported. Please check the errors below.',
          [{text: 'OK'}]
        );
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      Alert.alert(
        'Upload Error',
        error?.response?.data?.detail || 'Failed to upload file. Please try again.'
      );
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const renderInstructions = () => (
    <View style={styles.instructionsCard}>
      <View style={styles.instructionHeader}>
        <Icon name="information-circle" size={24} color="#007AFF" />
        <Text style={styles.instructionTitle}>Import Instructions</Text>
      </View>

      <Text style={styles.instructionStep}>
        <Text style={styles.stepNumber}>1.</Text> Download the CSV template below
      </Text>
      <Text style={styles.instructionStep}>
        <Text style={styles.stepNumber}>2.</Text> Fill in member details (one member per
        row)
      </Text>
      <Text style={styles.instructionStep}>
        <Text style={styles.stepNumber}>3.</Text> Ensure all flats exist in the system
      </Text>
      <Text style={styles.instructionStep}>
        <Text style={styles.stepNumber}>4.</Text> Phone numbers must be unique
      </Text>
      <Text style={styles.instructionStep}>
        <Text style={styles.stepNumber}>5.</Text> Use format: YYYY-MM-DD for dates
      </Text>

      <View style={styles.requiredFields}>
        <Text style={styles.requiredTitle}>Required Fields:</Text>
        <Text style={styles.requiredText}>
          • flat_number, name, phone_number, email
        </Text>
        <Text style={styles.requiredText}>
          • member_type (owner/tenant), move_in_date
        </Text>
      </View>

      <View style={styles.legalNotice}>
        <Icon name="shield-checkmark" size={16} color="#28a745" />
        <Text style={styles.legalText}>
          Legal Compliance: Only primary member info is collected. NO Aadhaar/PAN data.
        </Text>
      </View>
    </View>
  );

  const renderUploadSection = () => (
    <View style={styles.uploadCard}>
      <Text style={styles.cardTitle}>Upload Member Data</Text>

      {/* File Input */}
      <View style={styles.fileInputContainer}>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileSelect}
          style={styles.hiddenInput}
          id="file-input"
        />
        <label htmlFor="file-input" style={styles.fileInputLabel as any}>
          <View style={styles.fileInputButton}>
            <Icon name="document-attach" size={24} color="#007AFF" />
            <Text style={styles.fileInputText}>
              {selectedFile ? selectedFile.name : 'Choose CSV or Excel file'}
            </Text>
          </View>
        </label>
      </View>

      {selectedFile && (
        <View style={styles.selectedFileInfo}>
          <Icon name="checkmark-circle" size={20} color="#28a745" />
          <Text style={styles.selectedFileName}>{selectedFile.name}</Text>
          <Text style={styles.selectedFileSize}>
            {(selectedFile.size / 1024).toFixed(2)} KB
          </Text>
        </View>
      )}

      {/* Upload Button */}
      {selectedFile && !result && (
        <TouchableOpacity
          style={[styles.uploadButton, uploading && styles.uploadButtonDisabled]}
          onPress={handleUpload}
          disabled={uploading}
          activeOpacity={0.7}>
          {uploading ? (
            <>
              <ActivityIndicator size="small" color="#FFF" />
              <Text style={styles.uploadButtonText}>Uploading... {progress}%</Text>
            </>
          ) : (
            <>
              <Icon name="cloud-upload" size={24} color="#FFF" />
              <Text style={styles.uploadButtonText}>Upload & Import</Text>
            </>
          )}
        </TouchableOpacity>
      )}

      {/* Progress Bar */}
      {uploading && (
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, {width: `${progress}%`}]} />
          </View>
          <Text style={styles.progressText}>{progress}%</Text>
        </View>
      )}
    </View>
  );

  const renderResults = () => {
    if (!result) return null;

    return (
      <View style={styles.resultsCard}>
        <View style={styles.resultHeader}>
          <Icon
            name={result.successful > 0 ? 'checkmark-circle' : 'alert-circle'}
            size={32}
            color={result.successful > 0 ? '#28a745' : '#dc3545'}
          />
          <Text style={styles.resultTitle}>Import Results</Text>
        </View>

        {/* Summary Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.statBox}>
            <Text style={styles.statValue}>{result.total_rows}</Text>
            <Text style={styles.statLabel}>Total Rows</Text>
          </View>
          <View style={[styles.statBox, styles.successBox]}>
            <Text style={[styles.statValue, {color: '#28a745'}]}>
              {result.successful}
            </Text>
            <Text style={styles.statLabel}>Successful</Text>
          </View>
          <View style={[styles.statBox, styles.errorBox]}>
            <Text style={[styles.statValue, {color: '#dc3545'}]}>{result.failed}</Text>
            <Text style={styles.statLabel}>Failed</Text>
          </View>
          {result.warnings && result.warnings.length > 0 && (
            <View style={[styles.statBox, styles.warningBox]}>
              <Text style={[styles.statValue, {color: '#ffc107'}]}>
                {result.warnings.length}
              </Text>
              <Text style={styles.statLabel}>Warnings</Text>
            </View>
          )}
        </View>

        {/* Errors Section */}
        {result.errors && result.errors.length > 0 && (
          <View style={styles.errorsSection}>
            <Text style={styles.errorsSectionTitle}>
              Errors ({result.errors.length}):
            </Text>
            <ScrollView style={styles.errorsList} nestedScrollEnabled>
              {result.errors.map((error: string, index: number) => (
                <View key={index} style={styles.errorItem}>
                  <Icon name="close-circle" size={16} color="#dc3545" />
                  <Text style={styles.errorText}>{error}</Text>
                </View>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Warnings Section */}
        {result.warnings && result.warnings.length > 0 && (
          <View style={styles.warningsSection}>
            <Text style={styles.warningsSectionTitle}>
              Warnings ({result.warnings.length}):
            </Text>
            <ScrollView style={styles.warningsList} nestedScrollEnabled>
              {result.warnings.map((warning: string, index: number) => (
                <View key={index} style={styles.warningItem}>
                  <Icon name="warning" size={16} color="#ffc107" />
                  <Text style={styles.warningText}>{warning}</Text>
                </View>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={styles.importAnotherButton}
            onPress={() => {
              setSelectedFile(null);
              setResult(null);
              setProgress(0);
            }}
            activeOpacity={0.7}>
            <Icon name="add-circle-outline" size={20} color="#007AFF" />
            <Text style={styles.importAnotherText}>Import Another File</Text>
          </TouchableOpacity>

          {result.successful > 0 && (
            <TouchableOpacity
              style={styles.viewMembersButton}
              onPress={() => navigation.goBack()}
              activeOpacity={0.7}>
              <Icon name="people" size={20} color="#FFF" />
              <Text style={styles.viewMembersText}>View Members</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Bulk Member Import</Text>
        <Text style={styles.headerSubtitle}>
          Import multiple members at once using CSV or Excel file
        </Text>
      </View>

      {/* Download Template Button */}
      <TouchableOpacity
        style={styles.downloadTemplateButton}
        onPress={handleDownloadTemplate}
        activeOpacity={0.7}>
        <Icon name="download" size={24} color="#FFF" />
        <Text style={styles.downloadTemplateText}>Download CSV Template</Text>
      </TouchableOpacity>

      {/* Instructions */}
      {renderInstructions()}

      {/* Upload Section */}
      {renderUploadSection()}

      {/* Results */}
      {renderResults()}

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#FFF',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  downloadTemplateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#28a745',
    marginHorizontal: 16,
    marginVertical: 16,
    paddingVertical: 14,
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  downloadTemplateText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  instructionsCard: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  instructionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  instructionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 8,
  },
  instructionStep: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    paddingLeft: 8,
  },
  stepNumber: {
    fontWeight: 'bold',
    color: '#007AFF',
  },
  requiredFields: {
    backgroundColor: '#F8F9FA',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
    marginBottom: 12,
  },
  requiredTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 6,
  },
  requiredText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  legalNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    padding: 10,
    borderRadius: 8,
  },
  legalText: {
    fontSize: 11,
    color: '#28a745',
    marginLeft: 6,
    flex: 1,
  },
  uploadCard: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  fileInputContainer: {
    marginBottom: 16,
  },
  hiddenInput: {
    display: 'none',
  } as any,
  fileInputLabel: {
    cursor: 'pointer',
  },
  fileInputButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F0F8FF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
  },
  fileInputText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  selectedFileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  selectedFileName: {
    flex: 1,
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#28a745',
  },
  selectedFileSize: {
    fontSize: 12,
    color: '#666',
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  uploadButtonDisabled: {
    backgroundColor: '#CCC',
    opacity: 0.6,
  },
  uploadButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  progressContainer: {
    marginTop: 16,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
  },
  progressText: {
    textAlign: 'center',
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  resultsCard: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 12,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  statBox: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#F8F9FA',
    padding: 12,
    borderRadius: 8,
    margin: 4,
    alignItems: 'center',
  },
  successBox: {
    backgroundColor: '#E8F5E9',
  },
  errorBox: {
    backgroundColor: '#FFEBEE',
  },
  warningBox: {
    backgroundColor: '#FFF8E1',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  errorsSection: {
    marginTop: 16,
    marginBottom: 16,
  },
  errorsSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#dc3545',
    marginBottom: 8,
  },
  errorsList: {
    maxHeight: 200,
    backgroundColor: '#FFEBEE',
    borderRadius: 8,
    padding: 12,
  },
  errorItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  errorText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 13,
    color: '#dc3545',
  },
  warningsSection: {
    marginBottom: 16,
  },
  warningsSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffc107',
    marginBottom: 8,
  },
  warningsList: {
    maxHeight: 150,
    backgroundColor: '#FFF8E1',
    borderRadius: 8,
    padding: 12,
  },
  warningItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  warningText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 13,
    color: '#856404',
  },
  actionButtons: {
    flexDirection: 'row',
    marginTop: 16,
  },
  importAnotherButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFF',
    paddingVertical: 12,
    borderRadius: 8,
    marginRight: 8,
    borderWidth: 2,
    borderColor: '#007AFF',
  },
  importAnotherText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  viewMembersButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#28a745',
    paddingVertical: 12,
    borderRadius: 8,
  },
  viewMembersText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  bottomSpacer: {
    height: 20,
  },
});

export default BulkImportScreen;


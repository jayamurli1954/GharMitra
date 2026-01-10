import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Modal,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {
  adminGuidelinesService,
  AdminGuidelinesResponse,
  AdminAcknowledgmentResponse,
  AdminGuidelinesSection,
} from '../../services/adminGuidelinesService';

const AdminGuidelinesScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(true);
  const [acknowledging, setAcknowledging] = useState(false);
  const [guidelines, setGuidelines] = useState<AdminGuidelinesResponse | null>(null);
  const [acknowledgmentStatus, setAcknowledgmentStatus] =
    useState<AdminAcknowledgmentResponse | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [guidelinesData, ackStatus] = await Promise.all([
        adminGuidelinesService.getGuidelines(),
        adminGuidelinesService.getAcknowledgmentStatus(),
      ]);
      setGuidelines(guidelinesData);
      setAcknowledgmentStatus(ackStatus);
    } catch (error: any) {
      console.error('Error loading guidelines:', error);
      Alert.alert('Error', 'Failed to load admin guidelines');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async () => {
    if (!guidelines) return;

    Alert.alert(
      'Acknowledge Guidelines',
      'I confirm that I have read and understood the Admin Guidelines and agree to follow them.',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'I Agree',
          onPress: async () => {
            setAcknowledging(true);
            try {
              const response = await adminGuidelinesService.acknowledgeGuidelines(
                guidelines.version
              );
              setAcknowledgmentStatus(response);
              Alert.alert('Success', 'Guidelines acknowledged successfully');
            } catch (error: any) {
              console.error('Error acknowledging guidelines:', error);
              Alert.alert(
                'Error',
                error.response?.data?.detail || 'Failed to acknowledge guidelines'
              );
            } finally {
              setAcknowledging(false);
            }
          },
        },
      ]
    );
  };

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading guidelines...</Text>
      </View>
    );
  }

  if (!guidelines) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="alert-circle" size={48} color="#FF3B30" />
        <Text style={styles.errorText}>Failed to load guidelines</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadData}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const content = guidelines.content;
  const isAcknowledged = acknowledgmentStatus?.acknowledged || false;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          activeOpacity={0.7}>
          <Icon name="arrow-back" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Admin Guidelines</Text>
        <View style={styles.backButton} />
      </View>

      {/* Acknowledgment Status Banner */}
      {isAcknowledged ? (
        <View style={styles.acknowledgedBanner}>
          <Icon name="checkmark-circle" size={24} color="#34C759" />
          <View style={styles.acknowledgedTextContainer}>
            <Text style={styles.acknowledgedText}>Guidelines Acknowledged</Text>
            {acknowledgmentStatus?.acknowledged_at && (
              <Text style={styles.acknowledgedDate}>
                On:{' '}
                {new Date(acknowledgmentStatus.acknowledged_at).toLocaleDateString()}
              </Text>
            )}
          </View>
        </View>
      ) : (
        <View style={styles.notAcknowledgedBanner}>
          <Icon name="warning" size={24} color="#FF9500" />
          <View style={styles.notAcknowledgedTextContainer}>
            <Text style={styles.notAcknowledgedText}>
              Please read and acknowledge the guidelines
            </Text>
          </View>
        </View>
      )}

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Title and Version */}
        <View style={styles.titleContainer}>
          <Text style={styles.title}>{content.title}</Text>
          <View style={styles.versionContainer}>
            <Text style={styles.versionText}>Version {guidelines.version}</Text>
            <Text style={styles.lastUpdatedText}>
              Last Updated: {guidelines.last_updated}
            </Text>
          </View>
        </View>

        {/* Guidelines Sections */}
        {content.sections.map((section: AdminGuidelinesSection) => {
          const isExpanded = expandedSections.has(section.id);
          return (
            <View key={section.id} style={styles.sectionCard}>
              <TouchableOpacity
                style={styles.sectionHeader}
                onPress={() => toggleSection(section.id)}
                activeOpacity={0.7}>
                <View style={styles.sectionHeaderLeft}>
                  <Icon name={section.icon} size={24} color="#007AFF" />
                  <Text style={styles.sectionTitle}>{section.title}</Text>
                </View>
                <Icon
                  name={isExpanded ? 'chevron-up' : 'chevron-down'}
                  size={24}
                  color="#8E8E93"
                />
              </TouchableOpacity>

              {isExpanded && (
                <View style={styles.sectionContent}>
                  {/* Do's */}
                  <View style={styles.dosContainer}>
                    <Text style={styles.dosTitle}>Do's:</Text>
                    {section.dos.map((item, index) => (
                      <View key={index} style={styles.listItem}>
                        <Text style={styles.listItemText}>{item}</Text>
                      </View>
                    ))}
                  </View>

                  {/* Don'ts */}
                  <View style={styles.dontsContainer}>
                    <Text style={styles.dontsTitle}>Don'ts:</Text>
                    {section.donts.map((item, index) => (
                      <View key={index} style={styles.listItem}>
                        <Text style={styles.listItemText}>{item}</Text>
                      </View>
                    ))}
                  </View>

                  {/* Important Note */}
                  {section.important && (
                    <View style={styles.importantContainer}>
                      <Icon name="information-circle" size={20} color="#007AFF" />
                      <Text style={styles.importantText}>{section.important}</Text>
                    </View>
                  )}
                </View>
              )}
            </View>
          );
        })}

        {/* Acknowledgment Button */}
        {!isAcknowledged && (
          <View style={styles.acknowledgeContainer}>
            <TouchableOpacity
              style={styles.acknowledgeButton}
              onPress={handleAcknowledge}
              disabled={acknowledging}
              activeOpacity={0.7}>
              {acknowledging ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <>
                  <Icon name="checkmark-circle" size={24} color="#FFF" />
                  <Text style={styles.acknowledgeButtonText}>
                    {content.acknowledgment_message}
                  </Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
    padding: 20,
  },
  errorText: {
    marginTop: 12,
    fontSize: 16,
    color: '#FF3B30',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 20,
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  acknowledgedBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#C8E6C9',
  },
  acknowledgedTextContainer: {
    marginLeft: 12,
    flex: 1,
  },
  acknowledgedText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2E7D32',
  },
  acknowledgedDate: {
    fontSize: 14,
    color: '#4CAF50',
    marginTop: 4,
  },
  notAcknowledgedBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3E0',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#FFE0B2',
  },
  notAcknowledgedTextContainer: {
    marginLeft: 12,
    flex: 1,
  },
  notAcknowledgedText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#E65100',
  },
  scrollView: {
    flex: 1,
  },
  titleContainer: {
    backgroundColor: '#FFF',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1D1D1F',
    marginBottom: 12,
  },
  versionContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  versionText: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500',
  },
  lastUpdatedText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  sectionCard: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginLeft: 12,
    flex: 1,
  },
  sectionContent: {
    padding: 16,
    paddingTop: 0,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  dosContainer: {
    marginBottom: 16,
  },
  dosTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#34C759',
    marginBottom: 8,
  },
  dontsContainer: {
    marginBottom: 16,
  },
  dontsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF3B30',
    marginBottom: 8,
  },
  listItem: {
    marginBottom: 8,
    paddingLeft: 8,
  },
  listItemText: {
    fontSize: 15,
    color: '#1D1D1F',
    lineHeight: 22,
  },
  importantContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  importantText: {
    fontSize: 14,
    color: '#1976D2',
    marginLeft: 8,
    flex: 1,
    lineHeight: 20,
  },
  acknowledgeContainer: {
    padding: 16,
    marginTop: 24,
  },
  acknowledgeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  acknowledgeButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  bottomSpacer: {
    height: 32,
  },
});

export default AdminGuidelinesScreen;


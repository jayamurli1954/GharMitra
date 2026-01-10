import React, {useState, useEffect} from 'react';
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
import DateTimePicker from '@react-native-community/datetimepicker';
import {accountingService} from '../../services/accountingService';

const JournalEntryReportScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(false);
  const [fromDate, setFromDate] = useState<Date | null>(null);
  const [toDate, setToDate] = useState<Date | null>(null);
  const [showFromDatePicker, setShowFromDatePicker] = useState(false);
  const [showToDatePicker, setShowToDatePicker] = useState(false);
  const [entries, setEntries] = useState<any[]>([]);
  const [expandedEntry, setExpandedEntry] = useState<string | null>(null);

  useEffect(() => {
    loadEntries();
  }, []);

  const formatDate = (date: Date | null) => {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const loadEntries = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (fromDate) params.from_date = formatDate(fromDate);
      if (toDate) params.to_date = formatDate(toDate);
      
      const data = await accountingService.getJournalEntries(params);
      setEntries(data);
    } catch (error: any) {
      console.error('Error loading journal entries:', error);
      Alert.alert(
        'Error',
        error?.response?.data?.detail || 'Failed to load journal entries. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleEntry = (entryId: string) => {
    setExpandedEntry(expandedEntry === entryId ? null : entryId);
  };

  return (
    <View style={styles.container}>
      {/* Date Range Selector */}
      <View style={styles.dateSelector}>
        <View style={styles.dateRow}>
          <Text style={styles.dateLabel}>From Date (Optional):</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowFromDatePicker(true)}
            activeOpacity={0.7}>
            <Icon name="calendar-outline" size={20} color="#007AFF" />
            <Text style={styles.dateText}>
              {fromDate ? formatDate(fromDate) : 'All Time'}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.dateRow}>
          <Text style={styles.dateLabel}>To Date (Optional):</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowToDatePicker(true)}
            activeOpacity={0.7}>
            <Icon name="calendar-outline" size={20} color="#007AFF" />
            <Text style={styles.dateText}>
              {toDate ? formatDate(toDate) : 'All Time'}
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.generateButton}
          onPress={loadEntries}
          disabled={loading}
          activeOpacity={0.7}>
          {loading ? (
            <ActivityIndicator size="small" color="#FFF" />
          ) : (
            <>
              <Icon name="refresh" size={20} color="#FFF" />
              <Text style={styles.generateButtonText}>Refresh</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Date Pickers */}
      {showFromDatePicker && (
        <DateTimePicker
          value={fromDate || new Date()}
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowFromDatePicker(false);
            if (selectedDate) {
              setFromDate(selectedDate);
            }
          }}
        />
      )}

      {showToDatePicker && (
        <DateTimePicker
          value={toDate || new Date()}
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowToDatePicker(false);
            if (selectedDate) {
              setToDate(selectedDate);
            }
          }}
        />
      )}

      {/* Create New Button */}
      <TouchableOpacity
        style={styles.createButton}
        onPress={() => navigation.navigate('JournalEntry')}
        activeOpacity={0.7}>
        <Icon name="add-circle" size={24} color="#FFF" />
        <Text style={styles.createButtonText}>Create New Journal Entry</Text>
      </TouchableOpacity>

      {/* Entries List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading journal entries...</Text>
        </View>
      ) : entries.length > 0 ? (
        <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
          <View style={styles.reportHeader}>
            <Text style={styles.reportTitle}>Journal Entries</Text>
            {(fromDate || toDate) && (
              <Text style={styles.periodText}>
                Period: {fromDate ? formatDate(fromDate) : 'All'} to{' '}
                {toDate ? formatDate(toDate) : 'All'}
              </Text>
            )}
            <Text style={styles.countText}>{entries.length} entries found</Text>
          </View>

          {entries.map((entry: any) => {
            const isExpanded = expandedEntry === entry._id;
            const entryDate = new Date(entry.date).toLocaleDateString('en-IN');
            
            return (
              <View key={entry._id} style={styles.entryCard}>
                <TouchableOpacity
                  style={styles.entryHeader}
                  onPress={() => toggleEntry(entry._id)}
                  activeOpacity={0.7}>
                  <View style={styles.entryHeaderLeft}>
                    <View style={styles.entryNumberBadge}>
                      <Text style={styles.entryNumberText}>{entry.entry_number}</Text>
                    </View>
                    <View style={styles.entryHeaderInfo}>
                      <Text style={styles.entryDate}>{entryDate}</Text>
                      <Text style={styles.entryDescription} numberOfLines={2}>
                        {entry.description}
                      </Text>
                    </View>
                  </View>
                  <Icon
                    name={isExpanded ? 'chevron-up' : 'chevron-down'}
                    size={24}
                    color="#666"
                  />
                </TouchableOpacity>

                {/* Entry Summary */}
                <View style={styles.entrySummary}>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Total Debit</Text>
                    <Text style={[styles.summaryValue, {color: '#28a745'}]}>
                      {formatCurrency(entry.total_debit)}
                    </Text>
                  </View>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Total Credit</Text>
                    <Text style={[styles.summaryValue, {color: '#dc3545'}]}>
                      {formatCurrency(entry.total_credit)}
                    </Text>
                  </View>
                  {entry.is_balanced && (
                    <View style={styles.balancedBadge}>
                      <Icon name="checkmark-circle" size={16} color="#28a745" />
                      <Text style={styles.balancedText}>Balanced</Text>
                    </View>
                  )}
                </View>

                {/* Expanded Details */}
                {isExpanded && (
                  <View style={styles.entryDetails}>
                    <Text style={styles.detailsTitle}>Entry Lines:</Text>
                    
                    {entry.entries && entry.entries.length > 0 ? (
                      entry.entries.map((line: any, index: number) => (
                        <View key={index} style={styles.lineRow}>
                          <View style={styles.lineInfo}>
                            <Text style={styles.lineAccount}>
                              {line.account_code} - {line.account_name || 'Unknown Account'}
                            </Text>
                            {line.description && (
                              <Text style={styles.lineDescription}>{line.description}</Text>
                            )}
                          </View>
                          <View style={styles.lineAmounts}>
                            {line.debit_amount > 0 ? (
                              <Text style={[styles.lineAmount, {color: '#28a745'}]}>
                                Dr {formatCurrency(line.debit_amount)}
                              </Text>
                            ) : (
                              <Text style={[styles.lineAmount, {color: '#dc3545'}]}>
                                Cr {formatCurrency(line.credit_amount)}
                              </Text>
                            )}
                          </View>
                        </View>
                      ))
                    ) : (
                      <Text style={styles.noLinesText}>No entry lines available</Text>
                    )}

                    <View style={styles.metaInfo}>
                      <Text style={styles.metaText}>
                        Created: {new Date(entry.created_at).toLocaleString('en-IN')}
                      </Text>
                      <Text style={styles.metaText}>By: {entry.added_by}</Text>
                    </View>
                  </View>
                )}
              </View>
            );
          })}

          <View style={styles.bottomSpacer} />
        </ScrollView>
      ) : (
        <View style={styles.emptyState}>
          <Icon name="document-text-outline" size={60} color="#CCC" />
          <Text style={styles.emptyText}>No Journal Entries Found</Text>
          <Text style={styles.emptySubtext}>
            Create your first journal entry to get started
          </Text>
          <TouchableOpacity
            style={styles.emptyButton}
            onPress={() => navigation.navigate('JournalEntry')}
            activeOpacity={0.7}>
            <Text style={styles.emptyButtonText}>Create Journal Entry</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  dateSelector: {
    backgroundColor: '#FFF',
    padding: 16,
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  dateLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F8FF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#007AFF',
    flex: 2,
  },
  dateText: {
    marginLeft: 8,
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '500',
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  generateButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#28a745',
    marginHorizontal: 16,
    marginVertical: 12,
    paddingVertical: 14,
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  createButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  scrollView: {
    flex: 1,
  },
  reportHeader: {
    backgroundColor: '#FFF',
    padding: 16,
    marginBottom: 8,
    alignItems: 'center',
  },
  reportTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  periodText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  countText: {
    fontSize: 12,
    color: '#999',
  },
  entryCard: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 3,
    overflow: 'hidden',
  },
  entryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  entryHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  entryNumberBadge: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 12,
  },
  entryNumberText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  entryHeaderInfo: {
    flex: 1,
  },
  entryDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  entryDescription: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  entrySummary: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  summaryItem: {
    flex: 1,
  },
  summaryLabel: {
    fontSize: 11,
    color: '#999',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  balancedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  balancedText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#28a745',
    marginLeft: 4,
  },
  entryDetails: {
    padding: 16,
    backgroundColor: '#F8F9FA',
  },
  detailsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  lineRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E9ECEF',
  },
  lineInfo: {
    flex: 1,
    marginRight: 8,
  },
  lineAccount: {
    fontSize: 13,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  lineDescription: {
    fontSize: 11,
    color: '#666',
  },
  lineAmounts: {
    alignItems: 'flex-end',
  },
  lineAmount: {
    fontSize: 13,
    fontWeight: 'bold',
  },
  noLinesText: {
    fontSize: 13,
    color: '#999',
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: 12,
  },
  metaInfo: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E9ECEF',
  },
  metaText: {
    fontSize: 11,
    color: '#999',
    marginBottom: 4,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#999',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#BBB',
    marginTop: 8,
    textAlign: 'center',
  },
  emptyButton: {
    backgroundColor: '#28a745',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
  },
  emptyButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  bottomSpacer: {
    height: 20,
  },
});

export default JournalEntryReportScreen;



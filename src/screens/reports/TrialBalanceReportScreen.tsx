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
import DateTimePicker from '@react-native-community/datetimepicker';
import {reportsService} from '../../services/reportsService';

const TrialBalanceReportScreen = ({navigation}: any) => {
  const [asOnDate, setAsOnDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<any>(null);

  const loadReport = async () => {
    setLoading(true);
    try {
      const data = await reportsService.getTrialBalance(
        asOnDate.toISOString().split('T')[0]
      );
      setReportData(data);
    } catch (error: any) {
      console.error('Error loading trial balance:', error);
      Alert.alert('Error', error.message || 'Failed to load trial balance');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toFixed(2)}`;
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Trial Balance</Text>
        <Text style={styles.headerSubtitle}>
          All account balances as on selected date
        </Text>
      </View>

      <View style={styles.content}>
        <View style={styles.dateSelector}>
          <Text style={styles.label}>As On Date:</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowDatePicker(true)}>
            <Icon name="calendar" size={20} color="#007AFF" />
            <Text style={styles.dateText}>
              {asOnDate.toLocaleDateString()}
            </Text>
          </TouchableOpacity>
        </View>

        {showDatePicker && (
          <DateTimePicker
            value={asOnDate}
            mode="date"
            display="default"
            onChange={(event, selectedDate) => {
              setShowDatePicker(false);
              if (selectedDate) setAsOnDate(selectedDate);
            }}
          />
        )}

        <TouchableOpacity
          style={styles.generateButton}
          onPress={loadReport}
          disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Icon name="refresh" size={20} color="#FFF" />
              <Text style={styles.generateButtonText}>Generate Report</Text>
            </>
          )}
        </TouchableOpacity>

        {reportData && (
          <View style={styles.reportContainer}>
            <View style={styles.summaryBox}>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Total Debit:</Text>
                <Text style={styles.summaryValue}>
                  {formatCurrency(reportData.total_debit)}
                </Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Total Credit:</Text>
                <Text style={styles.summaryValue}>
                  {formatCurrency(reportData.total_credit)}
                </Text>
              </View>
              <View
                style={[
                  styles.summaryRow,
                  {
                    backgroundColor: reportData.is_balanced
                      ? '#E8F5E9'
                      : '#FFEBEE',
                  },
                ]}>
                <Text style={styles.summaryLabel}>Difference:</Text>
                <Text
                  style={[
                    styles.summaryValue,
                    {
                      color: reportData.is_balanced ? '#4CAF50' : '#F44336',
                      fontWeight: 'bold',
                    },
                  ]}>
                  {formatCurrency(reportData.difference)}
                </Text>
              </View>
              <View style={styles.balanceStatus}>
                <Icon
                  name={reportData.is_balanced ? 'checkmark-circle' : 'close-circle'}
                  size={24}
                  color={reportData.is_balanced ? '#4CAF50' : '#F44336'}
                />
                <Text
                  style={[
                    styles.balanceText,
                    {
                      color: reportData.is_balanced ? '#4CAF50' : '#F44336',
                    },
                  ]}>
                  {reportData.is_balanced ? 'BALANCED' : 'NOT BALANCED'}
                </Text>
              </View>
            </View>

            <View style={styles.tableHeader}>
              <Text style={[styles.tableHeaderText, {flex: 2}]}>
                Account
              </Text>
              <Text style={[styles.tableHeaderText, {flex: 1}]}>Debit</Text>
              <Text style={[styles.tableHeaderText, {flex: 1}]}>Credit</Text>
            </View>

            {reportData.items.map((item: any, index: number) => (
              <View key={index} style={styles.tableRow}>
                <View style={styles.accountCell}>
                  <Text style={styles.accountCode}>{item.account_code}</Text>
                  <Text style={styles.accountName}>{item.account_name}</Text>
                </View>
                <Text style={[styles.amountCell, {flex: 1}]}>
                  {item.debit_balance > 0
                    ? formatCurrency(item.debit_balance)
                    : '-'}
                </Text>
                <Text style={[styles.amountCell, {flex: 1}]}>
                  {item.credit_balance > 0
                    ? formatCurrency(item.credit_balance)
                    : '-'}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFF',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginTop: 5,
  },
  content: {
    padding: 15,
  },
  dateSelector: {
    marginBottom: 15,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#DDD',
  },
  dateText: {
    marginLeft: 10,
    fontSize: 16,
    color: '#333',
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
  },
  generateButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  reportContainer: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 15,
    marginTop: 10,
  },
  summaryBox: {
    backgroundColor: '#F9F9F9',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
  },
  summaryLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
  },
  summaryValue: {
    fontSize: 15,
    color: '#333',
  },
  balanceStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
    padding: 10,
  },
  balanceText: {
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#007AFF',
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
  },
  tableHeaderText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
  tableRow: {
    flexDirection: 'row',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
  },
  accountCell: {
    flex: 2,
  },
  accountCode: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  accountName: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  amountCell: {
    fontSize: 14,
    color: '#333',
    textAlign: 'right',
  },
});

export default TrialBalanceReportScreen;









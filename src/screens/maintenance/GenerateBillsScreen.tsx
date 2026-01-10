import React, {useEffect, useState, useCallback} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {useFocusEffect} from '@react-navigation/native';
import {maintenanceService} from '../../services/maintenanceService';
import {flatsService} from '../../services/flatsService';
import {getCurrentMonth, formatMonthYear, formatCurrency} from '../../utils/maintenanceCalculations';

const GenerateBillsScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [settings, setSettings] = useState<any>(null);
  const [flats, setFlats] = useState<any[]>([]);
  const [waterExpense, setWaterExpense] = useState<any>(null);
  const [fixedExpenses, setFixedExpenses] = useState<any[]>([]);
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth());
  const [allowedMonth, setAllowedMonth] = useState<any>(null);
  const [alreadyGenerated, setAlreadyGenerated] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refresh when screen comes into focus (e.g., after deleting bills)
  useFocusEffect(
    useCallback(() => {
      loadAllowedMonth();
    }, [])
  );

  useEffect(() => {
    loadAllowedMonth();
  }, []);

  useEffect(() => {
    if (allowedMonth) {
      loadData();
    }
  }, [selectedMonth, allowedMonth]);

  const loadAllowedMonth = async () => {
    try {
      const allowed = await maintenanceService.getAllowedBillMonth();
      setAllowedMonth(allowed);
      
      // Auto-select the allowed month
      const allowedMonthStr = `${allowed.allowed_year}-${String(allowed.allowed_month).padStart(2, '0')}`;
      setSelectedMonth(allowedMonthStr);
      setAlreadyGenerated(allowed.already_generated);
    } catch (error: any) {
      console.error('Error loading allowed month:', error);
      // Fallback to current month if API fails
      setAllowedMonth(null);
      setAlreadyGenerated(false);
    }
  };

  const loadData = async () => {
    if (!allowedMonth) {
      await loadAllowedMonth();
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      // Load settings
      const settingsData = await maintenanceService.getSettings();
      if (!settingsData) {
        setError('Settings not configured. Please configure apartment settings first.');
        setLoading(false);
        return;
      }
      setSettings(settingsData);

      // Load flats
      const flatsList = await flatsService.getFlats();
      setFlats(flatsList);

      // Use allowed month instead of selected month
      const year = allowedMonth.allowed_year;
      const month = allowedMonth.allowed_month;

      const existingBills = await maintenanceService.getBills({month, year});
      setAlreadyGenerated(existingBills.length > 0 || allowedMonth.already_generated);

      if (settingsData.calculation_method === 'variable') {
        // Load water expense for this month
        const waterExpenses = await maintenanceService.getWaterExpenses(month, year);
        if (waterExpenses.length > 0) {
          setWaterExpense(waterExpenses[0]);
        } else {
          setWaterExpense(null);
        }

        // Load fixed expenses
        const fixedExpensesList = await maintenanceService.getFixedExpenses();
        setFixedExpenses(fixedExpensesList);
      }
    } catch (error: any) {
      console.error('Error loading data:', error);
      if (error.response?.status === 404) {
        setError('Settings not configured. Please configure apartment settings first.');
      } else {
        setError('Failed to load data. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!settings) {
      Alert.alert('Error', 'Settings not loaded');
      return;
    }

    if (flats.length === 0) {
      Alert.alert('Error', 'Please add flats before generating bills');
      return;
    }

    if (alreadyGenerated) {
      Alert.alert(
        'Bills Already Generated',
        `Bills for ${allowedMonth?.formatted || 'this month'} have already been generated. Bills can only be generated once per month.`,
        [{text: 'OK'}],
      );
      return;
    }

    generateBills(false);
  };

  const generateBills = async (isRegenerate: boolean) => {
    if (!allowedMonth) {
      Alert.alert('Error', 'Allowed month not loaded. Please try again.');
      return;
    }
    
    setGenerating(true);
    try {
      const year = allowedMonth.allowed_year;
      const month = allowedMonth.allowed_month;

      // Delete existing bills if regenerating
      if (isRegenerate) {
        await maintenanceService.deleteBillsForMonth(month, year);
      }

      // Generate bills via backend API
      const result = await maintenanceService.generateBills(month, year);

      Alert.alert(
        'Success',
        `Generated ${result.total_bills_generated} maintenance bills for ${allowedMonth?.formatted || formatMonthYear(selectedMonth)}\nTotal Amount: ${formatCurrency(result.total_amount)}`,
        [
          {
            text: 'View Bills',
            onPress: () => {
              loadData();
              navigation.navigate('BillHistory');
            },
          },
          {
            text: 'OK',
            onPress: () => {
              loadData();
            },
          },
        ],
      );
    } catch (error: any) {
      console.error('Error generating bills:', error);
      const errorMessage =
        error.response?.data?.detail || 'Failed to generate bills. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  if (error && !settings) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="settings-outline" size={60} color="#F44336" />
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity
          style={styles.errorButton}
          onPress={() => navigation.navigate('ApartmentSettings')}
          activeOpacity={0.7}>
          <Text style={styles.errorButtonText}>Go to Settings</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!settings) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="settings-outline" size={60} color="#F44336" />
        <Text style={styles.errorText}>Settings not configured</Text>
        <TouchableOpacity
          style={styles.errorButton}
          onPress={() => navigation.navigate('ApartmentSettings')}
          activeOpacity={0.7}>
          <Text style={styles.errorButtonText}>Go to Settings</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const canGenerate =
    flats.length > 0 &&
    settings &&
    !generating;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Icon name="receipt" size={50} color="#FFF" />
        <Text style={styles.headerTitle}>Generate Bills</Text>
        {allowedMonth && (
          <Text style={styles.headerSubtitle}>
            {allowedMonth.formatted}
          </Text>
        )}
      </View>

      {allowedMonth && (
        <View style={styles.infoBox}>
          <Icon name="information-circle" size={24} color="#007AFF" />
          <View style={styles.infoContent}>
            <Text style={styles.infoTitle}>Bill Generation Month</Text>
            <Text style={styles.infoText}>
              Bills can only be generated for the previous month ({allowedMonth.formatted}).
              This ensures all expenses for that month are accounted for before billing.
              {'\n\n'}
              Current month: {new Date().toLocaleString('default', {month: 'long'})} {allowedMonth.current_year}
            </Text>
          </View>
        </View>
      )}

      <View style={styles.methodCard}>
        <Text style={styles.methodLabel}>Calculation Method</Text>
        <Text style={styles.methodValue}>
          {settings.calculation_method === 'sqft_rate'
            ? 'Square Feet Rate'
            : 'Variable (Water + Fixed)'}
        </Text>
      </View>

      <View style={styles.summarySection}>
        <Text style={styles.sectionTitle}>Summary</Text>

        <View style={styles.summaryItem}>
          <Icon name="home" size={20} color="#666" />
          <Text style={styles.summaryLabel}>Total Flats</Text>
          <Text style={styles.summaryValue}>{flats.length}</Text>
        </View>

        {settings.calculation_method === 'sqft_rate' && (
          <View style={styles.summaryItem}>
            <Icon name="pricetag" size={20} color="#666" />
            <Text style={styles.summaryLabel}>Rate per sq ft</Text>
            <Text style={styles.summaryValue}>
              {formatCurrency(settings.sqft_rate || 0)}
            </Text>
          </View>
        )}

        {settings.calculation_method === 'variable' && (
          <>
            <View style={styles.summaryItem}>
              <Icon name="water" size={20} color="#666" />
              <Text style={styles.summaryLabel}>Water Charges</Text>
              <Text style={styles.summaryValue}>
                From Transactions
              </Text>
            </View>

            <View style={styles.summaryItem}>
              <Icon name="people" size={20} color="#666" />
              <Text style={styles.summaryLabel}>Total Occupants</Text>
              <Text style={styles.summaryValue}>
                {flats.reduce((sum, f) => sum + (f.occupants || 0), 0)}
              </Text>
            </View>

            <View style={styles.summaryItem}>
              <Icon name="cash" size={20} color="#666" />
              <Text style={styles.summaryLabel}>Fixed Expenses</Text>
              <Text style={styles.summaryValue}>{fixedExpenses.length} items</Text>
            </View>
          </>
        )}
      </View>

      {!canGenerate && !generating && (
        <View style={styles.warningBox}>
          <Icon name="warning" size={24} color="#FF9800" />
          <View style={styles.warningContent}>
            <Text style={styles.warningTitle}>Cannot Generate Bills</Text>
            <Text style={styles.warningText}>
              {flats.length === 0
                ? 'Please add flats first'
                : !settings
                ? 'Settings not configured'
                : 'Ready to generate'}
            </Text>
          </View>
        </View>
      )}

      {alreadyGenerated && (
        <View style={styles.infoBox}>
          <Icon name="checkmark-circle" size={24} color="#4CAF50" />
          <View style={styles.infoContent}>
            <Text style={styles.infoTitle}>Bills Already Generated</Text>
            <Text style={styles.infoText}>
              Bills for {allowedMonth?.formatted || formatMonthYear(selectedMonth)} have already been generated.
              {'\n\n'}
              Bills can only be generated once per month.
            </Text>
            <TouchableOpacity
              style={styles.viewBillsButton}
              onPress={() => navigation.navigate('BillHistory')}
              activeOpacity={0.7}>
              <Icon name="receipt" size={18} color="#007AFF" />
              <Text style={styles.viewBillsButtonText}>View Bill History</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <TouchableOpacity
        style={[
          styles.generateButton,
          (!canGenerate || generating || alreadyGenerated) && styles.generateButtonDisabled,
        ]}
        onPress={handleGenerate}
        disabled={!canGenerate || generating || alreadyGenerated}
        activeOpacity={0.7}>
        {generating ? (
          <ActivityIndicator size="small" color="#FFF" />
        ) : (
          <Icon
            name="rocket"
            size={24}
            color="#FFF"
          />
        )}
        <Text style={styles.generateButtonText}>
          {generating
            ? 'Generating...'
            : 'Generate Bills'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
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
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
    padding: 40,
  },
  errorText: {
    fontSize: 18,
    color: '#999',
    marginTop: 20,
    textAlign: 'center',
  },
  errorButton: {
    marginTop: 20,
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
  },
  errorButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 30,
    alignItems: 'center',
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFF',
    marginTop: 15,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    marginTop: 5,
  },
  methodCard: {
    margin: 15,
    padding: 20,
    backgroundColor: '#FFF',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  methodLabel: {
    fontSize: 14,
    color: '#666',
  },
  methodValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
    marginTop: 4,
  },
  summarySection: {
    margin: 15,
    marginTop: 0,
    padding: 20,
    backgroundColor: '#FFF',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  summaryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  summaryLabel: {
    flex: 1,
    fontSize: 14,
    color: '#666',
    marginLeft: 10,
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  summaryValueError: {
    color: '#F44336',
  },
  warningBox: {
    flexDirection: 'row',
    margin: 15,
    padding: 16,
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  warningContent: {
    flex: 1,
    marginLeft: 10,
  },
  warningTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FF9800',
    marginBottom: 5,
  },
  warningText: {
    fontSize: 13,
    color: '#333',
  },
  infoBox: {
    flexDirection: 'row',
    margin: 15,
    padding: 16,
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  infoContent: {
    flex: 1,
    marginLeft: 10,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 5,
  },
  infoText: {
    fontSize: 13,
    color: '#333',
    marginBottom: 10,
  },
  viewBillsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    padding: 10,
    backgroundColor: '#FFF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#007AFF',
    gap: 8,
  },
  viewBillsButtonText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    margin: 15,
    padding: 16,
    borderRadius: 16,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  generateButtonDisabled: {
    backgroundColor: '#A0C4FF',
  },
  generateButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default GenerateBillsScreen;

import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {
  maintenanceService,
  ApartmentSettings,
} from '../../services/maintenanceService';

const ApartmentSettingsScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [settings, setSettings] = useState<ApartmentSettings | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [apartmentName, setApartmentName] = useState('');
  const [totalFlats, setTotalFlats] = useState('');
  const [calculationMethod, setCalculationMethod] = useState<'sqft_rate' | 'variable'>('variable');
  const [sqftRate, setSqftRate] = useState('');
  const [sinkingFundAmount, setSinkingFundAmount] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const settingsData = await maintenanceService.getSettings();
      if (settingsData) {
        setSettings(settingsData);
        setApartmentName(settingsData.apartment_name || '');
        setTotalFlats(String(settingsData.total_flats || ''));
        setCalculationMethod(settingsData.calculation_method || 'variable');
        setSqftRate(settingsData.sqft_rate ? String(settingsData.sqft_rate) : '');
        setSinkingFundAmount(
          settingsData.sinking_fund_total ? String(settingsData.sinking_fund_total) : '',
        );
      } else {
        // Settings don't exist yet - that's okay, user can create them
        // Don't set error, just show empty form
        setSettings(null);
        setApartmentName('');
        setTotalFlats('');
        setCalculationMethod('variable');
        setSqftRate('');
        setSinkingFundAmount('');
      }
    } catch (error: any) {
      console.error('Error loading settings:', error);
      // Only show error if it's not a 404 (settings not found is okay)
      if (error.response?.status !== 404) {
        const errorMessage = 
          error.response?.data?.detail || 
          error.message || 
          'Failed to load settings. Please check your connection and try again.';
        setError(errorMessage);
      } else {
        // 404 is handled by service returning null, so no error needed
        setSettings(null);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleSave = async () => {
    if (!apartmentName.trim()) {
      Alert.alert('Error', 'Please enter apartment name');
      return;
    }

    if (!totalFlats.trim()) {
      Alert.alert('Error', 'Please enter total number of flats');
      return;
    }

    const totalFlatsNum = parseInt(totalFlats);
    if (isNaN(totalFlatsNum) || totalFlatsNum <= 0) {
      Alert.alert('Error', 'Please enter a valid number of flats');
      return;
    }

    if (calculationMethod === 'sqft_rate' && !sqftRate.trim()) {
      Alert.alert('Error', 'Please enter square feet rate');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const settingsData: any = {
        apartment_name: apartmentName.trim(),
        total_flats: totalFlatsNum,
        calculation_method: calculationMethod,
      };

      if (calculationMethod === 'sqft_rate') {
        const sqftRateNum = parseFloat(sqftRate);
        if (isNaN(sqftRateNum) || sqftRateNum <= 0) {
          Alert.alert('Error', 'Please enter a valid square feet rate');
          setSaving(false);
          return;
        }
        settingsData.sqft_rate = sqftRateNum;
        settingsData.sinking_fund_total = null;
      } else {
        settingsData.sqft_rate = null;
        if (sinkingFundAmount.trim()) {
          const sinkingFundNum = parseFloat(sinkingFundAmount);
          if (!isNaN(sinkingFundNum) && sinkingFundNum >= 0) {
            settingsData.sinking_fund_total = sinkingFundNum;
          } else {
            settingsData.sinking_fund_total = 0;
          }
        } else {
          settingsData.sinking_fund_total = 0;
        }
      }

      console.log('Saving settings with data:', settingsData);
      const savedSettings = await maintenanceService.createOrUpdateSettings(settingsData);
      setSettings(savedSettings);
      Alert.alert('Success', 'Settings saved successfully!', [
        {text: 'OK', onPress: () => navigation.goBack()},
      ]);
    } catch (error: any) {
      console.error('Error saving settings:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      const errorMessage =
        error.response?.data?.detail || 
        error.response?.data?.error ||
        error.message ||
        'Failed to save settings. Please try again.';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // Show loading only on initial load (not when refreshing)
  if (loading && !settings && !error) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading settings...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={loadSettings} />
      }>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerIconContainer}>
          <Icon name="settings" size={48} color="#FFF" />
        </View>
        <Text style={styles.headerTitle}>Apartment Configuration</Text>
        <Text style={styles.headerSubtitle}>
          Configure maintenance billing settings
        </Text>
      </View>

      {/* Error Message */}
      {error && (
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={24} color="#FF3B30" />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={loadSettings}
            activeOpacity={0.7}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Info message when settings don't exist */}
      {!error && !settings && !loading && (
        <View style={styles.infoBox}>
          <Icon name="information-circle" size={24} color="#007AFF" />
          <View style={styles.infoContent}>
            <Text style={styles.infoTitle}>No Settings Found</Text>
            <Text style={styles.infoText}>
              Please configure your apartment settings below. This is required before you can generate maintenance bills.
            </Text>
          </View>
        </View>
      )}

      {/* Basic Information */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="information-circle" size={20} color="#007AFF" />
          <Text style={styles.sectionTitle}>Basic Information</Text>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Apartment Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter apartment name"
            placeholderTextColor="#999"
            value={apartmentName}
            onChangeText={setApartmentName}
            autoCapitalize="words"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Total Number of Flats *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter total flats"
            placeholderTextColor="#999"
            value={totalFlats}
            onChangeText={setTotalFlats}
            keyboardType="number-pad"
          />
        </View>
      </View>

      {/* Calculation Method */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="calculator" size={20} color="#007AFF" />
          <Text style={styles.sectionTitle}>Calculation Method</Text>
        </View>
        <Text style={styles.description}>
          Choose how maintenance bills should be calculated
        </Text>

        <TouchableOpacity
          style={[
            styles.methodCard,
            calculationMethod === 'sqft_rate' && styles.methodCardActive,
          ]}
          onPress={() => setCalculationMethod('sqft_rate')}
          activeOpacity={0.7}>
          <View style={styles.methodHeader}>
            <Icon
              name={
                calculationMethod === 'sqft_rate'
                  ? 'radio-button-on'
                  : 'radio-button-off'
              }
              size={24}
              color={calculationMethod === 'sqft_rate' ? '#007AFF' : '#C7C7CC'}
            />
            <Text style={styles.methodTitle}>Square Feet Rate</Text>
          </View>
          <Text style={styles.methodDescription}>
            Fixed rate per square feet. Simple calculation: Area × Rate
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.methodCard,
            calculationMethod === 'variable' && styles.methodCardActive,
          ]}
          onPress={() => setCalculationMethod('variable')}
          activeOpacity={0.7}>
          <View style={styles.methodHeader}>
            <Icon
              name={
                calculationMethod === 'variable'
                  ? 'radio-button-on'
                  : 'radio-button-off'
              }
              size={24}
              color={calculationMethod === 'variable' ? '#007AFF' : '#C7C7CC'}
            />
            <Text style={styles.methodTitle}>Variable (Water + Fixed)</Text>
          </View>
          <Text style={styles.methodDescription}>
            Variable water charges per person + fixed expenses per flat
          </Text>
        </TouchableOpacity>
      </View>

      {/* Square Feet Rate Configuration */}
      {calculationMethod === 'sqft_rate' && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Icon name="resize" size={20} color="#007AFF" />
            <Text style={styles.sectionTitle}>Square Feet Rate Configuration</Text>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Rate per Square Feet (₹) *</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g., 3.00"
              placeholderTextColor="#999"
              value={sqftRate}
              onChangeText={setSqftRate}
              keyboardType="decimal-pad"
            />
            {sqftRate && !isNaN(parseFloat(sqftRate)) && (
              <View style={styles.exampleBox}>
                <Text style={styles.exampleText}>
                  Example: 1000 sq ft × ₹{sqftRate} = ₹
                  {(1000 * parseFloat(sqftRate)).toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* Variable Method Configuration */}
      {calculationMethod === 'variable' && (
        <>
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Icon name="list" size={20} color="#007AFF" />
              <Text style={styles.sectionTitle}>Fixed Expenses Selection</Text>
            </View>
            <Text style={styles.description}>
              Select which expense account codes should be included in fixed expenses calculation.
              These expenses will be divided equally among all flats (including vacant flats).
            </Text>
            <TouchableOpacity
              style={styles.selectButton}
              onPress={() => navigation.navigate('SelectFixedExpenses')}
              activeOpacity={0.7}>
              <Icon name="settings-outline" size={20} color="#007AFF" />
              <Text style={styles.selectButtonText}>
                Select Fixed Expense Accounts
              </Text>
              <Icon name="chevron-forward" size={20} color="#007AFF" />
            </TouchableOpacity>
          </View>

          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Icon name="water" size={20} color="#007AFF" />
              <Text style={styles.sectionTitle}>Additional Configuration</Text>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Monthly Sinking Fund (₹)</Text>
              <TextInput
                style={styles.input}
                placeholder="Total monthly sinking fund amount"
                placeholderTextColor="#999"
                value={sinkingFundAmount}
                onChangeText={setSinkingFundAmount}
                keyboardType="decimal-pad"
              />
              <Text style={styles.hint}>
                This amount will be divided equally among all flats
              </Text>
            </View>
          </View>
        </>
      )}

      {/* Save Button */}
      <TouchableOpacity
        style={[styles.saveButton, saving && styles.saveButtonDisabled]}
        onPress={handleSave}
        disabled={saving}
        activeOpacity={0.7}>
        {saving ? (
          <ActivityIndicator size="small" color="#FFF" />
        ) : (
          <Icon name="checkmark-circle" size={24} color="#FFF" />
        )}
        <Text style={styles.saveButtonText}>
          {saving ? 'Saving...' : 'Save Settings'}
        </Text>
      </TouchableOpacity>

      {/* Info Box */}
      <View style={styles.infoBox}>
        <Icon name="information-circle" size={24} color="#007AFF" />
        <View style={styles.infoContent}>
          <Text style={styles.infoTitle}>Next Steps</Text>
          <Text style={styles.infoText}>
            After configuring settings:{'\n'}1. Add flat details (area, occupants)
            {'\n'}2. Set up fixed expenses (for variable method)
            {'\n'}3. Enter monthly water expenses (for variable method)
            {'\n'}4. Generate maintenance bills
          </Text>
        </View>
      </View>
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
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingTop: 50,
    paddingBottom: 30,
    alignItems: 'center',
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  headerIconContainer: {
    marginBottom: 12,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFF',
    marginBottom: 6,
  },
  headerSubtitle: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFE5E5',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#FF3B30',
    gap: 12,
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: '#D32F2F',
    fontWeight: '500',
  },
  retryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#FF3B30',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  section: {
    margin: 16,
    padding: 20,
    backgroundColor: '#FFF',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  description: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 16,
    lineHeight: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1.5,
    borderColor: '#E5E5EA',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    backgroundColor: '#FAFAFA',
    color: '#1D1D1F',
  },
  hint: {
    fontSize: 13,
    color: '#8E8E93',
    marginTop: 6,
    fontStyle: 'italic',
  },
  exampleBox: {
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  exampleText: {
    fontSize: 13,
    color: '#1976D2',
    fontWeight: '500',
  },
  methodCard: {
    borderWidth: 2,
    borderColor: '#E5E5EA',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    backgroundColor: '#FAFAFA',
  },
  methodCardActive: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD',
  },
  methodHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  methodTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1D1D1F',
    marginLeft: 10,
  },
  methodDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginLeft: 34,
    lineHeight: 20,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    margin: 16,
    padding: 16,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
    gap: 8,
  },
  saveButtonDisabled: {
    backgroundColor: '#A0C4FF',
  },
  saveButtonText: {
    color: '#FFF',
    fontSize: 17,
    fontWeight: '700',
  },
  infoBox: {
    flexDirection: 'row',
    margin: 16,
    marginBottom: 32,
    padding: 16,
    backgroundColor: '#E3F2FD',
    borderRadius: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
    gap: 12,
  },
  infoContent: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#007AFF',
    marginBottom: 6,
  },
  infoText: {
    fontSize: 13,
    color: '#1D1D1F',
    lineHeight: 20,
  },
  selectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#F0F8FF',
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#007AFF',
    marginTop: 12,
  },
  selectButtonText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
});

export default ApartmentSettingsScreen;

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
import {maintenanceService} from '../../services/maintenanceService';
import {flatsService} from '../../services/flatsService';
import {
  getCurrentMonth,
  formatMonthYear,
} from '../../utils/maintenanceCalculations';

const AddWaterExpenseScreen = ({navigation}: any) => {
  const [month, setMonth] = useState(getCurrentMonth());
  const [tankerCharges, setTankerCharges] = useState('');
  const [governmentCharges, setGovernmentCharges] = useState('');
  const [otherCharges, setOtherCharges] = useState('');
  const [totalOccupants, setTotalOccupants] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTotalOccupants();
    loadExistingExpense();
  }, [month]);

  const loadTotalOccupants = async () => {
    try {
      const flats = await flatsService.getFlats();
      const total = flats.reduce((sum, flat) => sum + flat.occupants, 0);
      setTotalOccupants(String(total));
    } catch (error) {
      console.error('Error loading occupants:', error);
    }
  };

  const loadExistingExpense = async () => {
    setLoading(true);
    try {
      const [year, monthNum] = month.split('-');
      const expenses = await maintenanceService.getWaterExpenses(
        parseInt(monthNum),
        parseInt(year),
      );

      if (expenses && expenses.length > 0) {
        const expense = expenses[0];
        setTankerCharges(String(expense.tanker_charges));
        setGovernmentCharges(String(expense.government_charges));
        setOtherCharges(String(expense.other_charges));
      } else {
        // Reset if no existing expense
        setTankerCharges('');
        setGovernmentCharges('');
        setOtherCharges('');
      }
    } catch (error: any) {
      // 404 is okay - means no expense exists yet
      if (error.response?.status !== 404) {
        console.error('Error loading water expense:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    const tanker = parseFloat(tankerCharges) || 0;
    const govt = parseFloat(governmentCharges) || 0;
    const other = parseFloat(otherCharges) || 0;
    const occupants = parseInt(totalOccupants);

    if (occupants <= 0) {
      Alert.alert('Error', 'Please enter valid number of occupants');
      return;
    }

    const totalAmount = tanker + govt + other;
    if (totalAmount <= 0) {
      Alert.alert('Error', 'Please enter at least one expense amount');
      return;
    }

    setSaving(true);
    try {
      const [year, monthNum] = month.split('-');

      const expenseData = {
        month: parseInt(monthNum),
        year: parseInt(year),
        tanker_charges: tanker,
        government_charges: govt,
        other_charges: other,
      };

      // Check if expense exists for this month
      const existing = await maintenanceService.getWaterExpenses(
        parseInt(monthNum),
        parseInt(year),
      );

      if (existing && existing.length > 0) {
        // Update existing - backend handles this automatically via POST
        await maintenanceService.createWaterExpense(expenseData);
        Alert.alert('Success', 'Water expense updated successfully', [
          {text: 'OK', onPress: () => navigation.goBack()},
        ]);
      } else {
        // Create new
        await maintenanceService.createWaterExpense(expenseData);
        Alert.alert('Success', 'Water expense saved successfully', [
          {text: 'OK', onPress: () => navigation.goBack()},
        ]);
      }
    } catch (error: any) {
      console.error('Error saving water expense:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to save water expense. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const totalAmount =
    (parseFloat(tankerCharges) || 0) +
    (parseFloat(governmentCharges) || 0) +
    (parseFloat(otherCharges) || 0);

  const perPersonCharge =
    totalAmount > 0 && parseInt(totalOccupants) > 0
      ? totalAmount / parseInt(totalOccupants)
      : 0;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Icon name="water" size={50} color="#007AFF" />
        <Text style={styles.headerTitle}>Water Expense</Text>
        <Text style={styles.headerSubtitle}>{formatMonthYear(month)}</Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.sectionTitle}>Water Charges</Text>

        <Text style={styles.label}>Tanker Charges (₹)</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter tanker water charges"
          value={tankerCharges}
          onChangeText={setTankerCharges}
          keyboardType="decimal-pad"
        />

        <Text style={styles.label}>Government Water Charges (₹)</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter government charges"
          value={governmentCharges}
          onChangeText={setGovernmentCharges}
          keyboardType="decimal-pad"
        />

        <Text style={styles.label}>Other Charges (₹)</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter other water-related charges"
          value={otherCharges}
          onChangeText={setOtherCharges}
          keyboardType="decimal-pad"
        />

        <View style={styles.totalCard}>
          <Text style={styles.totalLabel}>Total Water Expense</Text>
          <Text style={styles.totalAmount}>₹{totalAmount.toFixed(2)}</Text>
        </View>

        <Text style={styles.sectionTitle}>Occupancy</Text>

        <Text style={styles.label}>Total Occupants in Apartment</Text>
        <TextInput
          style={styles.input}
          placeholder="Total number of people"
          value={totalOccupants}
          onChangeText={setTotalOccupants}
          keyboardType="number-pad"
        />
        <Text style={styles.hint}>
          Auto-filled from flat data. Update if needed.
        </Text>

        <View style={styles.calculationCard}>
          <Text style={styles.calculationTitle}>Calculation</Text>
          <Text style={styles.calculationText}>
            Per Person Water Charge = ₹{totalAmount.toFixed(2)} ÷{' '}
            {totalOccupants || '0'} = ₹{perPersonCharge.toFixed(2)}
          </Text>
          <Text style={styles.calculationHint}>
            This rate will be multiplied by the number of occupants in each flat
          </Text>
        </View>

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
            {saving ? 'Saving...' : 'Save Water Expense'}
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
    backgroundColor: '#F5F5F5',
  },
  loadingText: {
    marginTop: 12,
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
  totalCard: {
    backgroundColor: '#E3F2FD',
    padding: 15,
    borderRadius: 12,
    marginTop: 15,
    alignItems: 'center',
  },
  totalLabel: {
    fontSize: 14,
    color: '#666',
  },
  totalAmount: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#007AFF',
    marginTop: 5,
  },
  calculationCard: {
    backgroundColor: '#FFF',
    padding: 15,
    borderRadius: 12,
    marginTop: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  calculationTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 8,
  },
  calculationText: {
    fontSize: 14,
    color: '#333',
    marginBottom: 8,
  },
  calculationHint: {
    fontSize: 12,
    color: '#666',
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

export default AddWaterExpenseScreen;

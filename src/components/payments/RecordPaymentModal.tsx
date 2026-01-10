import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {Picker} from '@react-native-picker/picker';
import {paymentService} from '../../services/paymentService';
import {spacing} from '../../constants/spacing';
import {formatCurrency} from '../../utils/formatters';

interface Bill {
  id: string;
  bill_number: string;
  total_amount: number;
  paid_amount?: number;
  flat_number: string;
  member_name: string;
}

interface RecordPaymentModalProps {
  visible: boolean;
  bill: Bill | null;
  onClose: () => void;
  onSuccess: () => void;
}

const RecordPaymentModal: React.FC<RecordPaymentModalProps> = ({
  visible,
  bill,
  onClose,
  onSuccess,
}) => {
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().split('T')[0],
  );
  const [paymentMode, setPaymentMode] = useState('cash');
  const [amount, setAmount] = useState('');
  const [transactionRef, setTransactionRef] = useState('');
  const [bankName, setBankName] = useState('');
  const [remarks, setRemarks] = useState('');
  const [lateFee, setLateFee] = useState('');
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
    setPaymentDate(new Date().toISOString().split('T')[0]);
    setPaymentMode('cash');
    setAmount('');
    setTransactionRef('');
    setBankName('');
    setRemarks('');
    setLateFee('');
  };

  const handleSubmit = async () => {
    if (!bill) return;

    // Validation
    if (!amount || parseFloat(amount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    const remainingAmount =
      bill.total_amount - (bill.paid_amount || 0);

    if (parseFloat(amount) > remainingAmount) {
      Alert.alert(
        'Error',
        `Payment amount cannot exceed remaining amount: ${formatCurrency(remainingAmount)}`,
      );
      return;
    }

    try {
      setLoading(true);

      await paymentService.recordPayment({
        bill_id: bill.id,
        payment_date: paymentDate,
        payment_mode: paymentMode,
        amount: parseFloat(amount),
        transaction_reference: transactionRef || undefined,
        bank_name: bankName || undefined,
        remarks: remarks || undefined,
        late_fee_charged: lateFee ? parseFloat(lateFee) : 0,
      });

      Alert.alert('Success', 'Payment recorded successfully!', [
        {
          text: 'OK',
          onPress: () => {
            resetForm();
            onSuccess();
            onClose();
          },
        },
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to record payment');
    } finally {
      setLoading(false);
    }
  };

  if (!bill) return null;

  const remainingAmount = bill.total_amount - (bill.paid_amount || 0);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Record Payment</Text>
            <TouchableOpacity onPress={onClose}>
              <Icon name="close" size={24} color="#1D1D1F" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Bill Info */}
            <View style={styles.billInfo}>
              <View style={styles.billInfoRow}>
                <Text style={styles.billInfoLabel}>Bill No:</Text>
                <Text style={styles.billInfoValue}>{bill.bill_number}</Text>
              </View>
              <View style={styles.billInfoRow}>
                <Text style={styles.billInfoLabel}>Flat:</Text>
                <Text style={styles.billInfoValue}>{bill.flat_number}</Text>
              </View>
              <View style={styles.billInfoRow}>
                <Text style={styles.billInfoLabel}>Member:</Text>
                <Text style={styles.billInfoValue}>{bill.member_name}</Text>
              </View>
              <View style={styles.billInfoRow}>
                <Text style={styles.billInfoLabel}>Bill Amount:</Text>
                <Text style={styles.billInfoValue}>
                  {formatCurrency(bill.total_amount)}
                </Text>
              </View>
              {bill.paid_amount && bill.paid_amount > 0 && (
                <View style={styles.billInfoRow}>
                  <Text style={styles.billInfoLabel}>Paid:</Text>
                  <Text style={[styles.billInfoValue, {color: '#34C759'}]}>
                    {formatCurrency(bill.paid_amount)}
                  </Text>
                </View>
              )}
              <View style={[styles.billInfoRow, styles.billInfoRowHighlight]}>
                <Text style={styles.billInfoLabelBold}>Remaining:</Text>
                <Text style={styles.billInfoValueBold}>
                  {formatCurrency(remainingAmount)}
                </Text>
              </View>
            </View>

            {/* Payment Date */}
            <View style={styles.field}>
              <Text style={styles.label}>Payment Date *</Text>
              <TextInput
                style={styles.input}
                value={paymentDate}
                onChangeText={setPaymentDate}
                placeholder="YYYY-MM-DD"
              />
            </View>

            {/* Payment Mode */}
            <View style={styles.field}>
              <Text style={styles.label}>Payment Mode *</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={paymentMode}
                  onValueChange={setPaymentMode}
                  style={styles.picker}>
                  <Picker.Item label="Cash" value="cash" />
                  <Picker.Item label="Cheque" value="cheque" />
                  <Picker.Item label="UPI" value="upi" />
                  <Picker.Item label="NEFT" value="neft" />
                  <Picker.Item label="RTGS" value="rtgs" />
                  <Picker.Item label="IMPS" value="imps" />
                  <Picker.Item label="Bank Transfer" value="bank_transfer" />
                  <Picker.Item label="Online" value="online" />
                  <Picker.Item label="Debit Card" value="debit_card" />
                  <Picker.Item label="Credit Card" value="credit_card" />
                  <Picker.Item label="Other" value="other" />
                </Picker>
              </View>
            </View>

            {/* Amount */}
            <View style={styles.field}>
              <Text style={styles.label}>Amount *</Text>
              <TextInput
                style={styles.input}
                value={amount}
                onChangeText={setAmount}
                placeholder="0.00"
                keyboardType="decimal-pad"
              />
              <TouchableOpacity
                style={styles.quickFillButton}
                onPress={() => setAmount(remainingAmount.toString())}>
                <Text style={styles.quickFillText}>
                  Full Amount: {formatCurrency(remainingAmount)}
                </Text>
              </TouchableOpacity>
            </View>

            {/* Transaction Reference */}
            {['cheque', 'upi', 'neft', 'rtgs', 'imps', 'online'].includes(
              paymentMode,
            ) && (
              <View style={styles.field}>
                <Text style={styles.label}>
                  {paymentMode === 'cheque'
                    ? 'Cheque Number'
                    : 'Transaction Reference'}
                </Text>
                <TextInput
                  style={styles.input}
                  value={transactionRef}
                  onChangeText={setTransactionRef}
                  placeholder={
                    paymentMode === 'cheque' ? 'Cheque no.' : 'UPI ref / Txn ID'
                  }
                />
              </View>
            )}

            {/* Bank Name */}
            {['cheque', 'neft', 'rtgs', 'bank_transfer'].includes(paymentMode) && (
              <View style={styles.field}>
                <Text style={styles.label}>Bank Name</Text>
                <TextInput
                  style={styles.input}
                  value={bankName}
                  onChangeText={setBankName}
                  placeholder="Bank name"
                />
              </View>
            )}

            {/* Late Fee */}
            <View style={styles.field}>
              <Text style={styles.label}>Late Fee (if any)</Text>
              <TextInput
                style={styles.input}
                value={lateFee}
                onChangeText={setLateFee}
                placeholder="0.00"
                keyboardType="decimal-pad"
              />
            </View>

            {/* Remarks */}
            <View style={styles.field}>
              <Text style={styles.label}>Remarks</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={remarks}
                onChangeText={setRemarks}
                placeholder="Optional remarks..."
                multiline
                numberOfLines={3}
              />
            </View>

            {/* Total Amount Summary */}
            {(amount || lateFee) && (
              <View style={styles.totalSummary}>
                <View style={styles.totalRow}>
                  <Text style={styles.totalLabel}>Payment Amount:</Text>
                  <Text style={styles.totalValue}>
                    {formatCurrency(parseFloat(amount || '0'))}
                  </Text>
                </View>
                {lateFee && parseFloat(lateFee) > 0 && (
                  <View style={styles.totalRow}>
                    <Text style={styles.totalLabel}>Late Fee:</Text>
                    <Text style={styles.totalValue}>
                      {formatCurrency(parseFloat(lateFee))}
                    </Text>
                  </View>
                )}
                <View style={[styles.totalRow, styles.totalRowFinal]}>
                  <Text style={styles.totalLabelBold}>Total Receiving:</Text>
                  <Text style={styles.totalValueBold}>
                    {formatCurrency(
                      parseFloat(amount || '0') + parseFloat(lateFee || '0'),
                    )}
                  </Text>
                </View>
              </View>
            )}
          </ScrollView>

          {/* Footer Buttons */}
          <View style={styles.footer}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={onClose}
              disabled={loading}>
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.submitButton]}
              onPress={handleSubmit}
              disabled={loading}>
              {loading ? (
                <ActivityIndicator color="#FFF" />
              ) : (
                <>
                  <Icon name="checkmark-circle-outline" size={20} color="#FFF" />
                  <Text style={styles.submitButtonText}>Record Payment</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  content: {
    padding: spacing.lg,
  },
  billInfo: {
    backgroundColor: '#F9F9F9',
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  billInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  billInfoRowHighlight: {
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  billInfoLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  billInfoValue: {
    fontSize: 14,
    color: '#1D1D1F',
    fontWeight: '500',
  },
  billInfoLabelBold: {
    fontSize: 15,
    color: '#1D1D1F',
    fontWeight: '600',
  },
  billInfoValueBold: {
    fontSize: 15,
    color: '#FF3B30',
    fontWeight: '700',
  },
  field: {
    marginBottom: spacing.md,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1D1D1F',
    marginBottom: spacing.xs,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    padding: spacing.sm,
    fontSize: 15,
    color: '#1D1D1F',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  quickFillButton: {
    marginTop: spacing.xs,
    padding: spacing.xs,
    alignItems: 'center',
  },
  quickFillText: {
    fontSize: 13,
    color: '#007AFF',
    fontWeight: '600',
  },
  totalSummary: {
    backgroundColor: '#E8F5E9',
    borderRadius: 12,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  totalRowFinal: {
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#34C759',
  },
  totalLabel: {
    fontSize: 14,
    color: '#2E7D32',
  },
  totalValue: {
    fontSize: 14,
    color: '#2E7D32',
    fontWeight: '500',
  },
  totalLabelBold: {
    fontSize: 16,
    color: '#1D1D1F',
    fontWeight: '700',
  },
  totalValueBold: {
    fontSize: 16,
    color: '#2E7D32',
    fontWeight: '700',
  },
  footer: {
    flexDirection: 'row',
    padding: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    gap: spacing.sm,
  },
  button: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
    borderRadius: 12,
    gap: spacing.xs,
  },
  cancelButton: {
    backgroundColor: '#F9F9F9',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  submitButton: {
    backgroundColor: '#34C759',
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});

export default RecordPaymentModal;



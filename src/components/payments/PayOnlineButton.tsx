import React, {useState} from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  Alert,
  ActivityIndicator,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {paymentGatewayService} from '../../services/paymentGatewayService';
import {spacing} from '../../constants/spacing';
import {formatCurrency} from '../../utils/formatters';

interface PayOnlineButtonProps {
  billId: string;
  billNumber: string;
  amount: number;
  onSuccess: () => void;
  onCancel?: () => void;
  style?: any;
  showAmount?: boolean;
}

const PayOnlineButton: React.FC<PayOnlineButtonProps> = ({
  billId,
  billNumber,
  amount,
  onSuccess,
  onCancel,
  style,
  showAmount = false,
}) => {
  const [loading, setLoading] = useState(false);

  const handlePayOnline = async () => {
    try {
      setLoading(true);

      // Initiate payment
      const result = await paymentGatewayService.payOnline(billId);

      // Payment successful
      Alert.alert(
        '✅ Payment Successful!',
        `Payment of ${formatCurrency(result.total_paid)} received successfully.\n\nReceipt No: ${result.receipt_number}\n\nPayment Method: ${paymentGatewayService.formatPaymentMethod(result.payment_method)}`,
        [
          {
            text: 'OK',
            onPress: () => {
              onSuccess();
            },
          },
        ],
      );
    } catch (error: any) {
      if (error.message === 'Payment cancelled by user' || error.message === 'Payment cancelled') {
        // User cancelled - don't show error
        if (onCancel) {
          onCancel();
        }
      } else {
        // Payment failed
        Alert.alert('Payment Failed', error.message || 'Unable to process payment. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <TouchableOpacity
      style={[styles.button, style]}
      onPress={handlePayOnline}
      disabled={loading}
      activeOpacity={0.7}>
      {loading ? (
        <ActivityIndicator color="#FFF" size="small" />
      ) : (
        <>
          <Icon name="card-outline" size={20} color="#FFF" />
          <View style={styles.textContainer}>
            <Text style={styles.buttonText}>Pay Online</Text>
            {showAmount && (
              <Text style={styles.amountText}>{formatCurrency(amount)}</Text>
            )}
          </View>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    gap: 10,
    shadowColor: '#007AFF',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  textContainer: {
    alignItems: 'center',
  },
  buttonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '700',
  },
  amountText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '500',
    marginTop: 2,
    opacity: 0.9,
  },
});

export default PayOnlineButton;



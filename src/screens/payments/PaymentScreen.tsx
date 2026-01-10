import React from 'react';
import {View, StyleSheet} from 'react-native';
import UnderDevelopment from '../../components/UnderDevelopment';

const PaymentScreen = () => {
  return (
    <View style={styles.container}>
      <UnderDevelopment
        featureName="Payment Gateway"
        estimatedTime="Phase 5 (3-4 weeks)"
        message="Payment integration with UPI, Razorpay, and PayU is currently under development. You can still record offline payments manually."
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
});

export default PaymentScreen;









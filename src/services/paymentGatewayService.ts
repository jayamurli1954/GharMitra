/**
 * Payment Gateway Service
 * Handles Razorpay integration for online payments
 */
import RazorpayCheckout from 'react-native-razorpay';
import api from './api';

export interface PaymentOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  bill_id: string;
  bill_number: string;
  bill_amount: number;
  convenience_fee: number;
  total_amount: number;
  member_name: string;
  member_email: string;
  member_phone: string;
  society_name: string;
  key_id: string;
}

export interface PaymentVerificationRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface PaymentVerificationResponse {
  success: boolean;
  message: string;
  payment_id: string;
  receipt_number: string;
  amount: number;
  convenience_fee: number;
  total_paid: number;
  payment_method: string;
  razorpay_payment_id: string;
}

export interface OnlinePaymentStatus {
  id: string;
  status: string;
  amount: number;
  payment_method?: string;
  created_at: string;
  completed_at?: string;
  razorpay_payment_id?: string;
  receipt_number?: string;
}

class PaymentGatewayService {
  /**
   * Create payment order and initiate Razorpay checkout
   */
  async payOnline(billId: string): Promise<PaymentVerificationResponse> {
    try {
      // Step 1: Create order on backend
      const orderResponse = await api.post<PaymentOrderResponse>(
        '/payment-gateway/create-order',
        null,
        {
          params: {bill_id: billId},
        },
      );

      const orderData = orderResponse.data;

      // Step 2: Open Razorpay checkout
      const options = {
        description: `Bill #${orderData.bill_number}`,
        image: 'https://your-logo-url.com/logo.png', // TODO: Replace with actual logo
        currency: orderData.currency,
        key: orderData.key_id,
        amount: Math.round(orderData.total_amount * 100), // Convert to paise
        order_id: orderData.order_id,
        name: orderData.society_name,
        prefill: {
          email: orderData.member_email,
          contact: orderData.member_phone,
          name: orderData.member_name,
        },
        theme: {color: '#007AFF'},
        notes: {
          bill_id: orderData.bill_id,
          bill_number: orderData.bill_number,
        },
      };

      // Step 3: Open Razorpay (returns promise)
      const paymentResult: any = await RazorpayCheckout.open(options);

      // Step 4: Verify payment on backend
      const verificationResponse = await api.post<PaymentVerificationResponse>(
        '/payment-gateway/verify-payment',
        null,
        {
          params: {
            razorpay_order_id: orderData.order_id,
            razorpay_payment_id: paymentResult.razorpay_payment_id,
            razorpay_signature: paymentResult.razorpay_signature,
          },
        },
      );

      return verificationResponse.data;
    } catch (error: any) {
      // Handle Razorpay specific errors
      if (error.code) {
        switch (error.code) {
          case 0:
            throw new Error('Payment cancelled by user');
          case 1:
            throw new Error('Payment failed. Please try again.');
          case 2:
            throw new Error('Payment cancelled');
          default:
            throw new Error(error.description || 'Payment failed');
        }
      }
      
      throw error;
    }
  }

  /**
   * Get payment status
   */
  async getPaymentStatus(
    onlinePaymentId: string,
  ): Promise<OnlinePaymentStatus> {
    const response = await api.get<OnlinePaymentStatus>(
      `/payment-gateway/payment-status/${onlinePaymentId}`,
    );
    return response.data;
  }

  /**
   * Format payment method for display
   */
  formatPaymentMethod(method: string): string {
    const methodMap: Record<string, string> = {
      upi: 'UPI',
      card: 'Card',
      netbanking: 'Net Banking',
      wallet: 'Wallet',
      emi: 'EMI',
      paylater: 'Pay Later',
    };
    return methodMap[method.toLowerCase()] || method;
  }

  /**
   * Get payment method icon
   */
  getPaymentMethodIcon(method: string): string {
    const iconMap: Record<string, string> = {
      upi: 'phone-portrait-outline',
      card: 'card-outline',
      netbanking: 'business-outline',
      wallet: 'wallet-outline',
      emi: 'cash-outline',
      paylater: 'time-outline',
    };
    return iconMap[method.toLowerCase()] || 'card-outline';
  }
}

export const paymentGatewayService = new PaymentGatewayService();



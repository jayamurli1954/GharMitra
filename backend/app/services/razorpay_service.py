"""
Razorpay Payment Gateway Service
Handles all interactions with Razorpay API
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hmac
import hashlib
from decimal import Decimal

from ..config import settings

# Optional import - only needed if Razorpay is enabled
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    razorpay = None


class RazorpayService:
    """
    Razorpay Payment Gateway Integration
    
    Provides methods for:
    - Creating orders
    - Verifying payments
    - Processing refunds
    - Creating payment links
    - Handling webhooks
    """
    
    def __init__(self):
        """Initialize Razorpay client"""
        if not RAZORPAY_AVAILABLE:
            raise ImportError("razorpay package is not installed. Install it with: pip install razorpay")
        
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    
    def create_order(
        self,
        amount: float,
        receipt: str,
        notes: Optional[Dict[str, str]] = None,
        currency: str = 'INR'
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            receipt: Receipt identifier (e.g., bill_uuid)
            notes: Additional metadata
            currency: Currency code (default: INR)
            
        Returns:
            Order details from Razorpay
        """
        try:
            # Convert amount to paise (Razorpay uses smallest currency unit)
            amount_paise = int(Decimal(str(amount)) * 100)
            
            # Create order
            order = self.client.order.create({
                'amount': amount_paise,
                'currency': currency,
                'receipt': receipt,
                'notes': notes or {},
                'payment_capture': 1  # Auto capture payment
            })
            
            return order
        except Exception as e:
            raise Exception(f"Failed to create Razorpay order: {str(e)}")
    
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature
        
        This is CRITICAL for security - ensures payment is genuine
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Signature from Razorpay
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Create signature string
            message = f"{order_id}|{payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.key_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            print(f"Signature verification error: {str(e)}")
            return False
    
    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetch payment details from Razorpay
        
        Args:
            payment_id: Razorpay payment ID
            
        Returns:
            Payment details
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            raise Exception(f"Failed to fetch payment: {str(e)}")
    
    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """
        Fetch order details from Razorpay
        
        Args:
            order_id: Razorpay order ID
            
        Returns:
            Order details
        """
        try:
            order = self.client.order.fetch(order_id)
            return order
        except Exception as e:
            raise Exception(f"Failed to fetch order: {str(e)}")
    
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        notes: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund (None = full refund)
            notes: Refund notes
            
        Returns:
            Refund details
        """
        try:
            refund_data = {}
            
            if amount:
                refund_data['amount'] = int(Decimal(str(amount)) * 100)
            
            if notes:
                refund_data['notes'] = notes
            
            refund = self.client.payment.refund(payment_id, refund_data)
            return refund
        except Exception as e:
            raise Exception(f"Failed to refund payment: {str(e)}")
    
    def create_payment_link(
        self,
        amount: float,
        description: str,
        customer: Dict[str, str],
        reference_id: str,
        callback_url: Optional[str] = None,
        expire_by: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a payment link
        
        Args:
            amount: Amount in rupees
            description: Payment description
            customer: Customer details (name, email, contact)
            reference_id: Your reference ID
            callback_url: Redirect URL after payment
            expire_by: Link expiry timestamp
            
        Returns:
            Payment link details
        """
        try:
            amount_paise = int(Decimal(str(amount)) * 100)
            
            link_data = {
                'amount': amount_paise,
                'currency': 'INR',
                'description': description,
                'customer': customer,
                'reference_id': reference_id,
                'notify': {
                    'sms': True,
                    'email': True
                }
            }
            
            if callback_url:
                link_data['callback_url'] = callback_url
                link_data['callback_method'] = 'get'
            
            if expire_by:
                link_data['expire_by'] = int(expire_by.timestamp())
            
            payment_link = self.client.payment_link.create(link_data)
            return payment_link
        except Exception as e:
            raise Exception(f"Failed to create payment link: {str(e)}")
    
    def fetch_payment_link(self, link_id: str) -> Dict[str, Any]:
        """
        Fetch payment link details
        
        Args:
            link_id: Payment link ID
            
        Returns:
            Payment link details
        """
        try:
            link = self.client.payment_link.fetch(link_id)
            return link
        except Exception as e:
            raise Exception(f"Failed to fetch payment link: {str(e)}")
    
    def verify_webhook_signature(
        self,
        webhook_body: str,
        webhook_signature: str
    ) -> bool:
        """
        Verify webhook signature
        
        CRITICAL for webhook security - ensures webhook is from Razorpay
        
        Args:
            webhook_body: Raw webhook body (as string)
            webhook_signature: X-Razorpay-Signature header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                webhook_body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, webhook_signature)
        except Exception as e:
            print(f"Webhook signature verification error: {str(e)}")
            return False
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """
        Get available payment methods
        
        Returns:
            Available payment methods
        """
        try:
            methods = self.client.payment.methods()
            return methods
        except Exception as e:
            raise Exception(f"Failed to fetch payment methods: {str(e)}")
    
    def calculate_convenience_fee(
        self,
        amount: float,
        fee_percentage: float = 2.0
    ) -> float:
        """
        Calculate convenience fee
        
        Args:
            amount: Bill amount
            fee_percentage: Fee percentage (default 2%)
            
        Returns:
            Convenience fee amount
        """
        return round(amount * (fee_percentage / 100), 2)
    
    def get_checkout_options(
        self,
        order_id: str,
        amount: float,
        currency: str,
        name: str,
        description: str,
        prefill: Dict[str, str],
        theme_color: str = '#007AFF'
    ) -> Dict[str, Any]:
        """
        Get Razorpay checkout options for frontend
        
        Args:
            order_id: Razorpay order ID
            amount: Amount in paise
            currency: Currency code
            name: Company/Society name
            description: Payment description
            prefill: Prefill data (name, email, contact)
            theme_color: Theme color for checkout
            
        Returns:
            Checkout options dictionary
        """
        return {
            'key': self.key_id,
            'order_id': order_id,
            'amount': int(Decimal(str(amount)) * 100),
            'currency': currency,
            'name': name,
            'description': description,
            'image': settings.RAZORPAY_LOGO_URL if hasattr(settings, 'RAZORPAY_LOGO_URL') else '',
            'prefill': prefill,
            'theme': {
                'color': theme_color
            },
            'modal': {
                'ondismiss': 'handle_payment_cancel'
            }
        }


# Singleton instance (only if Razorpay is available)
if RAZORPAY_AVAILABLE:
    try:
        razorpay_service = RazorpayService()
    except Exception as e:
        # If initialization fails, create a dummy service
        razorpay_service = None
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Razorpay service not available: {e}")
else:
    razorpay_service = None



/**
 * Network Utilities
 * Auto-detect and handle network changes
 */
import { Alert, Platform } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_IP_KEY = '@api_ip_address';
const METRO_IP_KEY = '@metro_ip_address';

/**
 * Get stored IP addresses
 */
export const getStoredIPs = async () => {
  try {
    const [apiIP, metroIP] = await Promise.all([
      AsyncStorage.getItem(API_IP_KEY),
      AsyncStorage.getItem(METRO_IP_KEY),
    ]);
    return {
      apiIP: apiIP || null,
      metroIP: metroIP || null,
    };
  } catch (error) {
    console.error('Error getting stored IPs:', error);
    return { apiIP: null, metroIP: null };
  }
};

/**
 * Store IP addresses
 */
export const storeIPs = async (apiIP: string, metroIP: string) => {
  try {
    await Promise.all([
      AsyncStorage.setItem(API_IP_KEY, apiIP),
      AsyncStorage.setItem(METRO_IP_KEY, metroIP),
    ]);
  } catch (error) {
    console.error('Error storing IPs:', error);
  }
};

/**
 * Detect network changes and notify user
 */
export const setupNetworkListener = (onNetworkChange?: (isConnected: boolean) => void) => {
  return NetInfo.addEventListener(state => {
    const isConnected = state.isConnected && state.isInternetReachable;
    
    if (onNetworkChange) {
      onNetworkChange(isConnected);
    }
    
    if (!isConnected) {
      console.warn('Network disconnected');
    } else {
      console.log('Network connected:', state.type);
      
      // If IP changed, show notification
      if (state.type === 'wifi' || state.type === 'cellular') {
        console.log('Network type:', state.type);
        // Note: We can't detect IP change from mobile app directly
        // User should run AUTO_DETECT_IP.bat on computer
      }
    }
  });
};

/**
 * Test API connection
 */
export const testAPIConnection = async (apiURL: string): Promise<boolean> => {
  try {
    const response = await fetch(`${apiURL}/health`, {
      method: 'GET',
      timeout: 5000,
    } as any);
    return response.ok;
  } catch (error) {
    console.error('API connection test failed:', error);
    return false;
  }
};

/**
 * Show network troubleshooting guide
 */
export const showNetworkHelp = () => {
  Alert.alert(
    'Network Connection Help',
    'If you cannot connect:\n\n' +
    '1. Make sure backend is running\n' +
    '2. Phone and computer on same WiFi\n' +
    '3. Run AUTO_DETECT_IP.bat on computer\n' +
    '4. Restart Metro: START_METRO_AUTO.bat\n' +
    '5. Reload app on phone\n\n' +
    'IP address updates automatically!',
    [{ text: 'OK' }]
  );
};


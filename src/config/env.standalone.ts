/**
 * Standalone Environment Configuration
 * Use this for standalone/demo deployments
 * 
 * To use: Copy this file to env.ts or update env.ts with these values
 */

let Config: any = null;

try {
  Config = require('react-native-config').default;
} catch (e) {
  console.warn('react-native-config not available, using defaults');
}

// Standalone configuration - Update API_URL with your server IP
export const ENV = {
  // IMPORTANT: Replace with your computer's IP address
  // Find it by running: python backend/get_local_ip.py
  // Or check when backend server starts
  API_URL: Config?.API_URL || 'http://192.168.29.141:8000',

  APP_NAME: Config?.APP_NAME || 'GharMitra',
  APP_VERSION: Config?.APP_VERSION || '1.0.0',
  NODE_ENV: Config?.NODE_ENV || 'development',

  // Standalone mode flag
  STANDALONE_MODE: true,
};

export default ENV;



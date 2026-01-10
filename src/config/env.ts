/**
 * Environment Configuration
 * Safe wrapper around react-native-config
 */

let Config: any = null;

try {
  Config = require('react-native-config').default;
} catch (e) {
  console.warn('react-native-config not available, using defaults');
}

export const ENV = {
  // For Physical Device (OnePlus) - use your laptop's IP
  // Changed to port 8001 to avoid conflict with other projects
  API_URL: Config?.API_URL || 'http://192.168.29.141:8001',

  // For Android Emulator - use 10.0.2.2
  // API_URL: Config?.API_URL || 'http://10.0.2.2:8001',

  // For iOS Simulator (Mac) - use localhost
  // API_URL: Config?.API_URL || 'http://localhost:8001',

  APP_NAME: Config?.APP_NAME || 'GharMitra',
  APP_VERSION: Config?.APP_VERSION || '1.0.0',
  NODE_ENV: Config?.NODE_ENV || 'development',
};

export default ENV;
